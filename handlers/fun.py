import logging
import requests
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from config import settings

logger = logging.getLogger(__name__)

async def funfact(update: Update, context: CallbackContext) -> None:
    """Handles the /funfact command with personality."""
    chat_id = update.effective_chat.id
    #personality = group_settings.get(chat_id, {}).get("personality", "makima")

    try:
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        fun_fact = data.get("text", "Could not retrieve a fun fact at this time.")

        #if personality == "makima":
        fun_fact_response = f"Interesting. Did you know this: {fun_fact}? Make sure you remember it."
        #elif personality == "random":
        #    fun_fact_response = f"Did you know this: {fun_fact}"
        #else:
        #   fun_fact_response = fun_fact
        await update.message.reply_text(fun_fact_response)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching fun fact: {e}")
        await update.message.reply_text("Failed to retrieve a fun fact. Please try again later.")

async def advice(update: Update, context: CallbackContext) -> None:
    """Handles the /advice command with personality."""
    chat_id = update.effective_chat.id
    #personality = group_settings.get(chat_id, {}).get("personality", "makima")

    try:
        response = requests.get("https://api.adviceslip.com/advice", timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        advice_text = data.get("slip", {}).get("advice", "Could not retrieve advice at this time.")

        #if personality == "makima":
        advice_response = f"Listen closely. This is the advice I give you: {advice_text} Heed it well."
        #elif personality == "random":
        #  advice_response = f"Here is a piece of advice: {advice_text}"
        #else:
        #    advice_response = advice_text

        await update.message.reply_text(advice_response)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching advice: {e}")
        await update.message.reply_text("Failed to retrieve advice. Please try again later.")

async def coinflip(update: Update, context: CallbackContext) -> None:
    """Handles the /coinflip command."""
    result = random.choice(["Heads", "Tails"])
    await update.message.reply_text(f"The coin landed on: {result}")

async def roll(update: Update, context: CallbackContext) -> None:
    """Handles the /roll command."""
    result = random.randint(1, 6)
    await update.message.reply_text(f"You rolled a: {result}")

async def meme(update: Update, context: CallbackContext) -> None:
    """Handles the /meme command."""
    try:
        response = requests.get("https://meme-api.com/gimme", timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        meme_url = data.get("url", None)

        if meme_url:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=meme_url)
        else:
            await update.message.reply_text("Could not retrieve a meme at this time.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching meme: {e}")
        await update.message.reply_text("Failed to retrieve a meme. Please try again later.")

async def joke(update: Update, context: CallbackContext) -> None:
    """Handles the /joke command."""
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,racist,sexist,explicit&safe-mode", timeout=5)
        response.raise_for_status()
        data = response.json()

        if data["type"] == "single":
            joke = data["joke"]
        else:
            joke = f"{data['setup']}\n\n{data['delivery']}"

        await update.message.reply_text(joke)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching joke: {e}")
        await update.message.reply_text("Failed to retrieve a joke. Please try again later.")

funfact_handler = CommandHandler("funfact", funfact)
advice_handler = CommandHandler("advice", advice)
coinflip_handler = CommandHandler("coinflip", coinflip)
roll_handler = CommandHandler("roll", roll)
meme_handler = CommandHandler("meme", meme)
joke_handler = CommandHandler("joke", joke)
  
