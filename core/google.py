from openai import OpenAI
from app.config import settings

if not settings.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
VISION_MODEL = "gpt-4o"