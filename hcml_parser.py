#!/usr/bin/env python3
# HCML Telegram Bot - با گزارش خطای کامل برای پیدا کردن مشکل

import os
import sys
import tempfile
import traceback
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("❌ خطا: BOT_TOKEN تنظیم نشده.")
    sys.exit(1)

# ایمپورت با گزارش خطای واضح
try:
    from hcml_core import load_chinese_chars
    from hcml_processor import HCMLProcessor
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    from telegram.constants import ParseMode
    print("✅ همه کتابخونه‌ها با موفقیت ایمپورت شدن.")
except Exception as e:
    print(f"❌ خطای ایمپورت: {e}")
    traceback.print_exc()
    sys.exit(1)

# بارگذاری کاراکترها
try:
    char_path = os.path.join(BASE_DIR, "Characters_Chinese_97600.txt")
    print(f"📂 درحال لود کردن فایل کاراکترها از: {char_path}")
    with open(char_path, "r", encoding="utf-8") as f:
        chinese_chars = [c for c in f.read() if c.strip()]
    print(f"✅ {len(chinese_chars)} کاراکتر با موفقیت لود شد.")
except Exception as e:
    print(f"❌ خطا توی لود فایل کاراکترها: {e}")
    traceback.print_exc()
    sys.exit(1)

# ایجاد پردازشگر
try:
    processor = HCMLProcessor(chinese_chars)
    print("✅ پردازشگر HCML آماده شد.")
except Exception as e:
    print(f"❌ خطا توی ساختن پردازشگر: {e}")
    traceback.print_exc()
    sys.exit(1)

TEXT_EXTENSIONS = {'.txt', '.json', '.xml', '.html', '.htm', '.js', '.ts', '.css', '.scss', '.py', '.csv', '.yaml', '.yml', '.ini', '.cfg', '.md', '.log', '.sql', '.hcml'}

def save_output(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".hcml", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

# --- هندلرهای ربات ---

async def start(update: Update, context):
    await update.message.reply_text(
        "✨ به ربات HCML خوش اومدی! ✨\n\n"
        "من یه پستچی ساده‌ام. متن یا فایلت رو می‌گیرم، می‌دم به ماشین رمزنگار و نتیجه رو برات می‌آرم.\n\n"
        "📝 **روش استفاده:**\n"
        "• `<E>متن</E>` برای رمزنگاری\n"
        "• `<D>متن</D>` برای رمزگشایی\n"
        "• فایل متنی هم می‌تونی بفرستی.\n\n"
        "/help - راهنمای سریع\n"
        "/example - چند مثال\n"
        "/status - وضعیت سیستم"
    )

async def help_command(update: Update, context):
    await update.message.reply_text(
        "📖 `<E>متن</E>` = رمزنگاری\n"
        "`<D>متن</D>` = رمزگشایی\n"
        "با پارامتر: `<E key=123 mode=\"#\">متن</E>`"
    )

async def example_command(update: Update, context):
    await update.message.reply_text(
        "💡 مثال:\n`<E>سلام دنیا</E>`\n`<E key=42>متن مخفی</E>`"
    )

async def status_command(update: Update, context):
    await update.message.reply_text(f"📊 فعال | {len(chinese_chars):,} کاراکتر")

async def handle_text(update: Update, context):
    try:
        user_text = update.message.text
        print(f"📩 پیام دریافت شد: {user_text[:50]}...") # لاگ توی Action
        
        # پردازش مستقیم
        result = processor.process(user_text)
        print(f"📤 نتیجه پردازش: {result[:50]}...") # لاگ توی Action
        
        await send_result(update, result)
    except Exception as e:
        print(f"❌ خطا توی handle_text: {e}")
        traceback.print_exc()
        # به کاربر هم بگو خطا رخ داد
        await update.message.reply_text("❌ یه مشکلی پیش اومد. ادمین داره بررسی می‌کنه.")

async def handle_file(update: Update, context):
    try:
        doc = update.message.document
        if not doc: return

        ext = os.path.splitext(doc.file_name)[1].lower()
        if ext not in TEXT_EXTENSIONS:
            await update.message.reply_text(f"❌ پسوند {ext} پشتیبانی نمی‌شه.")
            return

        file = await doc.get_file()
        file_content = await file.download_as_bytearray()
        text = file_content.decode('utf-8')
        
        result = processor.process(text)
        await send_result(update, result)
    except Exception as e:
        print(f"❌ خطا توی handle_file: {e}")
        traceback.print_exc()
        await update.message.reply_text("❌ یه مشکلی موقع خوندن فایل پیش اومد.")

async def send_result(update: Update, result: str):
    """فرمت‌بندی و ارسال نتیجه نهایی"""
    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    weekday = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"][now.weekday()]
    time_str = now.strftime("%H:%M")

    output_text = f"{result}\n\n📅 {date_str} | {weekday} | 🕐 {time_str}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 کپی متن", callback_data="copy"),
         InlineKeyboardButton("🗑 پاک کردن", callback_data="clear")],
        [InlineKeyboardButton("📁 ارسال فایل HCML", callback_data="send_file")]
    ])

    context.user_data['last_output_raw'] = result
    context.user_data['last_output_path'] = save_output(result)
    
    await update.message.reply_text(output_text, reply_markup=keyboard)

async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "clear":
        await query.message.delete()
    elif query.data == "send_file":
        path = context.user_data.get('last_output_path')
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                await query.message.reply_document(document=f, filename=f"output.hcml")
    elif query.data == "copy":
        text = context.user_data.get('last_output_raw', '')
        await query.answer(f"✅ متن:\n{text[:100]}...", show_alert=True)

# --- اجرا ---
def main():
    try:
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("example", example_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
        app.add_handler(CallbackQueryHandler(button_callback))
        
        print("🚀 ربات داره شروع به کار می‌کنه...")
        app.run_polling()
    except Exception as e:
        print(f"❌ خطای کلی توی اجرای ربات: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
