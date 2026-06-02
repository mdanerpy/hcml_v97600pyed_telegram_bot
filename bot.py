#!/usr/bin/env python3
# HCML Telegram Bot - فقط واسطه

import os
import sys
import tempfile
from datetime import datetime
import re

# مسیرها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ایمپورت HCML
from hcml_core import load_chinese_chars
from hcml_processor import HCMLProcessor

# تلگرام
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8324641811:AAF-PhEKNavtFlN8_trkmzOPHmLbf8COkE0"

# بارگذاری کاراکترها
with open(os.path.join(BASE_DIR, "Characters_Chinese_97600.txt"), "r", encoding="utf-8") as f:
    chinese_chars = [c for c in f.read() if c.strip()]

processor = HCMLProcessor(chinese_chars)

# پسوندهای مجاز برای فایل
TEXT_EXTENSIONS = {'.txt', '.json', '.xml', '.html', '.htm', '.js', '.ts', '.css', '.scss', '.py', '.csv', '.yaml', '.yml', '.ini', '.cfg', '.md', '.log', '.sql', '.hcml'}

def save_output(content: str) -> str:
    """ذخیره خروجی در فایل موقت"""
    fd, path = tempfile.mkstemp(suffix=".hcml", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔐 راهنما", callback_data="help")],
    ]
    await update.message.reply_text(
        "سلام! من ربات HCML هستم.\n\n"
        "می‌توانید:\n"
        "• متن حاوی `<E>` یا `<D>` بفرستید\n"
        "• فایل متنی بفرستید\n\n"
        "📚 راهنما: /help\n"
        "💡 مثال: /example\n"
        "📊 وضعیت: /status",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context):
    help_text = """📖 **راهنمای HCML**

**رمزنگاری:**
`<E>متن شما</E>`

**رمزگشایی:**
`<D>کاراکترهای چینی</D>`

**پارامترها:**
• `key=123` - کلید رمز
• `way="-"` - روش چیدمان
• `count=5000` - تعداد کاراکترها
• `class="name"` - کلاس ذخیره شده
• `mode="#"` - فقط خروجی

**مثال:**
`<E key=42 way="-" mode="#">متن مخفی</E>`

می‌توانید فایل‌های `.txt`، `.json`، `.py` و... را هم ارسال کنید."""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def example_command(update: Update, context):
    examples = """💡 **مثال‌ها:**

1. رمزنگاری ساده:
`<E>سلام دنیا</E>`

2. رمزنگاری با کلید:
`<E key=123>متن مخفی</E>`

3. رمزگشایی:
`<D>䷀䷁䷂䷃䷄䷅䷆䷇䷈䷉</D>`

4. با کلاس:
`<E class="secret" key=42>پیام محرمانه</E>`

5. حالت فقط خروجی:
`<E mode="#">بدون تگ خروجی</E>`

کافیست یکی از مثال‌ها را کپی کرده و ارسال کنید."""
    await update.message.reply_text(examples, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context):
    status_text = f"""📊 **وضعیت سیستم**

✅ وضعیت: فعال
📚 کاراکترهای چینی: {len(chinese_chars):,}
🗂 فایل کلاس‌ها: موجود

📝 راهنمای استفاده: /help
💡 مثال: /example"""
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def handle_text(update: Update, context):
    text = update.message.text
    if not text:
        return
    
    # پردازش با HCML
    result = processor.process(text)
    
    if result == text:
        await update.message.reply_text("❌ تگ `<E>` یا `<D>` پیدا نشد.\nبرای راهنما /help")
        return
    
    # نمایش نتیجه ساده
    await send_result(update, result)

async def handle_file(update: Update, context):
    """پردازش فایل دریافتی"""
    doc = update.message.document
    if not doc:
        return
    
    # بررسی پسوند
    ext = os.path.splitext(doc.file_name)[1].lower()
    if ext not in TEXT_EXTENSIONS:
        await update.message.reply_text(f"❌ پسوند {ext} پشتیبانی نمی‌شود.\nپسوندهای مجاز: {', '.join(TEXT_EXTENSIONS)}")
        return
    
    # دانلود فایل
    file = await doc.get_file()
    file_content = await file.download_as_bytearray()
    text = file_content.decode('utf-8')
    
    # پردازش
    result = processor.process(text)
    
    if result == text:
        await update.message.reply_text("❌ تگ `<E>` یا `<D>` در فایل پیدا نشد.")
        return
    
    # ذخیره خروجی برای ارسال فایل
    context.user_data['last_output'] = result
    
    await send_result(update, result, filename=doc.file_name)

async def send_result(update: Update, result: str, filename: str = None):
    """ارسال نتیجه به کاربر"""
    now = datetime.now()
    
    # تاریخ و زمان
    date_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")
    weekday = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"][now.weekday()]
    
    footer = f"\n\n📅 {date_str} | {weekday} | 🕐 {time_str}"
    
    # ساخت متن خروجی
    output_text = f"{result}{footer}"
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 کپی متن", callback_data=f"copy_{result[:100]}"),
            InlineKeyboardButton("🗑 پاک کردن", callback_data="clear"),
        ],
        [InlineKeyboardButton("📁 ارسال فایل HCML", callback_data="send_file")]
    ])
    
    # ذخیره برای ارسال فایل
    context.user_data['last_output_raw'] = result
    context.user_data['last_output_path'] = save_output(result)
    
    await update.message.reply_text(
        output_text,
        reply_markup=keyboard
    )

async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "clear":
        await query.message.delete()
    
    elif data == "send_file":
        path = context.user_data.get('last_output_path')
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.hcml"
                )
    
    elif data.startswith("copy_"):
        await query.answer("✅ متن آماده کپی است!", show_alert=True)
    
    elif data == "help":
        help_text = """📖 **راهنمای سریع**

**رمزنگاری:**
`<E>متن شما</E>`

**رمزگشایی:**
`<D>کاراکترهای چینی</D>`

**پارامترها:**
• `key=123` - کلید رمز
• `way="-"` - روش چیدمان
• `count=5000` - تعداد کاراکترها

**مثال:**
`<E key=42 way="-">متن مخفی</E>`"""
        await query.edit_message_text(help_text, parse_mode=ParseMode.MARKDOWN)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("example", example_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ ربات روشن شد")
    app.run_polling()

if __name__ == "__main__":
    main()
