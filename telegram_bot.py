import os

BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
RECIPENT_ID = os.getenv('RECIPENT_ID')

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name} with id {update.effective_user.id}')


telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))


