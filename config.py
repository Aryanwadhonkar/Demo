import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_CHANNEL = int(os.getenv("DB_CHANNEL"))
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))
    FORCE_SUB = os.getenv("FORCE_SUB", "0")
    DEVELOPER_CHAT_ID = int(os.getenv("DEVELOPER_CHAT_ID", "0"))
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    ANTI_FLOOD_COOLDOWN = int(os.getenv("ANTI_FLOOD_COOLDOWN", "3"))
    SPAM_THRESHOLD = int(os.getenv("SPAM_THRESHOLD", "5"))
    AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", "0"))
    URL_SHORTENER_DOMAIN = os.getenv("URL_SHORTENER_DOMAIN")
    URL_SHORTENER_API = os.getenv("URL_SHORTENER_API")
    ADMINS = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
    DEFAULT_LANGUAGE = "en"  # You can expand upon this later
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

settings = Settings()
