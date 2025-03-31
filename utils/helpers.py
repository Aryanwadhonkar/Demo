import logging
import requests

from config import settings

logger = logging.getLogger(__name__)

def shorten_url(long_url: str) -> str:
    try:
        payload = {"url": long_url, "domain": settings.URL_SHORTENER_DOMAIN}
        headers = {"Authorization": f"Bearer {settings.URL_SHORTENER_API}"}
        response = requests.post(f"https://{settings.URL_SHORTENER_DOMAIN}/api", json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("short_url", long_url)
        else:
            return long_url
    except Exception as e:
        logger.error("URL shortening failed: " + str(e))
        return long_url
        
