import os
import logging
from flask import Flask, request, send_file
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
import uuid

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
OWNER_ID = int(os.getenv('OWNER_ID'))  # Add your Telegram user ID here

# Create a directory to store files
if not os.path.exists('files'):
    os.makedirs('files')

# Dictionary to store file links
file_links = {}

# Function to start the bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! You can send me files to store.')

# Function to handle file uploads
def handle_file(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text('You are not authorized to upload files.')
        return

    file = update.message.document.get_file()
    file_id = str(uuid.uuid4())  # Generate a unique ID for the file
    file_path = os.path.join('files', f"{file_id}_{update.message.document.file_name}")
    file.download(file_path)

    # Send the file to the channel
    with open(file_path, 'rb') as f:
        context.bot.send_document(chat_id=CHANNEL_ID, document=InputFile(f, filename=update.message.document.file_name))

    # Store the link
    file_links[file_id] = file_path

    update.message.reply_text(f'File {update.message.document.file_name} has been uploaded! Access it using /file_{file_id}')

# Function to handle errors
def error(update: Update, context: CallbackContext) -> None:
    logging.warning(f'Update {update} caused error {context.error}')

# Function to access files via links
def access_file(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text('Please provide a valid file ID.')
        return

    file_id = context.args[0]
    if file_id in file_links:
        file_path = file_links[file_id]
        with open(file_path, 'rb') as f:
            update.message.reply_document(document=InputFile(f, filename=os.path.basename(file_path)))
    else:
        update.message.reply_text('File not found.')

# Set up the bot
def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_file))
    dispatcher.add_handler(CommandHandler("file_", access_file))  # Add command to access files
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
