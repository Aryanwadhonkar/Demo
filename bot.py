import os
import time
import logging
import threading
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
TOKEN_VALIDITY = 86400  # 24 hours in seconds
MEDIA_LIFETIME = 600  # 600 seconds

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# In-memory storage for user tokens and files
user_tokens = {}
sent_files = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! Use /gettoken to get your access token.')

def get_token(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_tokens and time.time() < user_tokens[user_id]['expiry']:
        update.message.reply_text(f'Your token is still valid: {user_tokens[user_id]["token"]}')
    else:
        # Generate a new token
        token = f'token_{user_id}_{int(time.time())}'
        user_tokens[user_id] = {'token': token, 'expiry': time.time() + TOKEN_VALIDITY}
        update.message.reply_text(f'Your new token is: {token}')

def save_file(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text('Only admins can save files.')
        return

    file = update.message.document.get_file()
    file_name = update.message.document.file_name
    file.download(file_name)

    # Send file to the channel
    context.bot.send_document(chat_id=CHANNEL_ID, document=open(file_name, 'rb'))
    
    # Store the file and start a thread to delete it after MEDIA_LIFETIME
    sent_files[file_name] = time.time()
    threading.Thread(target=delete_file_after_timeout, args=(file_name,)).start()
    
    update.message.reply_text('File saved!')

def delete_file_after_timeout(file_name: str) -> None:
    time.sleep(MEDIA_LIFETIME)
    if file_name in sent_files:
        os.remove(file_name)  # Delete the file from the local storage
        del sent_files[file_name]  # Remove from the tracking dictionary
        logging.info(f'Deleted file: {file_name}')

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
