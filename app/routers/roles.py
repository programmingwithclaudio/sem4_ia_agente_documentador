from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.models import Role, User, get_async_session
from app.auth import admin_required
from app.schemas import RoleRead, RoleCreate, AssignRoleRequest

router = APIRouter()

@router.get("/", response_model=List[RoleRead])
async def get_all_roles(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Obtiene todos los roles disponibles (solo admin)"""
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    return roles


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Crea un nuevo rol (solo admin)"""
    # Verificar si el rol ya existe
    result = await session.execute(
        select(Role).where(Role.name == role_data.name)
    )
    existing_role = result.scalar_one_or_none()
    
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {role_data.name} already exists"
        )
    
    new_role = Role(
        name=role_data.name,
        description=role_data.description
    )
    session.add(new_role)
    await session.commit()
    await session.refresh(new_role)
    
    return new_role


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Elimina un rol (solo admin)"""
    result = await session.execute(
        select(Role).where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # No permitir eliminar roles por defecto
    if role.name in ["ROLE_USER", "ROLE_ADMIN", "ROLE_MODERATOR"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default roles"
        )
    
    await session.delete(role)
    await session.commit()
    
    return {"message": f"Role {role.name} deleted successfully"}


@router.post("/assign")
async def assign_role_to_user(
    request: AssignRoleRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Asigna un rol a un usuario (solo admin)"""
    # Obtener usuario
    user_result = await session.execute(
        select(User).where(User.id == request.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Obtener rol
    role_result = await session.execute(
        select(Role).where(Role.name == request.role_name)
    )
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Verificar si ya tiene el rol
    if role in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already has role {request.role_name}"
        )
    
    # Asignar rol
    user.roles.append(role)
    await session.commit()
    
    return {
        "message": f"Role {request.role_name} assigned to user {user.username}",
        "user_id": user.id,
        "username": user.username,
        "roles": [r.name for r in user.roles]
    }


@router.delete("/revoke")
async def revoke_role_from_user(
    request: AssignRoleRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(admin_required)
):
    """Revoca un rol de un usuario (solo admin)"""
    # Obtener usuario
    user_result = await session.execute(
        select(User).where(User.id == request.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Obtener rol
    role_result = await session.execute(
        select(Role).where(Role.name == request.role_name)
    )
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Verificar si tiene el rol
    if role not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User doesn't have role {request.role_name}"
        )
    
    # Revocar rol
    user.roles.remove(role)
    await session.commit()
    
    return {
        "message": f"Role {request.role_name} revoked from user {user.username}",
        "user_id": user.id,
        "username": user.username,
        "roles": [r.name for r in user.roles]
    }