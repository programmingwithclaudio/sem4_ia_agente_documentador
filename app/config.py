from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación"""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:mermaiddev@localhost:5432/auth_db"
    database_sync_url: str = "postgresql://postgres:mermaiddev@localhost:5432/auth_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security - JWT
    secret_key: str = "change-this-super-secret-key"
    jwt_algorithm: str = "HS256"  # ✅ CORRECTO: Para firmar JWTs
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Security - Password Hashing
    password_hash_schemes: List[str] = ["argon2", "bcrypt"]  # ✅ Para passwords
    
    # Email
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "clblommberg@gmail.com"
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "Auth Service"
    mail_tls: bool = True
    mail_ssl: bool = False
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # OAuth2 (opcional)
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Rate Limiting
    rate_limit_per_minute: int = 10
    rate_limit_per_hour: int = 100
    rate_limit_enabled: bool = True
    
    # Environment
    environment: str = "development"
    app_name: str = "FastAPI Auth Service"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )
    
    @property
    def origins_list(self) -> List[str]:
        """Convierte string de orígenes separados por comas en lista"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()