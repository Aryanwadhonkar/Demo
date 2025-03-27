import os
import logging
from flask import Flask, request, send_file
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv  # Import dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Bot configuration
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
CHANNEL_ID = os.getenv('CHANNEL_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Create a directory to store files
if not os.path.exists('files'):
    os.makedirs('files')

# Function to start the bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! You can send me files to store.')

# Function to handle file uploads
def handle_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document.get_file()
    file_path = os.path.join('files', update.message.document.file_name)
    file.download(file_path)

    # Send the file to the channel
    with open(file_path, 'rb') as f:
        context.bot.send_document(chat_id=CHANNEL_ID, document=InputFile(f, filename=update.message.document.file_name))

    update.message.reply_text(f'File {update.message.document.file_name} has been uploaded!')

# Function to handle errors
def error(update: Update, context: CallbackContext) -> None:
    logging.warning(f'Update {update} caused error {context.error}')

# Set up the bot
def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_file))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

# Flask route to serve files
@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    return send_file(os.path.join('files', filename), as_attachment=True)

if __name__ == '__main__':
    from threading import Thread
    # Start the bot in a separate thread
    Thread(target=main).start()
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000)
