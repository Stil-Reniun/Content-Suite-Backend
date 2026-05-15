import logging
from supabase import Client

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def login(self, email: str, password: str) -> dict:
        # Authenticate user with Supabase Auth and return their profile.
        logger.info(f"Login attempt for: {email}")
        auth_res = self.supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if not auth_res.session:
            logger.error(f"Invalid credentials for: {email}")
            raise Exception("Invalid credentials")
        user_id = auth_res.user.id
        profile_res = (
            self.supabase.table("profile_users")
            .select("id, full_name, email, role, avatar_url, is_active")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not profile_res.data:
            logger.error(f"Profile not found for user_id: {user_id}")
            raise Exception("User profile not found")
        logger.info(f"User logged in successfully: {email}")
        return profile_res.data

    def register(self, email: str, password: str, full_name: str, role: str) -> dict:
        # Create a new user in Supabase Auth and insert a profile record.
        logger.info(f"Registering user: {email}")
        auth_res = self.supabase.auth.sign_up(
            {"email": email, "password": password}
        )
        if not auth_res.user:
            logger.error(f"User registration failed: {email}")
            raise Exception("User registration failed")
        user_id = auth_res.user.id
        profile_data = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role,
        }
        res = self.supabase.table("profile_users").insert(profile_data).execute()
        if not res.data:
            logger.error(f"Profile creation failed for: {email}")
            raise Exception("Profile creation failed")
        logger.info(f"User registered successfully: {email}")
        return res.data[0]
