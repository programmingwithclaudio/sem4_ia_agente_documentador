# app\users_manager.py
from datetime import datetime
from typing import Optional, Union
from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, IntegerIDMixin, exceptions, schemas
from fastapi_users.password import PasswordHelperProtocol
from passlib.context import CryptContext

from app.models import User, get_user_db
from app.config import settings
from app.email import send_verification_email, send_password_reset_email


class Argon2PasswordHelper(PasswordHelperProtocol):
    """
    Password helper personalizado usando Argon2 en lugar de bcrypt
    """
    def __init__(self):
        self.context = CryptContext(
            schemes=["argon2"],  # Solo argon2
            deprecated="auto",
        )
    
    def hash(self, password: str) -> str:
        """Hash password con argon2"""
        return self.context.hash(password)
    
    def verify_and_update(
        self, plain_password: str, hashed_password: str
    ) -> tuple[bool, str | None]:
        """Verifica password y retorna si necesita rehash"""
        valid = self.context.verify(plain_password, hashed_password)
        updated_password = None
        
        if valid and self.context.needs_update(hashed_password):
            updated_password = self.hash(plain_password)
        
        return valid, updated_password


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    Manager personalizado para FastAPI Users
    Maneja eventos de registro, verificación, cambio de contraseña, etc.
    """
    
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key
    
    def __init__(self, user_db):
        """Inicializar con password helper personalizado"""
        super().__init__(user_db)
        # CRÍTICO: Reemplazar el password_helper por defecto
        self.password_helper = Argon2PasswordHelper()
    
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Se ejecuta después de registrar un usuario"""
        print(f"✅ Usuario registrado: {user.email}")
        
        if settings.mail_username:
            try:
                token = await self.request_verify(user, request)
                await send_verification_email(user.email, token)
            except Exception as e:
                print(f"❌ Error enviando email de verificación: {e}")
    
    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Se ejecuta cuando se solicita reset de contraseña"""
        print(f"🔑 Reset de contraseña solicitado para: {user.email}")
        
        if settings.mail_username:
            try:
                await send_password_reset_email(user.email, token)
            except Exception as e:
                print(f"❌ Error enviando email de reset: {e}")
    
    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Se ejecuta cuando se solicita verificación de email"""
        print(f"📧 Verificación solicitada para: {user.email}")
    
    async def on_after_verify(
        self, user: User, request: Optional[Request] = None
    ):
        """Se ejecuta después de verificar email"""
        print(f"✅ Email verificado: {user.email}")
    
    async def on_after_update(
        self,
        user: User,
        update_dict: dict,
        request: Optional[Request] = None,
    ):
        """Se ejecuta después de actualizar usuario"""
        print(f"📝 Usuario actualizado: {user.email}")
    
    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,  # ← NUEVO parámetro
    ):
        """Se ejecuta después del login"""
        print(f"🔓 Login exitoso: {user.email}")
        
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
    
    async def on_after_reset_password(
        self, user: User, request: Optional[Request] = None
    ):
        """Se ejecuta después de resetear contraseña"""
        print(f"🔒 Contraseña reseteada para: {user.email}")
    
    async def validate_password(
        self,
        password: str,
        user: Union[User, schemas.UC],
    ) -> None:
        """Valida requisitos de contraseña"""
        if len(password) < 8:
            raise exceptions.InvalidPasswordException(
                reason="Password should be at least 8 characters"
            )
        
        if not any(char.isdigit() for char in password):
            raise exceptions.InvalidPasswordException(
                reason="Password should contain at least one digit"
            )
        
        if not any(char.isupper() for char in password):
            raise exceptions.InvalidPasswordException(
                reason="Password should contain at least one uppercase letter"
            )
        
        if not any(char.islower() for char in password):
            raise exceptions.InvalidPasswordException(
                reason="Password should contain at least one lowercase letter"
            )


async def get_user_manager(user_db=Depends(get_user_db)):
    """Dependency para obtener el UserManager"""
    yield UserManager(user_db)