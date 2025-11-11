# app/routers/users.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import User, UserSession, get_async_session
from app.auth import current_active_user
from app.schemas import (
    UserRead, 
    PaginatedUsers, 
    ChangePasswordRequest,
    UserSessionRead
)
from passlib.context import CryptContext
from datetime import datetime
from typing import List

router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ENDPOINTS DE USUARIO AUTENTICADO
@router.get("/users/me/profile", response_model=UserRead)
async def get_current_user_profile(
    user: User = Depends(current_active_user)
):
    """Obtiene el perfil del usuario actual"""
    return UserRead(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        bio=user.bio,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login,
        roles=[role.name for role in user.roles]
    )


@router.get("/users/me/sessions", response_model=List[UserSessionRead])
async def get_my_sessions(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Obtiene las sesiones activas del usuario actual"""
    result = await session.execute(
        select(UserSession)
        .where(UserSession.user_id == user.id)
        .where(UserSession.is_active == True)
        .order_by(UserSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return sessions


@router.delete("/users/me/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Revoca una sesión específica del usuario"""
    result = await session.execute(
        select(UserSession)
        .where(UserSession.id == session_id)
        .where(UserSession.user_id == user.id)
    )
    user_session = result.scalar_one_or_none()
    
    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    user_session.is_active = False
    user_session.revoked_at = datetime.utcnow()
    await session.commit()
    
    return {"message": "Session revoked successfully"}


@router.post("/users/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cambia la contraseña del usuario actual"""
    # Verificar contraseña actual
    if not pwd_context.verify(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash nueva contraseña
    user.hashed_password = pwd_context.hash(request.new_password)
    await session.commit()
    
    return {"message": "Password changed successfully"}