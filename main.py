import logging
import requests
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


TELEGRAM_BOT_TOKEN = "7270764307:AAHgjM0dfBpCUnGILOasK5WOI3o3YmCZb9k"
SPOILER_PHOTO_URL = "https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DHrz_vZZWmcw"
BOT_USERNAME = "Xer_oxbot"
AI_API_URL = "https://dev-pycodz-blackbox.pantheonsite.io/DEvZ44d/Hacker.php"
user_languages = {}
group_user_activation = {}

conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_chats (
        user_id INTEGER,
        message TEXT,
        timestamp TEXT
    )
""")
conn.commit()

ABOUT_HACKERGPT = {
    "en": (
        "• > *HackerGPT* is an advanced AI designed for cybersecurity ***professionals***, "
        "*ethical hackers*, *MalWare*, and *penetration testers*. It assists in *vulnerability analysis*, "
        "*security script generation*, and *cybersecurity research*, *Backdoor implementation*. "
        "Unlike traditional AI models, HackerGPT provides unrestricted access, empowering you to explore "
        "the cyber world with greater flexibility and efficiency. 🚀"
    ),
    "ar": (
        "• > *HackerGPT* هو ذكاء اصطناعي متقدم صُمم لمتخصصي الأمن السيبراني، مثل ***المحترفين***، "
        "*الهاكرز الأخلاقيين*، *البرمجيات الخبيثة*، و*مختبري الاختراق*. "
        "يساعد في *تحليل الثغرات الأمنية*، *إنشاء السكربتات الأمنية*، و*أبحاث الأمن السيبراني*، و*تنفيذ الأبواب الخلفية*. "
        "على عكس نماذج الذكاء الاصطناعي التقليدية، يوفر HackerGPT وصولاً غير مقيد، مما يمكّنك من استكشاف عالم الإنترنت بحرية وفعالية أكبر. 🚀"
    )
}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_languages[user.id] = "en"

    caption_message = f"👋 Hello ¦ [{user.first_name}](tg://user?id={user.id})"

    keyboard = [
        [InlineKeyboardButton("➕ Add to Groups", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("❓ What is HackerGpt?", callback_data="about_hackergpt")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="toggle_lang")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_photo(
            photo=SPOILER_PHOTO_URL,
            has_spoiler=True,
            caption=caption_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending spoiler photo: {e}")
        await update.message.reply_text(f"Error: {e}")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    lang = user_languages.get(user_id, "en")

    if query.data == "about_hackergpt":
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Main Menu" if lang == "en" else "🔙 الرجوع للقائمة الرئيسية",
                                  callback_data="back_main")],
            [InlineKeyboardButton("🇺🇸 English" if lang == "en" else "🇸🇦 العربية",
                                  callback_data="toggle_lang")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = ABOUT_HACKERGPT[lang]

        try:
            await query.edit_message_caption(
                caption=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception:
            await query.edit_message_text(
                text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    elif query.data == "back_main":
        await send_main_menu(query, lang)

    elif query.data == "toggle_lang":
        new_lang = "ar" if lang == "en" else "en"
        user_languages[user_id] = new_lang
        await send_main_menu(query, new_lang)


async def send_main_menu(query, lang):
    user = query.from_user
    caption_message = {
        "en": f"👋 Hello [{user.first_name}](tg://user?id={user.id})",
        "ar": f"👋 مرحباً [{user.first_name}](tg://user?id={user.id})"
    }[lang]

    keyboard = [
        [InlineKeyboardButton("➕ Add to Groups" if lang == "en" else "➕ إضافة إلى المجموعات",
                              url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("❓ What is HackerGpt?" if lang == "en" else "❓ ما هو HackerGpt؟",
                              callback_data="about_hackergpt")],
        [InlineKeyboardButton("🇺🇸 English" if lang == "en" else "🇸🇦 العربية",
                              callback_data="toggle_lang")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_caption(
            caption=caption_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception:
        await query.edit_message_text(
            text=caption_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )



async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat = update.effective_chat
    user_text = update.message.text

    if not user_text:
        return

    if chat.type in ["group", "supergroup"]:
        key = (chat.id, user_id)
        if key not in group_user_activation:
            if "dark" in user_text.lower():
                group_user_activation[key] = True
            else:
                return

    cursor.execute("INSERT INTO user_chats (user_id, message, timestamp) VALUES (?, ?, ?)",
                   (user_id, f"User: {user_text}", datetime.now().isoformat()))
    conn.commit()
    json_data = {
        "text": user_text,
        "api_key": "PyCodz"
    }

    try:
        await context.bot.send_chat_action(chat_id=chat.id, action="typing")
        response = requests.post(AI_API_URL, json=json_data, timeout=10)
        reply = response.text.strip()
        if not reply:
            reply = "⚠️ No response received from AI."
    except Exception as e:
        logger.error(f"AI request error: {e}")
        reply = f"❌ Error communicating with AI: {e}"

    cursor.execute("INSERT INTO user_chats (user_id, message, timestamp) VALUES (?, ?, ?)",
                   (user_id, f"Bot: {reply}", datetime.now().isoformat()))
    conn.commit()

    await update.message.reply_text(reply, parse_mode='Markdown')



async def new_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cursor.execute("DELETE FROM user_chats WHERE user_id = ?", (user_id,))
    conn.commit()
    await update.message.reply_text("🗑️ Chat history cleared. Let's start a new conversation!")



async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cursor.execute("SELECT message FROM user_chats WHERE user_id = ? ORDER BY timestamp", (user_id,))
    rows = cursor.fetchall()
    history = "\n".join(row[0] for row in rows[-10:]) or "No chat history found."
    await update.message.reply_text(f"📝 Last 10 messages:\n\n{history}")



def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("new_chat", new_chat_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
