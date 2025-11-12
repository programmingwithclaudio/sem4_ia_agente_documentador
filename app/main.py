#!/usr/bin/env python3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import create_db_and_tables, get_async_session, Role
from app.auth import fastapi_users, auth_backend
from app.schemas import UserRead, UserCreate
from app.routers import users_router, roles_router, admin_router, health_router
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Lifespan - Inicialización y cierre
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de vida de la aplicación
    Se ejecuta al iniciar y al cerrar
    """
    # STARTUP
    logger.info("🚀 Iniciando Auth Service...")
    
    # Crear tablas
    await create_db_and_tables()
    logger.info("✅ Tablas de BD creadas/verificadas")
    
    # Crear roles por defecto
    async for session in get_async_session():
        await initialize_roles(session)
        break
    
    logger.info("✅ Roles inicializados")
    logger.info("🎉 Auth Service listo!")
    
    yield
    
    # SHUTDOWN
    logger.info("👋 Cerrando Auth Service...")


async def initialize_roles(session: AsyncSession):
    """Inicializa roles por defecto en la BD"""
    from sqlalchemy import select
    
    default_roles = [
        {"name": "ROLE_USER", "description": "Usuario estándar"},
        {"name": "ROLE_MODERATOR", "description": "Moderador con permisos intermedios"},
        {"name": "ROLE_ADMIN", "description": "Administrador con todos los permisos"},
    ]
    
    for role_data in default_roles:
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            new_role = Role(**role_data)
            session.add(new_role)
    
    await session.commit()


# FastAPI
app = FastAPI(
    title="🔐 Auth Microservice",
    description="Sistema de autenticación centralizado con FastAPI Users",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Registrar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers 
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de excepciones"""
    logger.error(f"❌ Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Incluir routers de FastAPI Users
# Router de autenticación (login, logout)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth",
    tags=["auth"]
)

# Router de registro
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"]
)

# Router de verificación de email
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/api/auth",
    tags=["auth"]
)

# Router de reset de contraseña
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/api/auth",
    tags=["auth"]
)

# Router de gestión de usuarios (requiere auth)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/api/users",
    tags=["users"]
)


# Incluir routers personalizados
# Router de usuarios (endpoints para usuarios autenticados)
app.include_router(
    users_router, 
    prefix="/api", 
    tags=["users-extended"]
)

# Router de administración (endpoints solo admin)
app.include_router(
    admin_router, 
    prefix="/api/admin", 
    tags=["admin"]
)

# Router de roles
app.include_router(
    roles_router, 
    prefix="/api/roles", 
    tags=["roles"]
)

# Router de health
app.include_router(
    health_router, 
    prefix="/api/health", 
    tags=["health"]
)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz"""
    return {
        "service": "Auth Microservice",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }