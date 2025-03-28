import os
import time
import requests
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Constants
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
CHANNEL_ID = '@your_private_channel'
LINK_SHORTENER_API = 'https://api.urlshortener.com/shorten'
DEV_API_KEY = 'YOUR_DEV_API_KEY'
TOKEN_VALIDITY = 86400  # 24 hours in seconds
MEDIA_LIFETIME = 600  # 600 seconds

# In-memory storage for user tokens
user_tokens = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! Use /upload to upload files.')

def upload(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in user_tokens:
        update.message.reply_text('You need a valid token to upload files. Use /get_token.')
        return

    if update.message.document:
        file = update.message.document.get_file()
        file.download()
        # Send file to the private channel
        context.bot.send_document(chat_id=CHANNEL_ID, document=open(update.message.document.file_name, 'rb'))
        # Generate a link for the user
        link = generate_link(update.message.document.file_name)
        update.message.reply_text(f'File uploaded! Access it here: {link}')
        # Schedule auto-delete
        time.sleep(MEDIA_LIFETIME)
        os.remove(update.message.document.file_name)

def generate_link(file_name: str) -> str:
    # Shorten the link using the URL shortener API
    response = requests.post(LINK_SHORTENER_API, json={'url': f'https://t.me/{CHANNEL_ID}/{file_name}', 'api_key': DEV_API_KEY})
    return response.json().get('shortened_url')

def get_token(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_tokens and time.time() - user_tokens[user_id] < TOKEN_VALIDITY:
        update.message.reply_text('You already have a valid token.')
    else:
        # Generate a new token
        user_tokens[user_id] = time.time()
        update.message.reply_text('Your token has been generated!')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("upload", upload))
    dispatcher.add_handler(CommandHandler("get_token", get_token))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
