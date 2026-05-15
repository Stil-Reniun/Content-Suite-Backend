import logging
from supabase import create_client
from app.config import settings
from services.auth_service import AuthService
logger = logging.getLogger(__name__)
logger.info("Initializing Supabase client")
supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

def get_auth_service() -> AuthService:
    logger.info("Providing AuthService instance")
    return AuthService(supabase)