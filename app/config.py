# app/config.py
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here"
    database_url: str = "sqlite:///./app.db"
    jwt_secret_key: str = "your-jwt-secret-key-here"
    jwt_expires_hours: int = 24
    jwt_cookie_secure: bool = False
    jwt_cookie_csrf_protect: bool = True
    jwt_cookie_samesite: str = "lax"

    class Config:
        env_file = ".env"

settings = Settings()