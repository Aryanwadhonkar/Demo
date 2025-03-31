import os
import logging
from telegram.ext import Application

from config import settings  # Import settings from config.py
from handlers import basic, admin, fun, group # Import handlers
from utils import helpers  # Import helper functions

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""

    #Set up rate limiter
    rate_limiter = AIORateLimiter(max_retries=3)

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.BOT_TOKEN).rate_limiter(rate_limiter).build()

    # Add command handlers
    application.add_handler(basic.start_handler)

    #Admin handlers
    application.add_handler(admin.getlink_handler)
    application.add_handler(admin.firstbatch_handler)
    application.add_handler(admin.lastbatch_handler)
    application.add_handler(admin.broadcast_handler)
    application.add_handler(admin.stats_handler)
    application.add_handler(admin.ban_handler)
    application.add_handler(admin.premiummembers_handler)
    application.add_handler(admin.restart_handler)

    #Fun Handlers
    application.add_handler(fun.funfact_handler)
    application.add_handler(fun.advice_handler)
    application.add_handler(fun.coinflip_handler)
    application.add_handler(fun.roll_handler)
    application.add_handler(fun.meme_handler)
    application.add_handler(fun.joke_handler)

    #Group handlers
    application.add_handler(group.group_message_handler)
    application.add_handler(group.new_member_handler)
    application.add_handler(group.left_member_handler)
    application.add_handler(group.chat_member_update_handler)

    application.add_handler(basic.language_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
