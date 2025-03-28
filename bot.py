import os
import time
import json
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, Updater
from dotenv import load_dotenv
import threading
from error_handler import log_error  # Import the error handler

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(',')))

app = Flask(__name__)
bot = Bot(token=TOKEN)

# Store files and user tokens
file_storage = {}
user_tokens = {}

# Function to generate a token for users
def generate_token(user_id):
    return f"token_{user_id}"

# Command to start the bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /get_token to get your access token.")

# Command to upload files (only for admins)
def upload(update: Update, context: CallbackContext):
    if update.message.from_user.id in ADMIN_IDS:
        file = update.message.document
        if file:
            file_id = file.file_id
            file_storage[file_id] = {
                "file": file,
                "timestamp": time.time()
            }
            update.message.reply_text(f"File {file.file_name} uploaded successfully.")
    else:
        update.message.reply_text("You are not authorized to upload files.")

# Command to get a token
def get_token(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    token = generate_token(user_id)
    user_tokens[user_id] = {
        "token": token,
        "timestamp": time.time()
    }
    update.message.reply_text(f"Your token is: {token}. It will expire in 24 hours.")

# Function to handle incoming messages
def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_tokens:
        if time.time() - user_tokens[user_id]["timestamp"] < 86400:  # 24 hours
            update.message.reply_text("You can access files using the provided links.")
        else:
            update.message.reply_text("Your token has expired. Please get a new one using /get_token.")
    else:
        update.message.reply_text("You need to get a token first using /get_token.")

# Auto-delete files after 600 seconds
def auto_delete_files():
    while True:
        current_time = time.time()
        for file_id, file_info in list(file_storage.items()):
            if current_time - file_info["timestamp"] > 600:
                del file_storage[file_id]
        time.sleep(60)

# Set up the webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("upload", upload))
    dispatcher.add_handler(CommandHandler("get_token", get_token))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_message))

    # Add the error handler
    dispatcher.add_error_handler(log_error)
    
