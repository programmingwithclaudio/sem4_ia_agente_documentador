#  app\models.py
from datetime import datetime
from typing import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.config import settings


# Base declarativa
class Base(DeclarativeBase):
    pass


# Tabla de asociación muchos a muchos (users <-> roles)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)


class Role(Base):
    """Modelo de roles"""
    __tablename__ = 'roles'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    
    def __repr__(self):
        return f"<Role {self.name}>"

class User(SQLAlchemyBaseUserTable[int], Base):
    """
    Modelo de usuario extendido de FastAPI Users
    Incluye campos adicionales personalizados
    """
    __tablename__ = 'users'

    # Campos heredados de FastAPIUsers:
    # - id (pk)
    # - email (unique, indexed)
    # - hashed_password
    # - is_active (bool)
    # - is_superuser (bool)
    # - is_verified (bool)
       
    # IMPORTANTE: Definir explícitamente el id como primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Campos personalizados adicionales
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Avatar/Profile
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Seguridad adicional
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # OAuth providers
    oauth_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    oauth_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Relaciones
    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )
    
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.username} - {self.email}>"


class UserSession(Base):
    """
    Auditoría de sesiones de usuario
    Permite rastrear logins, dispositivos, IPs, etc.
    """
    __tablename__ = 'user_sessions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Token info
    access_token_jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token_jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    
    # Device/Client info
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=True)  # mobile, desktop, tablet
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relación
    user: Mapped[User] = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session {self.id} - User {self.user_id}>"


# =============================================
# Database Engine y SessionMaker
# =============================================

# Async engine para FastAPI Users
engine = create_async_engine(
    settings.database_url,
    echo=False,  # True para debug SQL
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_db_and_tables():
    """Crea las tablas en la base de datos"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obtener sesión async de DB"""
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Dependency para FastAPI Users"""
    yield SQLAlchemyUserDatabase(session, User)