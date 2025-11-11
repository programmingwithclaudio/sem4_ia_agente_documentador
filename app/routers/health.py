from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models import get_async_session
from app.schemas import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Verifica el estado de salud del servicio
    """
    # Verificar base de datos
    try:
        await session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Verificar Redis (si está configurado)
    redis_status = "not configured"
    # Aquí puedes agregar verificación de Redis si lo usas
    
    return HealthCheck(
        status="healthy" if db_status == "healthy" else "unhealthy",
        version="2.0.0",
        database=db_status,
        redis=redis_status
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"ping": "pong"}