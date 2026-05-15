import logging
from langfuse import Langfuse
from app.config import settings


logging.getLogger("langfuse").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("Initializing Langfuse client")

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL,
    debug=False,
)

# Verify connection on startup
try:
    langfuse.auth_check()
    logger.info("Langfuse authentication successful")
except Exception as e:
    logger.error(f"Langfuse authentication failed: {e}")

# Simple helper to flush events explicitly if needed
def flush_langfuse():
    try:
        langfuse.flush()
        logger.info("Langfuse events flushed successfully")
    except Exception as e:
        logger.warning(f"Langfuse flush failed: {e}")
