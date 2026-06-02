#!/usr/bin/env python3
# HCML Telegram Bot - پستچی ساده با ریپلای و کد بلاک

import os
import sys
import tempfile
import traceback
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
INTRO_IMAGE = os.path.join(BASE_DIR, "HCML_Page.png")

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("❌ BOT_TOKEN تنظیم نشده")
    sys.exit(1)

# ایمپورت کتابخونه‌ها
try:
    from hcml_core import load_chinese_chars
    from hcml_processor import HCMLProcessor
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    from telegram.constants import ParseMode
    print("✅ ایمپورت‌ها موفق")
except Exception as e:
    print(f"❌ خطای ایمپورت: {e}")
    traceback.print_exc()
    sys.exit(1)

# لود کاراکترها
try:
    char_path = os.path.join(BASE_DIR, "Characters_Chinese_97600.txt")
    print(f"📂 لود کاراکترها از: {char_path}")
    with open(char_path, "r", encoding="utf-8") as f:
        chinese_chars = [c for c in f.read() if c.strip()]
    print(f"✅ {len(chinese_chars)} کاراکتر لود شد")
except Exception as e:
    print(f"❌ خطای لود کاراکترها: {e}")
    traceback.print_exc()
    sys.exit(1)

# ساخت پردازشگر
try:
    processor = HCMLProcessor(chinese_chars)
    print("✅ پردازشگر HCML آماده شد")
except Exception as e:
    print(f"❌ خطای ساخت پردازشگر: {e}")
    traceback.print_exc()
    sys.exit(1)

# پسوندهای مجاز فایل
TEXT_EXTENSIONS = {
    '.txt', '.json', '.xml', '.html', '.htm', '.js', '.ts',
    '.css', '.scss', '.py', '.csv', '.yaml', '.yml', '.ini',
    '.cfg', '.md', '.log', '.sql', '.hcml'
}

def save_output(content: str) -> str:
    """ذخیره خروجی در فایل موقت .hcml"""
    fd, path = tempfile.mkstemp(suffix=".hcml", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

# ─── دستورات ربات ────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اول عکس رو بفرست
    if os.path.exists(INTRO_IMAGE):
        with open(INTRO_IMAGE, 'rb') as img:
            await update.message.reply_photo(
                photo=img,
                caption=(
                    f"✨ **به HCML Bot خوش اومدی!** ✨\n\n"
                    f"🔐 **HCML (Hanzi Cipher Markup Language)** یک زبان رمزنگاری متنی مبتنی بر کاراکترهای چینی است.\n\n"
                    f"🤖 این ربات رابط کاربری موتور HCML است.\n"
                    f"پیام یا فایل را دریافت می‌کند و نتیجه را برمی‌گرداند.\n\n"
                    f"📝 **شروع سریع:**\n"
                    f"• `<E>متن شما</E>` → رمزنگاری\n"
                    f"• `<D>متن رمز</D>` → رمزگشایی\n"
                    f"• ارسال فایل‌های متنی برای پردازش مستقیم\n\n"
                    f"⚡ **ویژگی‌ها:**\n"
                    f"• کلیدهای سفارشی\n"
                    f"• پشتیبانی از فایل‌های متنی\n"
                    f"• خروجی قابل کپی\n"
                    f"• تولید فایل HCML\n"
                    f"• استفاده از 97,600 کاراکتر چینی\n\n"
                    f"📚 /help | 💡 /example | 📊 /status"
                )
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        # اگه عکس نبود، فقط متن رو بفرست (مثل قبل)
        await update.message.reply_text(
            f"✨ **به ربات HCML خوش اومدی!** ✨\n\n"
            f"من یه پستچی ساده‌ام. متن یا فایل رو می‌گیرم، می‌دم به ماشین رمزنگار و نتیجه رو برمی‌گردونم.\n\n"
            f"📝 **روش استفاده:**\n"
            f"• `<E>متن</E>` ← رمزنگاری\n"
            f"• `<D>متن</D>` ← رمزگشایی\n"
            f"• فایل متنی هم می‌تونی بفرستی\n\n"
            f"📚 /help | 💡 /example | 📊 /status",
            parse_mode=ParseMode.MARKDOWN
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📖 **راهنمای HCML**\n\n"
        f"🔐 **تگ‌های اصلی:**\n"
        f"`<E>متن</E>` → رمزنگاری\n"
        f"`<D>متن</D>` → رمزگشایی\n\n"
        f"⚙️ **پارامترهای پرکاربرد:**\n"
        f"`key=123` → کلید رمز\n"
        f"`count=5000` → تعداد کاراکترهای مورد استفاده\n"
        f"`way=\"+\"` → ترتیب چیدمان کاراکترها\n"
        f"`mode=\"#\"` → فقط خروجی رمز\n"
        f"`mode=\"!\"` → کلید تصادفی\n"
        f"`class=\"name\"` → استفاده از کلاس ذخیره‌شده\n\n"
        f"📝 **نمونه:**\n"
        f"`<E key=123 mode=\"#\">سلام دنیا</E>`\n\n"
        f"📂 فایل‌های متنی نیز قابل پردازش هستند.\n\n"
        f"💡 برای مشاهده مثال‌های بیشتر از دستور /example استفاده کنید.",
        parse_mode=ParseMode.MARKDOWN
    )


async def example_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💡 **نمونه‌های HCML**\n\n"
        f"🔐 رمزنگاری ساده:\n"
        f"`<E>سلام دنیا</E>`\n\n"
        f"🔑 رمزنگاری با کلید:\n"
        f"`<E key=42>متن مخفی</E>`\n\n"
        f"📤 فقط خروجی رمز:\n"
        f"`<E mode=\"#\">متن من</E>`\n\n"
        f"🎲 کلید تصادفی:\n"
        f"`<E mode=\"!\">پیام محرمانه</E>`\n\n"
        f"📚 استفاده از کلاس:\n"
        f"`<E class=\"mycipher\">متن</E>`\n\n"
        f"⚙️ تنظیم تعداد کاراکترها:\n"
        f"`<E key=123 count=5000>متن</E>`\n\n"
        f"🔓 رمزگشایی:\n"
        f"`<D>متن رمز شده</D>`\n\n"
        f"📂 همچنین می‌توانید فایل‌های متنی را مستقیماً ارسال کنید.",
        parse_mode=ParseMode.MARKDOWN
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 **HCML Engine Status**\n\n"
        "🟢 وضعیت ربات: آنلاین\n"
        "🔐 موتور رمزنگاری: فعال\n"
        f"📚 کاراکترهای چینی: {len(chinese_chars):,}\n"
        "🏷️ نسخه: HCML v97600\n"
        "🐍 Runtime: Python\n"
        "⚡ آماده پردازش متن و فایل\n\n"
        "🚀 All Systems Operational"
    )


# ─── مدیریت پیام و فایل (پستچی ساده) ─────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text
        if not user_text:
            return

        print(f"📩 متن دریافت شد: {user_text[:80]}...")

        # ارسال مستقیم به پردازشگر
        result = processor.process(user_text)

        print(f"📤 نتیجه: {result[:80]}...")

        await send_result(update, context, result)

    except Exception as e:
        print(f"❌ خطا در handle_text: {e}")
        traceback.print_exc()
        await update.message.reply_text("❌ یه مشکلی پیش اومد. لطفاً دوباره تلاش کن.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        doc = update.message.document
        if not doc:
            return

        ext = os.path.splitext(doc.file_name)[1].lower()
        if ext not in TEXT_EXTENSIONS:
            await update.message.reply_text(f"❌ پسوند `{ext}` پشتیبانی نمی‌شه.")
            return

        print(f"📂 فایل دریافت شد: {doc.file_name}")

        file = await doc.get_file()
        file_content = await file.download_as_bytearray()
        text = file_content.decode('utf-8')

        result = processor.process(text)

        await send_result(update, context, result)

    except Exception as e:
        print(f"❌ خطا در handle_file: {e}")
        traceback.print_exc()
        await update.message.reply_text("❌ یه مشکلی در خوندن فایل پیش اومد.")

# ─── فرمت‌بندی و ارسال نتیجه ─────────────────────────────

async def send_result(update: Update, context: ContextTypes.DEFAULT_TYPE, result: str):
    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    weekday_list = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"]
    weekday = weekday_list[now.weekday()]
    time_str = now.strftime("%H:%M")

    # ─── تشخیص نوع خروجی ───
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in result)

    if has_chinese:
        # خروجی رمزنگاری شده → بین `` ` `` قرار می‌گیره
        output_message = (
            "<hcml>\n"
            f"`{result}`\n"
            "</hcml>\n\n"
            "||@hcml_v97600py_tel_bot||\n"
            f"{date_str} | {weekday} | {time_str}"
        )
    else:
        # خروجی رمزگشایی شده یا عادی
        output_message = f"<hcml>\n`{result}`\n</hcml>\n\n||@hcml_v97600py_tel_bot||\n{date_str} | {weekday} | {time_str}"

    # دکمه‌ها (فقط پاک کردن و ارسال فایل - بدون کپی)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗑 پاک کردن", callback_data="clear"),
            InlineKeyboardButton("📁 ارسال فایل HCML", callback_data="send_file")
        ]
    ])

    # ذخیره برای ارسال فایل
    context.user_data['last_output_raw'] = result
    context.user_data['last_output_path'] = save_output(result)

    # ─── ریپلای به پیام کاربر (مهم!) ───
    await update.message.reply_text(
        output_message,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=update.message.message_id  # ← این خط ریپلای می‌کنه
    )

# ─── دکمه‌ها ──────────────────────────────────────────────

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await query.answer("❌ فایلی برای ارسال پیدا نشد!", show_alert=True)

# ─── اجرا ─────────────────────────────────────────────────

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
        print(f"❌ خطای کلی: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
