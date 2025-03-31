import uuid
import time
import logging
from functools import wraps
from telegram import Update, TelegramError, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext

from config import settings
from utils import helpers

logger = logging.getLogger(__name__)

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        if update.effective_user.id not in settings.ADMINS:
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
        forwarded = await context.bot.forward_message(chat_id=settings.DB_CHANNEL, from_chat_id=msg.chat.id, message_id=msg.message_id)
        token = str(uuid.uuid4())[:8]
        #tokens[token] = {"data": forwarded.message_id, "timestamp": time.time(), "type": "single"}
        special_link = f"https://t.me/{context.bot.username}?start={token}"
        special_link = helpers.shorten_url(special_link)
        await update.message.reply_text(f"File stored!\nToken Link: {special_link}", disable_web_page_preview=True)
        await context.bot.send_message(chat_id=settings.LOG_CHANNEL, text=f"Admin {update.effective_user.id} stored a file. Token: {token}")
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
            forwarded = await context.bot.forward_message(chat_id=settings.DB_CHANNEL, from_chat_id=file_msg.chat.id, message_id=file_msg.message_id)
            batch_msg_ids.append(forwarded.message_id)
        except TelegramError as e:
            logger.error("Error forwarding batch file: " + str(e))

    token = str(uuid.uuid4())[:8]
    #tokens[token] = {"data": batch_msg_ids, "timestamp": time.time(), "type": "batch"}
    special_link = f"https://t.me/{context.bot.username}?start={token}"
    special_link = helpers.shorten_url(special_link)
    await update.message.reply_text(f"Batch stored!\nToken Link: {special_link}", disable_web_page_preview=True)
    await context.bot.send_message(chat_id=settings.LOG_CHANNEL, text=f"Admin {update.effective_user.id} stored a batch. Token: {token}")
    context.user_data["batch_files"] = []  # Reset batch mode

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
    #active_tokens = len(tokens)
    stats_text = f"Total Users: {total_users}\nActive Tokens: {active_tokens}"
    await update.message.reply_text(stats_text)

@admin_only
async def ban(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Provide a user ID to ban.")
        return

    try:
        user_id = int(context.args[0])
        #banned_users.add(user_id)
        await update.message.reply_text(f"User {user_id} has been banned.")
        await context.bot.send_message(chat_id=settings.LOG_CHANNEL, text=f"Admin {update.effective_user.id} banned by admin {update.effective_user.id}")
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
            #premium_members.add(user_id)
            await update.message.reply_text(f"User {user_id} is now a premium member.")
        elif action == "remove":
            #premium_members.discard(user_id)
            await update.message.reply_text(f"User {user_id} has been removed from premium members.")
        else:
            await update.message.reply_text("Invalid action. Use add or remove.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

@admin_only
async def restart(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Restarting bot...")
    await context.bot.send_message(chat_id=settings.LOG_CHANNEL, text=f"Bot restarted by admin {update.effective_user.id}")
    os.execv(sys.executable, [sys.executable] + sys.argv)

getlink_handler = CommandHandler("getlink", getlink)
firstbatch_handler = CommandHandler("firstbatch", firstbatch)
lastbatch_handler = CommandHandler("lastbatch", lastbatch)
broadcast_handler = CommandHandler("broadcast", broadcast)
stats_handler = CommandHandler("stats", stats)
ban_handler = CommandHandler("ban", ban)
premiummembers_handler = CommandHandler("premiummembers", premiummembers)
restart_handler = CommandHandler("restart", restart)
