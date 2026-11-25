import logging
import sqlite3
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# APNI DETAILS YAHAAN BHAREIN
BOT_TOKEN = "9290632324:AAHJe2t-k2W9Ux3E7_xRALnxKEub0hCAyeU"
ADMIN_ID = 7441057457

DB = "livechat.db"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def database():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            admin_message_id INTEGER PRIMARY KEY,
            user_id INTEGER
        )
    """)
    con.commit()
    return con


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "👑 ADMIN PANEL\n\n"
            "User ke message par Reply karke jawab dein.\n"
            "Aapka jawab seedha user ko milega.\n\n"
            "/stats - Total users"
        )
        return

    con = database()
    con.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
        (user.id, user.full_name, user.username)
    )
    con.commit()
    con.close()

    await update.message.reply_text(
        f"how are you {user.first_name}! ❤️\n\n"
        "Welcome to our Live Chat Support.\n"
        "Aap apna message bhejiye.\n"
        "Hamari team jald hi aapko reply karegi. 💬"
    )

    await context.bot.send_message(
        ADMIN_ID,
        f"🆕 NEW USER\n\n"
        f"👤 Name: {user.full_name}\n"
        f"🔗 Username: @{user.username or 'Not Available'}\n"
        f"🆔 ID: {user.id}"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    con = database()
    count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    con.close()

    await update.message.reply_text(
        f"📊 Total Registered Users: {count}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if user.id == ADMIN_ID:
        if not message.reply_to_message:
            await message.reply_text(
                "Kisi user ke message par Reply karke jawab dein."
            )
            return

        con = database()
        result = con.execute(
            "SELECT user_id FROM messages WHERE admin_message_id = ?",
            (message.reply_to_message.message_id,)
        ).fetchone()
        con.close()

        if not result:
            await message.reply_text(
                "❌ User nahi mila. Original user message par Reply karein."
            )
            return

        target_id = result[0]

        try:
            await context.bot.copy_message(
                chat_id=target_id,
                from_chat_id=ADMIN_ID,
                message_id=message.message_id
            )
            await message.reply_text("✅ Reply successfully sent!")
        except Exception:
            await message.reply_text(
                "❌ Message nahi bheja ja saka. User ne bot block kiya ho sakta hai."
            )
        return

    con = database()
    con.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
        (user.id, user.full_name, user.username)
    )
    con.commit()
    con.close()

    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"📩 NEW MESSAGE\n\n"
            f"👤 {user.full_name}\n"
            f"🔗 @{user.username or 'Not Available'}\n"
            f"🆔 {user.id}\n\n"
            "👇 Iske neeche wale message par Reply karein:"
        )

        copied = await context.bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=update.effective_chat.id,
            message_id=message.message_id
        )

        con = database()
        con.execute(
            "INSERT OR REPLACE INTO messages VALUES (?, ?)",
            (copied.message_id, user.id)
        )
        con.commit()
        con.close()

    except Exception:
        logging.exception("Message forwarding failed")


def main():
    database()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, handle_message)
    )

    print("🔥 LIVE CHAT BOT STARTED!")
    app.run_polling()


if __name__ == "__main__":
    main()
