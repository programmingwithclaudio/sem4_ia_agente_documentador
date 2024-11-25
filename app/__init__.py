# app/__init__.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_lifespan_manager import LifespanManager, State
from app.auth import auth_router
from app.users import users_router
from app.models import Base, engine, SessionLocal, Role
from typing import AsyncIterator
# Crear el LifespanManager
manager = LifespanManager()

@manager.add
async def init_db(app: FastAPI) -> AsyncIterator[State]:
    db = SessionLocal()
    try:
        roles = ['ROLE_USER', 'ROLE_MODERATOR', 'ROLE_ADMIN']
        for role_name in roles:
            if not db.query(Role).filter_by(name=role_name).first():
                db.add(Role(name=role_name))
        db.commit()  # Confirmamos los cambios aquí
    finally:
        db.close()

    yield {}

# Crear la aplicación
def create_app():
    app = FastAPI(title="FastAPI Login Example", lifespan=manager)
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Incluir routers
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(users_router, prefix="/api", tags=["users"])
    
    # Crear tablas en la base de datos
    Base.metadata.create_all(bind=engine)
    
    return app
