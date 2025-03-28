import logging
from telegram import Update
from telegram.ext import CallbackContext

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

def log_error(update: Update, context: CallbackContext):
    """Log the error before sending a message to the user."""
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    # Optionally, you can notify the user about the error
    if update.effective_chat:
        update.effective_chat.send_message(
            text="An error occurred while processing your request. Please try again later."
        )
