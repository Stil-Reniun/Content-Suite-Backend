import logging
from groq import Groq
from app.config import settings
logger = logging.getLogger(__name__)
logger.info("Initializing Groq client")

client = Groq(
    api_key=settings.GROQ_API_KEY
)