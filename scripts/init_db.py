"""
Script para inicializar la base de datos con roles y superusuario
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.context import CryptContext

from app.config import settings
from app.models import Base, User, Role

# Usar Argon2 en lugar de bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def create_tables(engine):
    """Crear todas las tablas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas creadas")


async def create_roles(session: AsyncSession):
    """Crear roles por defecto"""
    default_roles = [
        {"name": "ROLE_USER", "description": "Usuario regular"},
        {"name": "ROLE_MODERATOR", "description": "Moderador"},
        {"name": "ROLE_ADMIN", "description": "Administrador"},
    ]
    
    for role_data in default_roles:
        # Verificar si el rol ya existe
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            role = Role(**role_data)
            session.add(role)
            print(f"✅ Rol creado: {role_data['name']}")
        else:
            print(f"⏭️  Rol ya existe: {role_data['name']}")
    
    await session.commit()


async def create_superuser(session: AsyncSession):
    """Crear superusuario por defecto"""
    email = "admin@example.com"
    password = "Admin123!"
    
    # Verificar si ya existe
    result = await session.execute(
        select(User).where(User.email == email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        print(f"⏭️  Superusuario ya existe: {email}")
        return
    
    # Hashear password con Argon2
    hashed_password = pwd_context.hash(password)
    
    # Crear usuario
    user = User(
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
        is_superuser=True,
        username="admin",
        first_name="Super",
        last_name="Admin"
    )
    
    # Asignar rol ADMIN
    result = await session.execute(
        select(Role).where(Role.name == "ROLE_ADMIN")
    )
    admin_role = result.scalar_one_or_none()
    
    if admin_role:
        user.roles.append(admin_role)
    
    session.add(user)
    await session.commit()
    
    print(f"✅ Superusuario creado:")
    print(f"   📧 Email: {email}")
    print(f"   🔑 Password: {password}")
    print(f"   ⚠️  CAMBIA LA CONTRASEÑA EN PRODUCCIÓN!")


async def main():
    """Función principal"""
    print("🚀 Inicializando base de datos...\n")
    
    # Crear engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        future=True
    )
    
    # Crear tablas
    await create_tables(engine)
    print()
    
    # Crear session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Crear roles
        await create_roles(session)
        print()
        
        # Crear superusuario
        await create_superuser(session)
    
    print("\n✨ ¡Inicialización completada!")
    print("🚀 Puedes iniciar la API con: python run.py")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())