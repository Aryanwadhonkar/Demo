import os
import time
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
URL_SHORTENER_API = os.getenv("URL_SHORTENER_API")
TOKEN_VALIDITY = 86400  # 24 hours in seconds
MEDIA_LIFETIME = 600  # 600 seconds

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# In-memory storage for user tokens
user_tokens = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! Use /gettoken to get your access token.')

def get_token(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_tokens and time.time() < user_tokens[user_id]['expiry']:
        update.message.reply_text(f'Your token is still valid: {user_tokens[user_id]["token"]}')
    else:
        # Generate a new token (you can implement a more secure token generation)
        token = f'token_{user_id}_{int(time.time())}'
        user_tokens[user_id] = {'token': token, 'expiry': time.time() + TOKEN_VALIDITY}
        update.message.reply_text(f'Your new token is: {token}')

def save_file(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text('Only admins can save files.')
        return

    file = update.message.document.get_file()
    file.download()
    # Send file to the channel
    context.bot.send_document(chat_id=CHANNEL_ID, document=open(update.message.document.file_name, 'rb'))
    update.message.reply_text('File saved!')

def access_file(update: Update, context: CallbackContext) -> None:
    # Logic to handle file access based on the link clicked
    pass

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("gettoken", get_token))
    dispatcher.add_handler(MessageHandler(Filters.document, save_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
