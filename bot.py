import os
import time
import logging
import threading
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, Defaults
from dotenv import load_dotenv
from error_handler import log_error, handle_invalid_token, handle_file_not_found, handle_generic_error

load_dotenv()

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Use the channel username or ID
ADMIN_IDS = [123456789, 987654321]  # Replace with actual Telegram user IDs of admins
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
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text('Only admins can save files.')
        return

    try:
        file = update.message.document.get_file()
        file_name = update.message.document.file_name
        file.download(file_name)

        # Send file to the private channel
        context.bot.send_document(chat_id=CHANNEL_ID, document=open(file_name, 'rb'))
        
        # Store the file and start a thread to delete it after MEDIA_LIFETIME
        sent_files[file_name] = time.time()
        threading.Thread(target=delete_file_after_timeout, args=(file_name,)).start()
        
        update.message.reply_text('File saved in the private channel!')
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        handle_generic_error(update, context)

def delete_file_after_timeout(file_name: str) -> None:
    time.sleep(MEDIA_LIFETIME)
    if file_name in sent_files:
        try:
            os.remove(file_name)  # Delete the file from the local storage
            del sent_files[file_name]  # Remove from the tracking dictionary
            logging.info(f'Deleted file: {file_name}')
        except FileNotFoundError:
            logging.warning(f'File not found for deletion: {file_name}')
        except Exception as e:
            logging.error(f"Error deleting file: {e}")

def main() -> None:
    # Set up the bot with a custom timeout and other defaults
    defaults = Defaults(parse_mode='HTML', timeout=10)  # Timeout is in seconds
    updater = Updater(TELEGRAM_TOKEN, defaults=defaults)
    
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("gettoken", get_token))
    dispatcher.add_handler(MessageHandler(Filters.document, save_file))

    # Error handlers
    dispatcher.add_error_handler(log_error)
    dispatcher.add_error_handler(handle_invalid_token)
    dispatcher.add_error_handler(handle_file_not_found)
    dispatcher.add_error_handler(handle_generic_error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
