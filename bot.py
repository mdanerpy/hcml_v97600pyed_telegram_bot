#!/usr/bin/env python3
# Telegram Bot for Hanzi Cipher Markup Language (HCML)
# @HCML_Bot

import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import tempfile
from datetime import datetime
import json

from hcml_core import load_chinese_chars, build_cipher_map, encrypt_text, decrypt_text
from hcml_processor import HCMLProcessor

# ========== تنظیمات ==========
TOKEN = "8324641811:AAF-PhEKNavtFlN8_trkmzOPHmLbf8COkE0"

# مسیر فایل‌ها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHINESE_CHARS_FILE = os.path.join(BASE_DIR, "Characters_Chinese_97600.txt")
CLASSES_FILE = os.path.join(BASE_DIR, "HCML_Classes.json")

# لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# بارگذاری کاراکترهای چینی
try:
    with open(CHINESE_CHARS_FILE, "r", encoding="utf-8") as f:
        chinese_chars = list(f.read())
    chinese_chars = [c for c in chinese_chars if c.strip()]
    logger.info(f"✅ {len(chinese_chars)} کاراکتر چینی بارگذاری شد")
except Exception as e:
    logger.error(f"❌ خطا در بارگذاری کاراکترها: {e}")
    chinese_chars = []

# ========== توابع کمکی ==========
def get_processor():
    return HCMLProcessor(chinese_chars) if chinese_chars else None

def format_result(text: str, is_encrypted: bool) -> str:
    """格式化 نتیجه برای نمایش زیبا"""
    border = "🔷" * 20
    title = "🔐 متن رمزنگاری شده" if is_encrypted else "🔓 متن رمزگشایی شده"
    return f"""
{border}
{title}
{border}

`{text[:4000]}`

{border}
📊 آمار: {len(text)} کاراکتر
🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

# ========== هندلرهای فرمان ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فرمان /start - خوش‌آمدگویی"""
    user = update.effective_user
    welcome_text = f"""
✨ **به ربات HCML خوش آمدید** ✨

سلام {user.first_name}! 👋

این ربات، **Hanzi Cipher Markup Language** را پیاده‌سازی کرده است - یک روش خلاقانه برای رمزنگاری متن با استفاده از کاراکترهای چینی!

🎯 **قابلیت‌ها:**
• رمزنگاری متن به کاراکترهای چینی
• رمزگشایی متن‌های رمز شده
• پشتیبانی از کلاس‌های سفارشی
• تنظیمات پیشرفته (key, count, way)

📝 **نحوه استفاده:**

1️⃣ **رمزنگاری ساده:**
`<E>متن شما</E>`

2️⃣ **رمزگشایی:**
`<D>کاراکترهای چینی</D>`

3️⃣ **با تنظیمات پیشرفته:**
`<E key=42 way="-" count=5000>متن محرمانه</E>`

4️⃣ **تعریف کلاس:**
`<E class="secret" key=123>متن</E>`

5️⃣ **حالت زیبا (mode="#"):**
`<E mode="#">متن</E>` (فقط خروجی رمز)

🎮 **دکمه‌های زیر را امتحان کنید!**

📚 راهنما: /help
💡 مثال: /example
📊 وضعیت: /status
"""

    keyboard = [
        [InlineKeyboardButton("🔐 رمزنگاری سریع", callback_data="quick_encrypt")],
        [InlineKeyboardButton("🔓 رمزگشایی سریع", callback_data="quick_decrypt")],
        [InlineKeyboardButton("📚 مثال‌ها", callback_data="examples")],
        [InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="settings")],
        [InlineKeyboardButton("ℹ️ درباره", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فرمان /help - راهنمای کامل"""
    help_text = """
📖 **راهنمای کامل HCML**

**تگ‌ها:**
• `<E>` - رمزنگاری (Encrypt)
• `<D>` - رمزگشایی (Decrypt)

**ویژگی‌ها:**
• `class` - نام کلاس برای ذخیره تنظیمات
• `count` - تعداد کاراکترهای چینی (پیش‌فرض: 3000)
• `key` - کلید رمز (پیش‌فرض: 0)
• `way` - روش چیدمان (+, -, %n, *n)
• `mode` - حالت ویژه (# فقط خروجی، ! کلید تصادفی)
• `tokens` - جداکننده‌ها (پیش‌فرض: { و })

**مثال‌های پیشرفته:**

1. استفاده از کلید سفارشی:
`<E key=12345>Hello World!</E>`

2. با کلاس و ذخیره‌سازی:
`<E class="mysecret" key=999 way="-">پیام مخفی</E>`

3. رمزگشایی با همان کلاس:
`<D class="mysecret">...کاراکترهای چینی...</D>`

4. حالت زیبا (فقط خروجی):
`<E mode="#">سلام دنیا</E>`

5. کلید تصادفی:
`<E mode="!">متن تصادفی</E>`

💡 **نکته:** می‌توانید چندین تگ را در یک پیام ترکیب کنید!
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def example_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فرمان /example - نمایش مثال‌ها"""
    examples = [
        ("🔐 مثال ساده", "<E>سلام دنیا!</E>"),
        ("🔓 رمزگشایی", "<D>䷀䷁䷂䷃䷄䷅䷆䷇䷈䷉</D>"),
        ("⚙️ با کلید سفارشی", "<E key=42 way=\"-\">متن مخفی</E>"),
        ("📁 با کلاس", "<E class=\"topsecret\" key=777>اطلاعات محرمانه</E>"),
        ("🎲 کلید تصادفی", "<E mode=\"!\">هر بار متفاوت</E>")
    ]

    for title, example in examples:
        keyboard = [[InlineKeyboardButton("🔄 امتحان کن", callback_data=f"try_{example[:30]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"*{title}*\n\n`{example}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        await asyncio.sleep(0.5)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فرمان /status - وضعیت سیستم"""
    status_text = f"""
📊 **وضعیت سیستم HCML**

✅ **وضعیت:** فعال
📚 **کاراکترهای چینی:** {len(chinese_chars):,}
🗂 **فایل کلاس‌ها:** {"✅" if os.path.exists(CLASSES_FILE) else "❌"}

🔧 **تنظیمات پیش‌فرض:**
• count: 3000
• key: 0
• way: "+"
• mode: ""

💡 **نکات:**
• حداکثر طول متن: 4096 کاراکتر
• پشتیبانی از یونیکد کامل
• ذخیره خودکار کلاس‌ها
"""
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

# ========== هندلر پیام‌ها ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های دریافتی"""
    text = update.message.text
    if not text:
        return

    processor = get_processor()
    if not processor:
        await update.message.reply_text("❌ خطا: سیستم آماده نیست!")
        return

    # ارسال پیام در حال پردازش
    processing_msg = await update.message.reply_text("⏳ در حال پردازش...")

    try:
        # پردازش متن
        result = processor.process(text)

        # اگر نتیجه با ورودی متفاوت است (پردازش شده)
        if result != text:
            # تشخیص نوع پردازش (رمزنگاری یا رمزگشایی)
            is_encrypted = "<E" in text and result.count("䷀") > 0
            
            # نمایش نتیجه
            formatted = format_result(result[:3000], is_encrypted)
            
            # اضافه کردن دکمه‌های عملیاتی
            keyboard = [
                [InlineKeyboardButton("📋 کپی متن", callback_data=f"copy_{result[:50]}")],
                [InlineKeyboardButton("🔄 رمزگشایی معکوس", callback_data="reverse")],
                [InlineKeyboardButton("💾 ذخیره در کلاس", callback_data="save_class")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(
                formatted,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            # اگر تگی وجود نداشت، راهنمایی نشان بده
            await processing_msg.edit_text(
                "❓ **هیچ تگ معتبری یافت نشد!**\n\n"
                "برای رمزنگاری از `<E>متن شما</E>` استفاده کنید.\n"
                "برای رمزگشایی از `<D>...کاراکترهای چینی...</D>` استفاده کنید.\n\n"
                "راهنمای کامل: /help",
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text(f"❌ خطا: {str(e)[:200]}\n\nلطفاً متن خود را بررسی کنید.")

# ========== هندلر دکمه‌ها ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش کلیک روی دکمه‌ها"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "quick_encrypt":
        await query.edit_message_text(
            "🔐 **رمزنگاری سریع**\n\n"
            "لطفاً متنی که می‌خواهید رمزنگاری شود را ارسال کنید.\n\n"
            "مثال: `سلام دنیا!`",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['mode'] = 'encrypt'

    elif data == "quick_decrypt":
        await query.edit_message_text(
            "🔓 **رمزگشایی سریع**\n\n"
            "لطفاً متن رمزنگاری شده (کاراکترهای چینی) را ارسال کنید.\n\n"
            "مثال: `䷀䷁䷂䷃`",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['mode'] = 'decrypt'

    elif data == "examples":
        examples_text = """
📚 **مثال‌های کاربردی:**

1️⃣ **پیام ساده:**
`<E>Hello World!</E>`

2️⃣ **متن فارسی:**
`<E key=123>سلام ایران</E>`

3️⃣ **رمزگشایی:**
`<D>䷀䷁䷂䷃䷄䷅䷆䷇䷈䷉</D>`

4️⃣ **استفاده از کلاس:**
`<E class="personal" key=456>پیام شخصی</E>`

✅ **کافی است یکی از این مثال‌ها را کپی کرده و ارسال کنید!**
"""
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")]]
        await query.edit_message_text(
            examples_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "settings":
        settings_text = """
⚙️ **تنظیمات پیشرفته:**

می‌توانید از این پارامترها استفاده کنید:

• `key` - کلید عددی (مثلاً key=42)
• `way` - روش چیدمان (+, -, %2, *3)
• `count` - تعداد کاراکترها (1000 تا 97600)
• `mode` - حالت ویژه (# یا !)

**مثال ترکیبی:**
`<E key=999 way="%3" count=5000 mode="#">متن پیشرفته</E>`
"""
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")]]
        await query.edit_message_text(
            settings_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "about":
        about_text = """
ℹ️ **درباره HCML Bot**

**نسخه:** 1.0.0
**HCML نسخه:** 97600

این ربات، پیاده‌سازی **Hanzi Cipher Markup Language** است - یک زبان نشانه‌گذاری برای رمزنگاری متن با استفاده از کاراکترهای چینی.

🎯 **ویژگی‌ها:**
• رمزنگاری یکطرفه و برگشت‌پذیر
• پشتیبانی از 97,600 کاراکتر چینی
• کلاس‌های قابل ذخیره‌سازی
• تنظیمات پیشرفته رمزنگاری

👨‍💻 **منبع:** گیت هاب
📝 **ساخته شده با:** Python + python-telegram-bot

✨ **از استفاده شما سپاسگزاریم!**
"""
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")]]
        await query.edit_message_text(
            about_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "back_to_start":
        keyboard = [
            [InlineKeyboardButton("🔐 رمزنگاری سریع", callback_data="quick_encrypt")],
            [InlineKeyboardButton("🔓 رمزگشایی سریع", callback_data="quick_decrypt")],
            [InlineKeyboardButton("📚 مثال‌ها", callback_data="examples")],
            [InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="settings")],
            [InlineKeyboardButton("ℹ️ درباره", callback_data="about")]
        ]
        await query.edit_message_text(
            "✨ **منوی اصلی HCML Bot** ✨\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("try_"):
        example_text = data[4:]
        await query.message.reply_text(
            f"✅ مثال ارسال شد:\n\n`{example_text}`\n\nدر حال پردازش...",
            parse_mode=ParseMode.MARKDOWN
        )
        # ایجاد پیام جدید با همان مثال
        await handle_message(update, context)

# ========== تابع اصلی ==========
def main():
    """راه‌اندازی ربات"""
    if not chinese_chars:
        print("❌ خطا: فایل کاراکترهای چینی یافت نشد!")
        print(f"مسیر مورد نظر: {CHINESE_CHARS_FILE}")
        return

    print("🚀 راه‌اندازی ربات HCML...")
    print(f"📚 تعداد کاراکترها: {len(chinese_chars):,}")
    print(f"🤖 توکن: {TOKEN[:10]}...")

    # ایجاد برنامه
    application = Application.builder().token(TOKEN).build()

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("example", example_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    # راه‌اندازی
    print("✅ ربات آماده است! در حال اجرا...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()