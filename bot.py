#!/usr/bin/env python3
# HCML Telegram Bot - فقط واسطه

import os
import sys
import tempfile
from datetime import datetime

# مسیرها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ایمپورت HCML
from hcml_core import load_chinese_chars
from hcml_processor import HCMLProcessor

# تلگرام - خط درست شده
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8324641811:AAF-PhEKNavtFlN8_trkmzOPHmLbf8COkE0"

# بارگذاری کاراکترها
with open(os.path.join(BASE_DIR, "Characters_Chinese_97600.txt"), "r", encoding="utf-8") as f:
    chinese_chars = [c for c in f.read() if c.strip()]

processor = HCMLProcessor(chinese_chars)

# پسوندهای مجاز
TEXT_EXTENSIONS = {'.txt', '.json', '.xml', '.html', '.htm', '.js', '.ts', '.css', '.scss', '.py', '.csv', '.yaml', '.yml', '.ini', '.cfg', '.md', '.log', '.sql', '.hcml'}

def save_output(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".hcml", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

async def start(update: Update, context):
    await update.message.reply_text(
        "سلام! من ربات HCML هستم.\n\n"
        "می‌توانید:\n"
        "• متن حاوی `<E>` یا `<D>` بفرستید\n"
        "• فایل متنی بفرستید\n\n"
        "/help - راهنما\n"
        "/example - مثال\n"
        "/status - وضعیت",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context):
    await update.message.reply_text(
        "📖 **راهنما**\n\n"
        "`<E>متن</E>` - رمزنگاری\n"
        "`<D>متن</D>` - رمزگشایی\n"
        "`<E key=123>متن</E>` - با کلید",
        parse_mode=ParseMode.MARKDOWN
    )

async def example_command(update: Update, context):
    await update.message.reply_text(
        "💡 **مثال:**\n\n"
        "`<E>سلام دنیا</E>`\n\n"
        "`<E key=123>متن مخفی</E>`",
        parse_mode=ParseMode.MARKDOWN
    )

async def status_command(update: Update, context):
    await update.message.reply_text(
        f"📊 **وضعیت**\n\n"
        f"کاراکترها: {len(chinese_chars):,}\n"
        f"وضعیت: فعال",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_text(update: Update, context):
    text = update.message.text
    if not text:
        return
    
    result = processor.process(text)
    
    if result == text:
        await update.message.reply_text("❌ تگ `<E>` یا `<D>` پیدا نشد.")
        return
    
    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    weekday = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"][now.weekday()]
    
    output_text = f"{result}\n\n📅 {date_str} | {weekday}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 کپی متن", callback_data="copy")],
        [InlineKeyboardButton("📁 ارسال فایل", callback_data="send_file")]
    ])
    
    context.user_data['last_output_path'] = save_output(result)
    
    await update.message.reply_text(output_text, reply_markup=keyboard)

async def handle_file(update: Update, context):
    doc = update.message.document
    if not doc:
        return
    
    ext = os.path.splitext(doc.file_name)[1].lower()
    if ext not in TEXT_EXTENSIONS:
        await update.message.reply_text(f"❌ پسوند {ext} پشتیبانی نمی‌شود.")
        return
    
    file = await doc.get_file()
    file_content = await file.download_as_bytearray()
    text = file_content.decode('utf-8')
    result = processor.process(text)
    
    if result == text:
        await update.message.reply_text("❌ تگ پیدا نشد.")
        return
    
    context.user_data['last_output_path'] = save_output(result)
    
    await update.message.reply_text(result)

async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "copy":
        await query.answer("✅ متن آماده کپی است!", show_alert=True)
    elif query.data == "send_file":
        path = context.user_data.get('last_output_path')
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                await query.message.reply_document(document=f, filename="output.hcml")

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
