from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext

from config import settings

async def start(update: Update, context: CallbackContext) -> None:
    """Sends the welcome message."""
    if update.effective_chat.type == "private":
        keyboard = [[InlineKeyboardButton(text=settings.LANGUAGE_OPTIONS[lang], callback_data=f"set_language:{lang}") for lang in settings.LANGUAGE_OPTIONS]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Welcome to CHEETAH Bot! Please choose your language:", reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("Set Personality", callback_data="set_personality")] , [InlineKeyboardButton("Set Filter Level", callback_data="set_filter_level")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Hello! I've been added to this group. Admin, please configure me:", reply_markup=reply_markup)

async def language(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /language ")
        return

    lang = context.args[0].lower()
    if lang in settings.LANGUAGE_OPTIONS:
      context.user_data["language"] = lang
      await update.message.reply_text(f"Language set to {settings.LANGUAGE_OPTIONS[lang]}.")
    else:
      await update.message.reply_text("Invalid Language")

start_handler = CommandHandler("start", start)
language_handler = CommandHandler("language", language)
