import logging
from openai import OpenAI
from app.config import settings
logger = logging.getLogger(__name__)
logger.info("Initializing OpenAI client")

client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)