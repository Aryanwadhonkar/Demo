import os
import requests
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from dotenv import load_dotenv

load_dotenv()

URL_SHORTNER = os.getenv("URL_SHORTNER")
URL_SHORTNER_API = os.getenv("URL_SHORTNER_API")

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

# Register the URL shortening handler
url_handlers = CommandHandler("shorten", shorten_url)
