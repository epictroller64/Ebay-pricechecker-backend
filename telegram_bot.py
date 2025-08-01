import os

BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
RECIPENT_ID = os.getenv('RECIPENT_ID')
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name} with id {update.effective_user.id}')

if os.getenv("RUN_TG") == "TRUE":
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()


    telegram_app.add_handler(CommandHandler("start", start))


    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
else:
    telegram_app = None


