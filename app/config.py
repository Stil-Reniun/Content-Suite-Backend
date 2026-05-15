# ============================================
# APPLICATION CONFIGURATION
# Environment variables and global settings
# ============================================
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    def __init__(self):
        self.APP_NAME = "Content Suite API"
        self.ENV = os.getenv("ENV", "dev")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        self.GOOGLE_IA_STUDIO_API_KEY = os.getenv("GOOGLE_IA_STUDIO_API_KEY")
        self.LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
        self.LANGFUSE_BASE_URL = os.getenv(
            "LANGFUSE_BASE_URL",
            "https://cloud.langfuse.com"
        )

# Global settings instance
settings = Settings()
