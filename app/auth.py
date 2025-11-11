# app\auth.py
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from app.models import User
from app.users_manager import get_user_manager
from app.config import settings


# Bearer Transport (headers + cookies)
bearer_transport = BearerTransport(tokenUrl="/api/auth/login")



# JWT Strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=settings.access_token_expire_minutes * 60,
        algorithm=settings.jwt_algorithm,
    )


# Authentication Backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)



# FastAPI Users Instance
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)



# Dependencies de autenticación
current_active_user = fastapi_users.current_user(active=True)
current_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


# Dependency para verificar roles
from fastapi import Depends, HTTPException, status


async def require_role(required_role: str):
    """
    Dependency factory para verificar roles específicos
    Uso: current_user = Depends(require_role("ROLE_ADMIN"))
    """
    async def _verify_role(user: User = Depends(current_active_user)):
        user_roles = [role.name for role in user.roles]
        if required_role not in user_roles and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required"
            )
        return user
    return _verify_role


async def require_any_role(*required_roles: str):
    """
    Dependency factory para verificar que tenga al menos uno de los roles
    Uso: current_user = Depends(require_any_role("ROLE_ADMIN", "ROLE_MODERATOR"))
    """
    async def _verify_roles(user: User = Depends(current_active_user)):
        user_roles = [role.name for role in user.roles]
        if not any(role in user_roles for role in required_roles) and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(required_roles)}"
            )
        return user
    return _verify_roles


async def admin_required(user: User = Depends(current_active_user)):
    """Dependency para verificar que sea admin o superuser"""
    user_roles = [role.name for role in user.roles]
    if "ROLE_ADMIN" not in user_roles and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user