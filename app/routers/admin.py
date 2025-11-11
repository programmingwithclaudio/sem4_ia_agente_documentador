# app/routers/admin.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from app.models import User, Role, UserSession, get_async_session
from app.auth import admin_required
from app.schemas import UserStatsResponse, PaginatedUsers, UserRead

router = APIRouter()


# ESTADÍSTICAS DEL SISTEMA

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """
    Obtiene estadísticas generales del sistema (solo admin)
    """
    # Total de usuarios
    total_users_result = await session.execute(
        select(func.count(User.id))
    )
    total_users = total_users_result.scalar()
    
    # Usuarios verificados
    verified_users_result = await session.execute(
        select(func.count(User.id)).where(User.is_verified == True)
    )
    verified_users = verified_users_result.scalar()
    
    # Sesiones activas
    active_sessions_result = await session.execute(
        select(func.count(UserSession.id)).where(UserSession.is_active == True)
    )
    active_sessions = active_sessions_result.scalar()
    
    # Usuarios por rol
    roles_result = await session.execute(select(Role))
    roles = roles_result.scalars().all()
    
    users_by_role = {}
    for role in roles:
        count_result = await session.execute(
            select(func.count(User.id))
            .join(User.roles)
            .where(Role.id == role.id)
        )
        users_by_role[role.name] = count_result.scalar()
    
    return UserStatsResponse(
        total_users=total_users,
        verified_users=verified_users,
        active_sessions=active_sessions,
        users_by_role=users_by_role
    )


# ==========================================
# BÚSQUEDA DE USUARIOS
# ==========================================

@router.get("/users/search", response_model=PaginatedUsers)
async def search_users(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required),
    q: str = Query(None, description="Search query"),
    page: int = Query(1, gt=0),
    size: int = Query(10, gt=0, le=100),
    role: str = Query(None, description="Filter by role"),
    is_verified: bool = Query(None, description="Filter by verification status"),
    is_active: bool = Query(None, description="Filter by active status")
):
    """
    Búsqueda avanzada de usuarios (solo admin)
    """
    query = select(User)
    
    # Filtros
    if q:
        query = query.where(
            (User.username.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%")) |
            (User.first_name.ilike(f"%{q}%")) |
            (User.last_name.ilike(f"%{q}%"))
        )
    
    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Paginación
    query = query.offset((page - 1) * size).limit(size)
    result = await session.execute(query)
    users = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return PaginatedUsers(
        items=[
            UserRead(
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
            for user in users
        ],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


# ==========================================
# GESTIÓN DE USUARIOS
# ==========================================

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Activa un usuario (solo admin)"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.locked_until = None
    user.failed_login_attempts = 0
    await session.commit()
    
    return {"message": f"User {user.username} activated successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Desactiva un usuario (solo admin)"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate superuser"
        )
    
    user.is_active = False
    await session.commit()
    
    return {"message": f"User {user.username} deactivated successfully"}


@router.post("/users/{user_id}/verify")
async def verify_user_manually(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Verifica manualmente un usuario (solo admin)"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    await session.commit()
    
    return {"message": f"User {user.username} verified successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Elimina un usuario permanentemente (solo admin)"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete superuser"
        )
    
    await session.delete(user)
    await session.commit()
    
    return {"message": f"User {user.username} deleted successfully"}


@router.post("/users/{user_id}/make-superuser")
async def make_superuser(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Convierte un usuario en superuser (solo admin)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create other superusers"
        )
    
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_superuser = True
    await session.commit()
    
    return {"message": f"User {user.username} is now a superuser"}


# ==========================================
# GESTIÓN DE SESIONES
# ==========================================

@router.get("/sessions/active")
async def get_active_sessions(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required),
    limit: int = 50
):
    """Obtiene las sesiones activas del sistema (solo admin)"""
    result = await session.execute(
        select(UserSession)
        .where(UserSession.is_active == True)
        .order_by(UserSession.last_activity.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "ip_address": s.ip_address,
            "device_type": s.device_type,
            "created_at": s.created_at,
            "last_activity": s.last_activity
        }
        for s in sessions
    ]


@router.delete("/sessions/cleanup")
async def cleanup_expired_sessions(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Limpia sesiones expiradas (solo admin)"""
    now = datetime.utcnow()
    
    result = await session.execute(
        select(UserSession).where(
            and_(
                UserSession.expires_at < now,
                UserSession.is_active == True
            )
        )
    )
    expired_sessions = result.scalars().all()
    
    count = 0
    for sess in expired_sessions:
        sess.is_active = False
        sess.revoked_at = now
        count += 1
    
    await session.commit()
    
    return {"message": f"Cleaned up {count} expired sessions"}