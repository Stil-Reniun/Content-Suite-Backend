from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.auth_service import AuthService
from core.supabase_client import get_auth_service
import logging
logger = logging.getLogger(__name__)
router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str

@router.post("/login")
def login(data: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    #Authenticates user with email/password via Supabase Auth.
    logger.info(f"POST /login - {data.email}")
    try:
        user = auth.login(data.email, data.password)
        return {
            "success": True,
            "user": user
        }
    except Exception as e:
        logger.error(f"Login failed for {data.email}: {e}")
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/register")
def register(data: RegisterRequest, auth: AuthService = Depends(get_auth_service)):
    #Creates a new user account and profile.
    logger.info(f"POST /register - {data.email}")
    try:
        user = auth.register(
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            role=data.role,
        )
        return {
            "success": True,
            "user": user
        }
    except Exception as e:
        logger.error(f"Register failed for {data.email}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
