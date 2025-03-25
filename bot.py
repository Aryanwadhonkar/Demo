import os
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
MONGODB_URL = os.getenv("MONGODB_URL")
URL_SHORTNER = os.getenv("URL_SHORTNER")
URL_SHORTNER_API = os.getenv("URL_SHORTNER_API")
OWNER_ID = int(os.getenv("OWNER_ID"))
ADMINS_ID = list(map(int, os.getenv("ADMINS_ID").split(',')))
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT"))
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Add your private channel ID here

# Initialize MongoDB client
client = MongoClient(MONGODB_URL)
db = client['file_database']

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /upload to upload files.")

def upload(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMINS_ID:
        update.message.reply_text("You are not authorized to upload files.")
        return

    if update.message.document:
        file = update.message.document.get_file()
        file_name = update.message.document.file_name
        file_path = os.path.join("uploaded_files", file_name)

        # Download the file to the local filesystem
        file.download(file_path)

        # Send the file to the private channel
        with open(file_path, 'rb') as f:
            context.bot.send_document(chat_id=CHANNEL_ID, document=f, caption=f"Uploaded by {update.message.from_user.first_name}: {file_name}")

        # Store metadata in MongoDB
        db.files.insert_one({
            "file_id": update.message.document.file_id,
            "user_id": update.message.from_user.id,
            "file_name": file_name,
            "timestamp": time.time()
        })

        update.message.reply_text("File uploaded successfully to the channel!")
    else:
        update.message.reply_text("Please send a document.")

def get_file(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /getfile <file_id>")
        return

    file_id = context.args[0]
    file_data = db.files.find_one({"file_id": file_id})

    if file_data:
        update.message.reply_text(f"File found: {file_data['file_name']}. You can access it in the channel.")
    else:
        update.message.reply_text("File not found.")

def shorten_url(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /shorten <url>")
        return

    long_url = context.args[0]
    response = requests.post(URL_SHORTNER, json={"long_url": long_url, "api_token": URL_SHORTNER_API})
    
    if response.status_code == 200:
        short_url = response.json().get("short_url")
        update.message.reply_text(f"Shortened URL: {short_url}")
    else:
        update.message.reply_text("Failed to shorten URL.")

def auto_delete_media(update: Update, context: CallbackContext):
    time.sleep(900)  # 15 minutes
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("upload", upload))
    dp.add_handler(CommandHandler("getfile", get_file))
    dp.add_handler(CommandHandler("shorten", shorten_url))
    dp.add_handler(MessageHandler(Filters.document, upload))
    
    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
