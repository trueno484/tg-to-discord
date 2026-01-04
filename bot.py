import os
import re
import aiohttp
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TG_TOKEN = os.getenv("TG_BOT_TOKEN")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
SOURCE_CHAT_ID = os.getenv("TG_SOURCE_CHAT_ID")  # set after we detect it

# Block rules:
# 1) " ATM" as a full word with a space before it (case-insensitive)
# 2) "accurate signals" phrase any case
# 3) "200%"
# 4) "bonus" any case
BLOCK_REGEXES = [
    r"(?i)atm",          # space before ATM, ATM as its own token
    r"(?i)accurate\s+signals",          # phrase, any case
    r"200%",                            # literal
    r"(?i)\bbonus\b",                   # bonus as a word, any case
    r"(?i)\bperformance\b",
]

compiled = [re.compile(p) for p in BLOCK_REGEXES]

def should_block(text: str) -> bool:
    if not text:
        return True
    for rx in compiled:
        if rx.search(text):
            return True
    return False

async def post_to_discord(content: str) -> None:
    if not DISCORD_WEBHOOK:
        return
    payload = {"content": content[:1900]}
    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK, json=payload) as resp:
            await resp.text()

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat

    # Only send text messages. Ignore photos, videos, stickers, etc.
    if not msg or not msg.text:
        return

    text = msg.text

    # Print chat_id so you can copy it once
    if chat:
        print(f"Message in chat_id={chat.id} title={chat.title}")

    # Lock to one Telegram group if TG_SOURCE_CHAT_ID is set
    if SOURCE_CHAT_ID and str(chat.id) != str(SOURCE_CHAT_ID).strip():
        return

    # Apply filters
    if should_block(text):
        return

    await post_to_discord(text)

def main():
    if not TG_TOKEN:
        raise RuntimeError("TG_BOT_TOKEN not set")
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, on_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()


