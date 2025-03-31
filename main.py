import os
import sys
import uuid
import time
import logging
import asyncio
import requests
import html
import traceback
import json  # For handling JSON data
import random
from functools import wraps
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ChatMemberUpdated, BotCommand, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    ChatMemberHandler,
    CallbackQueryHandler,
    AIORateLimiter,
)
from telegram.error import TelegramError

# --- CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_CHANNEL = int(os.getenv("DB_CHANNEL"))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))
FORCE_SUB = os.getenv("FORCE_SUB", "0")
DEVELOPER_CHAT_ID = int(os.getenv("DEVELOPER_CHAT_ID", "0"))  # Add this to your .env
API_ID = os.getenv("API_ID")  # Add this to your .env
API_HASH = os.getenv("API_HASH")  # Add this to your .env
ANTI_FLOOD_COOLDOWN = int(os.getenv("ANTI_FLOOD_COOLDOWN", "3"))
SPAM_THRESHOLD = int(os.getenv("SPAM_THRESHOLD", "5"))  # Number of messages to consider spam

if FORCE_SUB != "0":
    try:
        FORCE_SUB = int(FORCE_SUB)
    except Exception:
        FORCE_SUB = FORCE_SUB.strip()

AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", "0"))  # in minutes
URL_SHORTENER_DOMAIN = os.getenv("URL_SHORTENER_DOMAIN")
URL_SHORTENER_API = os.getenv("URL_SHORTENER_API")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
LANGUAGE_OPTIONS = {
    "en": "English",
    "hi": "Hindi",
    "de": "German",
    "es": "Spanish",
    "ja": "Japanese",
    "fr": "French",
    "ar": "Arabic",
    "zh": "Chinese",
    "ru": "Russian",
}
DEFAULT_LANGUAGE = "en"
ANIME_GIRL_PERSONALITIES = {
    "tsundere": "Im a bit harsh, but secretly care.",
    "yandere": "I am obsessively in love with you.",
    "kuudere": "I am calm, collected, and emotionless.",
    "dandere": "I am shy and quiet, but I open up.",
    "makima": "I expect absolute obedience. Are you ready to serve?",  # Makima
    "random": "I am a mix of all personalities.",  # Mix personality
}
# --- END CONFIGURATION ---

# --- GLOBAL DATA ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
tokens = {}  # token -> { 'data': file_id or [file_ids], 'timestamp': unix_time, 'type': 'single'|'batch' }
banned_users = set()
premium_members = set()
group_settings = {}  # chat_id -> {'personality': 'tsundere', 'filter_level': 'moderate'}
user_message_counts = {}  # user_id -> {'count': int, 'timestamp': float} for anti-flood
# --- END GLOBAL DATA ---

def check_credit():
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            code = f.read()
        if "CHEETAH" not in code:
            logger.error("Credit for CHEETAH has been tampered with. Crashing bot.")
            sys.exit("Credit removed")
    except Exception as e:
        logger.error("Credit check failed: " + str(e))
        sys.exit("Credit check failed")

def print_ascii_art():
    art = r"""
    ____ _ _ ______ _______ _ _ _
   / ___| | | | ____|__ __| \ | | |
  | |   | |_| | |__ | | | \| | |
  | |   | _ | __| | | | . ` | |
  | |___| | | | | | | | |\ | |____
   \____|_| |_|_| |_| |_| \_|______|
    """
    print(art)
    print("Developer: @wleaksOwner | GitHub: Aryanwadhonkar/Cheetah")

def shorten_url(long_url: str) -> str:
    try:
        payload = {"url": long_url, "domain": URL_SHORTENER_DOMAIN}
        headers = {"Authorization": f"Bearer {URL_SHORTENER_API}"}
        response = requests.post(f"https://{URL_SHORTENER_DOMAIN}/api", json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("short_url", long_url)
        else:
            return long_url
    except Exception as e:
        logger.error("URL shortening failed: " + str(e))
        return long_url

async def force_sub_check(update: Update, context: CallbackContext) -> bool:
    if FORCE_SUB != "0":
        try:
            member = await context.bot.get_chat_member(FORCE_SUB, update.effective_user.id)
            if member.status == "left":
                keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB}")]]
                await update.message.reply_text("Please join our channel to use this bot.", reply_markup=InlineKeyboardMarkup(keyboard))
                return False
        except TelegramError:
            await update.message.reply_text("Error verifying your subscription. Try again later.")
            return False
    return True

async def start(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type == "private":
        if FORCE_SUB != "0":
            valid = await force_sub_check(update, context)
            if not valid:
                return

        if update.effective_user.id in banned_users:
            await update.message.reply_text("You are banned from using this bot.")
            return

        context.bot_data.setdefault("users", set()).add(update.effective_user.id)
        args = context.args
        if args:
            token = args[0]
            token_data = tokens.get(token)
            if token_data and (time.time() - token_data["timestamp"] <= 86400):
                data = token_data["data"]
                try:
                    if isinstance(data, list):
                        for msg_id in data:
                            await context.bot.copy_message(chat_id=update.effective_chat.id, from_chat_id=DB_CHANNEL, message_id=msg_id, protect_content=True)
                            if AUTO_DELETE_TIME:
                                context.job_queue.run_once(
                                    lambda ctx: asyncio.create_task(ctx.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)),
                                    AUTO_DELETE_TIME * 60,
                                )
                    else:
                        sent_msg = await context.bot.copy_message(chat_id=update.effective_chat.id, from_chat_id=DB_CHANNEL, message_id=data, protect_content=True)
                        if AUTO_DELETE_TIME:
                            context.job_queue.run_once(
                                lambda ctx: asyncio.create_task(ctx.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)),
                                AUTO_DELETE_TIME * 60,
                            )
                    await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"User {update.effective_user.id} accessed token {token}")
                    del tokens[token]
                except TelegramError as e:
                    logger.error("Error sending file: " + str(e))
                    await update.message.reply_text("Error sending the file. Possibly due to Telegram restrictions.")
            else:
                await update.message.reply_text("Invalid or expired token.")
        else:
            keyboard = [[InlineKeyboardButton(text=LANGUAGE_OPTIONS[lang], callback_data=f"set_language:{lang}") for lang in LANGUAGE_OPTIONS]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Welcome to CHEETAH Bot! Please choose your language:", reply_markup=reply_markup)
    else:
        # Interaction when added to a group
        keyboard = [[InlineKeyboardButton("Set Personality", callback_data="set_personality")] , [InlineKeyboardButton("Set Filter Level", callback_data="set_filter_level")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Hello! I've been added to this group. Admin, please configure me:", reply_markup=reply_markup)

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context)
    return wrapped

@admin_only
async def getlink(update: Update, context: CallbackContext) -> None:
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a media message with /getlink")
        return

    msg = update.message.reply_to_message
    file_id = None
    if msg.document:
        file_id = msg.document.file_id
    elif msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.video:
        file_id = msg.video.file_id
    else:
        await update.message.reply_text("No valid media found in replied message.")
        return

    try:
        forwarded = await context.bot.forward_message(chat_id=DB_CHANNEL, from_chat_id=msg.chat.id, message_id=msg.message_id)
        token = str(uuid.uuid4())[:8]
        tokens[token] = {"data": forwarded.message_id, "timestamp": time.time(), "type": "single"}
        special_link = f"https://t.me/{context.bot.username}?start={token}"
        special_link = shorten_url(special_link)
        await update.message.reply_text(f"File stored!\nToken Link: {special_link}", disable_web_page_preview=True)
        await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"Admin {update.effective_user.id} stored a file. Token: {token}")
    except TelegramError as e:
        logger.error("Error in /getlink: " + str(e))
        await update.message.reply_text("Failed to store file due to an error.")

@admin_only
async def firstbatch(update: Update, context: CallbackContext) -> None:
    context.user_data["batch_files"] = []
    await update.message.reply_text("Batch mode started. Send your files and then use /lastbatch to complete.")

@admin_only
async def lastbatch(update: Update, context: CallbackContext) -> None:
    batch_files = context.user_data.get("batch_files", [])
    if not batch_files:
        await update.message.reply_text("No files received for batch.")
        return

    batch_msg_ids = []
    for file_msg in batch_files:
        try:
            forwarded = await context.bot.forward_message(chat_id=DB_CHANNEL, from_chat_id=file_msg.chat.id, message_id=file_msg.message_id)
            batch_msg_ids.append(forwarded.message_id)
        except TelegramError as e:
            logger.error("Error forwarding batch file: " + str(e))

    token = str(uuid.uuid4())[:8]
    tokens[token] = {"data": batch_msg_ids, "timestamp": time.time(), "type": "batch"}
    special_link = f"https://t.me/{context.bot.username}?start={token}"
    special_link = shorten_url(special_link)
    await update.message.reply_text(f"Batch stored!\nToken Link: {special_link}", disable_web_page_preview=True)
    await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"Admin {update.effective_user.id} stored a batch. Token: {token}")
    context.user_data["batch_files"] = []  # Reset batch mode

@admin_only
async def batch_file_handler(update: Update, context: CallbackContext) -> None:
    if "batch_files" in context.user_data:
        context.user_data["batch_files"].append(update.message)
        await update.message.reply_text("File added to batch.")

@admin_only
async def broadcast(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Provide a message to broadcast.")
        return

    message = " ".join(context.args)
    users = context.bot_data.get("users", set())
    sent_count = 0
    for user_id in users:
        try:
            await context.bot.send_message(user_id, message)
            sent_count += 1
        except TelegramError as e:
            logger.error(f"Error sending broadcast to {user_id}: " + str(e))

    await update.message.reply_text(f"Broadcast sent to {sent_count} users.")

@admin_only
async def stats(update: Update, context: CallbackContext) -> None:
    total_users = len(context.bot_data.get("users", set()))
    active_tokens = len(tokens)
    stats_text = f"Total Users: {total_users}\nActive Tokens: {active_tokens}"
    await update.message.reply_text(stats_text)

@admin_only
async def ban(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Provide a user ID to ban.")
        return

    try:
        user_id = int(context.args[0])
        banned_users.add(user_id)
        await update.message.reply_text(f"User {user_id} has been banned.")
        await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"User {user_id} banned by admin {update.effective_user.id}")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

@admin_only
async def premiummembers(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /premiummembers add|remove ")
        return

    action = context.args[0].lower()
    try:
        user_id = int(context.args[1])
        if action == "add":
            premium_members.add(user_id)
            await update.message.reply_text(f"User {user_id} is now a premium member.")
        elif action == "remove":
            premium_members.discard(user_id)
            await update.message.reply_text(f"User {user_id} has been removed from premium members.")
        else:
            await update.message.reply_text("Invalid action. Use add or remove.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

@admin_only
async def restart(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Restarting bot...")
    await context.bot.send_message(LOG_CHANNEL, f"Bot restarted by admin {update.effective_user.id}")
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def language(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /language ")
        return

    lang = context.args[0].lower()
    if lang in LANGUAGE_OPTIONS:
      context.user_data["language"] = lang
      await update.message.reply_text(f"Language set to {LANGUAGE_OPTIONS[lang]}.")
    else:
      await update.message.reply_text("Invalid Language")

async def report(update: Update, context: CallbackContext) -> None:
    """Handles user reports and feature requests."""
    user_id = update.effective_user.id
    message = " ".join(context.args)

    if not message:
        await update.message.reply_text("Please provide a report or feature request after the /report command.")
        return

    report_text = f"Report from user {user_id}:\n{message}"
    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL, text=report_text)  # Send to log channel for review
        await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=report_text) # Send report to developer
        await update.message.reply_text("Your report has been submitted. Thank you!")
    except TelegramError as e:
        logger.error("Error sending report: " + str(e))
        await update.message.reply_text("Failed to submit your report. Please try again later.")

#chunk2
async def funfact(update: Update, context: CallbackContext) -> None:
    """Handles the /funfact command with personality."""
    chat_id = update.effective_chat.id
    personality = group_settings.get(chat_id, {}).get("personality", "makima")

    try:
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        fun_fact = data.get("text", "Could not retrieve a fun fact at this time.")

        if personality == "makima":
            fun_fact_response = f"Interesting. Did you know this: {fun_fact}? Make sure you remember it."
        elif personality == "random":
            fun_fact_response = f"Did you know this: {fun_fact}"
        else:
            fun_fact_response = fun_fact
        await update.message.reply_text(fun_fact_response)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching fun fact: {e}")
        await update.message.reply_text("Failed to retrieve a fun fact. Please try again later.")

async def advice(update: Update, context: CallbackContext) -> None:
    """Handles the /advice command with personality."""
    chat_id = update.effective_chat.id
    personality = group_settings.get(chat_id, {}).get("personality", "makima")

    try:
        response = requests.get("https://api.adviceslip.com/advice", timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        advice_text = data.get("slip", {}).get("advice", "Could not retrieve advice at this time.")

        if personality == "makima":
            advice_response = f"Listen closely. This is the advice I give you: {advice_text} Heed it well."
        elif personality == "random":
          advice_response = f"Here is a piece of advice: {advice_text}"
        else:
            advice_response = advice_text

        await update.message.reply_text(advice_response)

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
        #chunk3

async def group_message_handler(update: Update, context: CallbackContext) -> None:
    """Handles messages in group chats, applying the configured personality and filter."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get user ID
    text = update.message.text

    # Anti-flood mechanism
    now = time.time()
    if user_id in user_message_counts:
        if now - user_message_counts[user_id]['timestamp'] < ANTI_FLOOD_COOLDOWN:
            user_message_counts[user_id]['count'] += 1
            if user_message_counts[user_id]['count'] > SPAM_THRESHOLD:
                try:
                    await context.bot.ban_chat_member(chat_id, user_id)
                    await update.message.reply_text(f"User {update.effective_user.first_name} banned for spamming.")
                    logger.info(f"User {user_id} banned for spamming in chat {chat_id}")
                except TelegramError as e:
                    logger.error(f"Error banning user {user_id}: {e}")
                return  # Stop processing message

        else:
            # Reset count if cooldown has passed
            user_message_counts[user_id] = {'count': 1, 'timestamp': now}
    else:
        user_message_counts[user_id] = {'count': 1, 'timestamp': now}

    settings = group_settings.get(chat_id, {})
    personality = settings.get("personality", "makima")  # Default to Makima
    filter_level = settings.get("filter_level", "moderate")  # Default to moderate

    # --- PERSONALITY ---
    if personality and text:
        if personality in ANIME_GIRL_PERSONALITIES:
            personality_text = ANIME_GIRL_PERSONALITIES[personality]
            # Basic personality-based response (customize as needed)

            if personality == "makima":
                if "hello" in text.lower():
                    response_text = f"{personality_text} Good, you recognize my authority."
                elif "thank you" in text.lower():
                    response_text = f"{personality_text} You're welcome. Your gratitude is expected."
                elif "help" in text.lower():
                    response_text = f"{personality_text} Obey my commands, and you won't need help."
                else:
                    response_text = f"{personality_text} Speak when spoken to."

            elif personality == "random":
                # Random personality response (add more as desired)
                import random
                available_personalities = list(ANIME_GIRL_PERSONALITIES.keys())
                chosen_personality = random.choice(available_personalities)
                personality_text = ANIME_GIRL_PERSONALITIES[chosen_personality]
                response_text = f"*{chosen_personality.capitalize()}* {personality_text}"  # Add a personality indicator

            else:
                if "hello" in text.lower():
                    response_text = f"{personality_text} Hmph, don't think I'm happy you greeted me!"
                elif "thank you" in text.lower():
                    response_text = f"{personality_text} It's not like I did it for you or anything!"
                else:
                    response_text = f"{personality_text} What do you want?"

            await update.message.reply_text(response_text)
    # --- END PERSONALITY ---

    # --- AUTO FILTER ---
    if filter_level:
        # Basic profanity filter (expand as needed)
        profane_words = ["badword1", "badword2", "badword3"]  # Replace with actual words
        if any(word in text.lower() for word in profane_words):
            if filter_level == "high":
                await update.message.delete()
                await context.bot.send_message(chat_id, "Profanity is not allowed.")
            elif filter_level == "moderate":
                # Mild warning
                await context.bot.send_message(chat_id, "Please refrain from using inappropriate language.")
    # --- END AUTO FILTER ---

async def post_initializer(application: Application) -> None:
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("getlink", "Get a token link for a file (reply to the file)"),
        BotCommand("firstbatch", "Start a batch file upload"),
        BotCommand("lastbatch", "Finish a batch file upload"),
        BotCommand("broadcast", "Broadcast a message to all users (admin only)"),
        BotCommand("stats", "Show bot statistics (admin only)"),
        BotCommand("ban", "Ban a user (admin only)"),
        BotCommand("premiummembers", "Manage premium members (admin only)"),
        BotCommand("restart", "Restart the bot (admin only)"),
        BotCommand("language", "Set your language"),
        BotCommand("report", "Report a problem or request a feature"),
        BotCommand("funfact", "Get a random fun fact"),  # New command
        BotCommand("advice", "Get some advice"),  # New command
        BotCommand("coinflip", "Flip a coin!"), # New fun command
        BotCommand("roll", "Roll a dice!"),# New Fun Command
        BotCommand("meme", "Get a random meme"), # New Fun Command
        BotCommand("joke", "Tell me a joke!"),# New Fun Command

    ]
    await application.bot.set_my_commands(commands)

async def new_member_handler(update: Update, context: CallbackContext) -> None:
    """Handles new chat members joining the group."""
    new_members = update.message.new_chat_members
    chat_id = update.effective_chat.id

    for member in new_members:
        if member.is_bot:
            # A bot was added, configure the bot
            keyboard = [[InlineKeyboardButton("Set Personality", callback_data="set_personality")], [InlineKeyboardButton("Set Filter Level", callback_data="set_filter_level")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Thank you for adding me! Admin, please configure my personality and filter level:", reply_markup=reply_markup)
        else:
            # A user joined, welcome them (optional)
            welcome_message = f"Welcome, {member.first_name}, to the group!"
            await context.bot.send_message(chat_id, welcome_message)

async def left_member_handler(update: Update, context: CallbackContext) -> None:
    """Handles chat members leaving the group."""
    chat_id = update.effective_chat.id
    user = update.message.left_chat_member

    # Check if a user or bot left
    if user.is_bot:
        # A bot left, handle accordingly
        await context.bot.send_message(LOG_CHANNEL, f"Bot {user.username} left chat {chat_id}.")
    else:
        # A user left, handle accordingly (e.g., log it)
        await context.bot.send_message(LOG_CHANNEL, f"User {user.first_name} left chat {chat_id}.")

async def chat_member_update_handler(update: Update, context: CallbackContext) -> None:
    """Handles chat member updates, such as a user being banned or unbanned."""
    chat_id = update.effective_chat.id
    user = update.chat_member.new_chat_member.user
    status = update.chat_member.new_chat_member.status

    if status == "kicked":
        # User was banned
        await context.bot.send_message(LOG_CHANNEL, f"User {user.first_name} was banned from chat {chat_id}.")
    elif status == "member":
        # User was unbanned or rejoined
        await context.bot.send_message(LOG_CHANNEL, f"User {user.first_name} rejoined chat {chat_id}.")

async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if data.startswith("set_language:"):
        lang = data.split(":")[1]
        context.user_data["language"] = lang
        await query.edit_message_text(f"Language set to {LANGUAGE_OPTIONS[lang]}!")

    elif data == "set_personality":
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the personality.", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton(text=personality.capitalize(), callback_data=f"personality:{key}")] for key, personality in ANIME_GIRL_PERSONALITIES.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose the bot's personality:", reply_markup=reply_markup)

    elif data.startswith("personality:"):
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the personality.", show_alert=True)
            return
        personality = data.split(":")[1]
        group_settings[chat_id] = group_settings.get(chat_id, {})
        group_settings[chat_id]["personality"] = personality
        await query.edit_message_text(f"Bot personality set to {personality}.")

    elif data == "set_filter_level":
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the filter level.", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton(text="Low", callback_data="filter:low")],
            [InlineKeyboardButton(text="Moderate", callback_data="filter:moderate")],
            [InlineKeyboardButton(text="High", callback_data="filter:high")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose the filter level:", reply_markup=reply_markup)

    elif data.startswith("filter:"):
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the filter level.", show_alert=True)
            return
        filter_level = data.split(":")[1]
        group_settings[chat_id] = group_settings.get(chat_id, {})
        group_settings[chat_id]["filter_level"] = filter_level
        await query.edit_message_text(f"Filter level set to {filter_level}.")

def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        # Collect error information
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)

        # Build the message
        message = (
            f'An exception was raised while handling an update:\n'
            f'<pre>update = {html.escape(str(update.to_dict()), quote=False)}</pre>\n'
            f'<pre>context.chat_data = {html.escape(str(context.chat_data), quote=False)}</pre>\n'
            f'<pre>context.user_
        
