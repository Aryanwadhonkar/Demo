# error_handler.py

import logging
from telegram import Update
from telegram.ext import CallbackContext

def log_error(update: Update, context: CallbackContext) -> None:
    """Log the error before handling it."""
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

def handle_invalid_token(update: Update, context: CallbackContext) -> None:
    """Handle invalid token errors."""
    update.message.reply_text("Your token is invalid or has expired. Please get a new token using /gettoken.")

def handle_file_not_found(update: Update, context: CallbackContext) -> None:
    """Handle file not found errors."""
    update.message.reply_text("The requested file was not found or has been deleted.")

def handle_generic_error(update: Update, context: CallbackContext) -> None:
    """Handle any other generic errors."""
    update.message.reply_text("An unexpected error occurred. Please try again later.")
