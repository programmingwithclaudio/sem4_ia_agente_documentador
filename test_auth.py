"""
Tests para el sistema de autenticación
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register_user():
    """Test de registro de usuario"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "Test123!",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_login():
    """Test de login"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Primero registrar
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "Login123!"
            }
        )
        
        # Luego hacer login
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "login@example.com",
                "password": "Login123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_current_user():
    """Test de obtener usuario actual"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Registrar y login
        await client.post(
            "/api/auth/register",
            json={
                "email": "current@example.com",
                "username": "currentuser",
                "password": "Current123!"
            }
        )
        
        login_response = await client.post(
            "/api/auth/login",
            data={
                "username": "current@example.com",
                "password": "Current123!"
            }
        )
        token = login_response.json()["access_token"]
        
        # Obtener perfil
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "current@example.com"


@pytest.mark.asyncio
async def test_invalid_credentials():
    """Test de credenciales inválidas"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_weak_password():
    """Test de contraseña débil"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "weak"  # Muy corta
            }
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_duplicate_email():
    """Test de email duplicado"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Primer registro
        await client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "Password123!"
            }
        )
        
        # Segundo registro con mismo email
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "Password123!"
            }
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_health_check():
    """Test de health check"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}