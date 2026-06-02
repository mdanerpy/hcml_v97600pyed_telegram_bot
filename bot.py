#!/usr/bin/env python3
# HCML Telegram Bot - پستچی ساده و وظیفه‌شناس

import os
import sys
import tempfile
from datetime import datetime

# مسیرها - مثل قبل، پیش‌نیازها رو می‌خونه
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from hcml_core import load_chinese_chars
from hcml_processor import HCMLProcessor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

# توکن فقط و فقط از متغیر محیطی خوندشه میشه. امنیت رو جدی بگیریم دیگه.
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("❌ خطا: BOT_TOKEN رو توی environment variable تنظیم نکردی!")
    sys.exit(1)

# بارگذاری کتابخونه و کاراکترهای چینی
try:
    with open(os.path.join(BASE_DIR, "Characters_Chinese_97600.txt"), "r", encoding="utf-8") as f:
        chinese_chars = [c for c in f.read() if c.strip()]
    processor = HCMLProcessor(chinese_chars)
except Exception as e:
    print(f"❌ خطا توی لود کردن فایل‌های کتابخونه: {e}")
    sys.exit(1)

# پسوندهای مجاز برای فایل (طبق دستور تو)
TEXT_EXTENSIONS = {'.txt', '.json', '.xml', '.html', '.htm', '.js', '.ts', '.css', '.scss', '.py', '.csv', '.yaml', '.yml', '.ini', '.cfg', '.md', '.log', '.sql', '.hcml'}

def save_output(content: str) -> str:
    """خروجی رو توی یه فایل موقت .hcml ذخیره می‌کنه"""
    fd, path = tempfile.mkstemp(suffix=".hcml", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

# --- دستورات اصلی ربات ---

async def start(update: Update, context):
    """خوش‌آمدگویی و توضیح خیلی ساده"""
    await update.message.reply_text(
        "✨ به ربات HCML خوش اومدی! ✨\n\n"
        "من یه پستچی ساده‌ام. متن یا فایلت رو می‌گیرم، می‌دم به ماشین رمزنگار و نتیجه رو برات می‌آرم.\n\n"
        "📝 **روش استفاده خیلی آسونه:**\n"
        "• متن داخل تگ `<E>` رو رمزنگاری می‌کنم.\n"
        "• متن داخل تگ `<D>` رو رمزگشایی می‌کنم.\n"
        "• می‌تونی فایل متنی هم برام بفرستی.\n\n"
        "👇 راهنما و مثال‌ها رو ببین:\n"
        "/help - راهنمای سریع\n"
        "/example - چند تا مثال آماده",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context):
    """راهنمای خیلی سریع"""
    await update.message.reply_text(
        "📖 **راهنما**\n\n"
        "`<E>متن برای رمزنگاری</E>`\n"
        "`<D>کاراکترهای چینی برای رمزگشایی</D>`\n\n"
        "می‌تونی از پارامترهای اختیاری هم استفاده کنی:\n"
        "`<E key=123 way=\"-\" mode=\"#\">متن</E>`",
        parse_mode=ParseMode.MARKDOWN
    )

async def example_command(update: Update, context):
    """چند مثال دستی"""
    await update.message.reply_text(
        "💡 **چند مثال:**\n\n"
        "`<E>سلام دنیا</E>`\n"
        "`<E key=123>متن مخفی من</E>`\n"
        "`<E mode=\"#\">فقط خروجی رو بده</E>`",
        parse_mode=ParseMode.MARKDOWN
    )

async def status_command(update: Update, context):
    """وضعیت کتابخونه"""
    await update.message.reply_text(f"📊 **وضعیت سیستم**\n\n✅ ربات فعال\n📚 تعداد کاراکترهای چینی: {len(chinese_chars):,}")

# --- مدیریت پیام‌ها (قلب واسطه‌گری) ---

async def handle_text(update: Update, context):
    """متن کاربر رو می‌گیره و مستقیم می‌ده به ماشین"""
    user_text = update.message.text
    if not user_text:
        return

    # اینجا مهمه: ما هیچ چک نمی‌کنیم تگ داره یا نه. ماشین خودش تصمیم می‌گیره.
    result = processor.process(user_text)

    # ماشین اگر نتونه پردازش کنه، خود متن رو برمی‌گردونه. ما هم چیزی نمی‌گیم.
    # ولی خب، برای اینکه کاربر بدونه یه کاری شده، همون نتیجه رو نشون می‌دیم.
    # اگه متن خروجی عوض نشده بود، یعنی احتمالا تگی وجود نداشته. ما بازم ایراد نمی‌گیریم،
    # چون شاید کاربر می‌خواسته همون متن رو ببینه.
    # به خاطر "اسکل بازی درنیاری" گفتی، دیگه اون پیام "تگ پیدا نشد" رو هم حذف کردم.
    # مستقیم نتیجه رو نشون می‌دیم.
    
    await send_final_result(update, result)

async def handle_file(update: Update, context):
    """فایل کاربر رو می‌گیره و مستقیم می‌ده به ماشین"""
    doc = update.message.document
    if not doc:
        return

    # چک پسوند فایل
    ext = os.path.splitext(doc.file_name)[1].lower()
    if ext not in TEXT_EXTENSIONS:
        # فقط اگه پسوند نامعتبر باشه یه پیام ساده می‌دیم
        await update.message.reply_text(f"❌ پسوند فایل `{ext}` پشتیبانی نمی‌شه.", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        file = await doc.get_file()
        file_content = await file.download_as_bytearray()
        text = file_content.decode('utf-8')
        
        result = processor.process(text)
        # باز هم هیچ چک اضافه‌ای. مستقیم خروجی رو نشون می‌دیم.
        await send_final_result(update, result)

    except Exception as e:
        await update.message.reply_text(f"❌ یه مشکلی موقع خوندن فایل پیش اومد: {e}")

async def send_final_result(update: Update, result: str):
    """خروجی نهایی رو با اون فرمت و دکمه‌هایی که خواستی می‌سازه و می‌فرسته"""
    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    weekday = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"][now.weekday()]
    time_str = now.strftime("%H:%M")

    # سرهم کردن متن نهایی خروجی: نتیجه + تاریخ و روز و ساعت
    output_text = f"{result}\n\n📅 {date_str} | {weekday} | 🕐 {time_str}"

    # دکمه‌های زیر خروجی
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 کپی متن خروجی", callback_data="copy"),
            InlineKeyboardButton("🗑 پاک کردن خروجی", callback_data="clear"),
        ],
        [InlineKeyboardButton("📁 ارسال فایل HCML", callback_data="send_file")]
    ])

    # ذخیره‌سازی خروجی برای ارسال فایل بعداً
    context.user_data['last_output_raw'] = result
    context.user_data['last_output_path'] = save_output(result)
    
    # ارسال نتیجه به کاربر
    await update.message.reply_text(output_text, reply_markup=keyboard)

# --- دکمه‌های زیر پیام ---

async def button_callback(update: Update, context):
    """مدیریت کلیک روی دکمه‌ها"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "clear":
        await query.message.delete()
    
    elif query.data == "send_file":
        path = context.user_data.get('last_output_path')
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.hcml"
                )
        else:
            await query.answer("فایلی برای ارسال پیدا نشد!", show_alert=True)
    
    elif query.data == "copy":
        # متن خروجی رو توی یه پیام هشدار نشون می‌ده تا کاربر راحت کپی کنه
        raw_output = context.user_data.get('last_output_raw', '')
        await query.answer(f"✅ متن آماده کپی:\n\n{raw_output[:200]}...", show_alert=True)

# --- اجرای ربات ---

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("example", example_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ ربات پستچی HCML روشن شد و آماده خدمت‌رسانیه!")
    app.run_polling()

if __name__ == "__main__":
    main()
