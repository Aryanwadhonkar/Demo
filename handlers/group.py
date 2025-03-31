import logging
import time
from telegram import Update
from telegram.ext import MessageHandler, filters, CallbackContext, ChatMemberHandler

from config import settings

logger = logging.getLogger(__name__)

async def group_message_handler(update: Update, context: CallbackContext) -> None:
    """Handles messages in group chats, applying the configured personality and filter."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get user ID
    text = update.message.text

    # Anti-flood mechanism
    now = time.time()
    if user_id in user_message_counts:
        if now - user_message_counts[user_id]['timestamp'] < settings.ANTI_FLOOD_COOLDOWN:
            user_message_counts[user_id]['count'] += 1
            if user_message_counts[user_id]['count'] > settings.SPAM_THRESHOLD:
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

group_message_handler = MessageHandler(filters.TEXT & filters.ChatType.GROUP, group_message_handler)
new_member_handler = ChatMemberHandler(new_member_handler, ChatMemberHandler.CHAT_MEMBERS)
left_member_handler = ChatMemberHandler(left_member_handler, ChatMemberHandler.CHAT_MEMBERS)
chat_member_update_handler = ChatMemberHandler(chat_member_update_handler, ChatMemberHandler.CHAT_MEMBER)
  
