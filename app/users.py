# app/users.py
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.models import User, get_db
from app.auth import admin_required
from pydantic import BaseModel

users_router = APIRouter()

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    roles: List[str]

    class Config:
        from_attributes = True

class PaginatedUsers(BaseModel):
    items: List[UserResponse]
    total: int
    pages: int
    current_page: int

@users_router.get("/users", response_model=PaginatedUsers)
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    page: int = Query(1, gt=0),
    size: int = Query(10, gt=0),
    username: Optional[str] = None
):
    query = db.query(User)
    if username:
        query = query.filter(User.username.contains(username))

    total = query.count()
    pages = (total + size - 1) // size

    users = query.offset((page - 1) * size).limit(size).all()

    return {
        "items": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": [role.name for role in user.roles]
            }
            for user in users
        ],
        "total": total,
        "pages": pages,
        "current_page": page
    }

@users_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [role.name for role in user.roles]
    }