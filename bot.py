import os
import time
import uuid
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
MONGODB_URL = os.getenv("MONGODB_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
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

        # Generate a unique access link for the file
        access_link = generate_access_link(file.file_id, update.message.from_user.id)

        # Store metadata in MongoDB
        db.files.insert_one({
            "file_id": file.file_id,
            "user_id": update.message.from_user.id,
            "file_name": file_name,
            "timestamp": time.time(),
            "access_link": access_link
        })

        update.message.reply_text(f"File uploaded successfully! Access it here: {access_link}")
    else:
        update.message.reply_text("Please send a document.")

def generate_access_link(file_id, user_id):
    token = create_token(user_id)  # Create a 24-hour token
    access_link = f"https://yourwebservice.com/access?file_id={file_id}&token={token}"  # Replace with your web service URL
    return access_link

def create_token(user_id):
    token = str(uuid.uuid4())  # Generate a unique token
    expiration_time = time.time() + 86400  # Token valid for 24 hours
    db.tokens.insert_one({"token": token, "user_id": user_id, "expires_at": expiration_time})
    return token

def access_media(file_id, token):
    token_data = db.tokens.find_one({"token": token})
    
    if token_data and token_data['expires_at'] > time.time():
        # Logic to retrieve the file based on file_id
        file_data = db.files.find_one({"file_id": file_id})
        if file_data:
            file_path = os.path.join("uploaded_files", file_data['file_name'])  # Adjust as necessary
            return send_file(file_path)  # Serve the file
    else:
        return "Access denied or token expired", 403

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("upload", upload))
    
    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
