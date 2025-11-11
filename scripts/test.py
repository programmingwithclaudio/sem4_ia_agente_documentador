from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import os

# Cargar variables de entorno
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mermaiddev")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

print(f"Inicio de conexión: {datetime.now()} ✅")

# ==========================================================
# LIMPIAR TABLA (FULL RELOAD) O CONSULTA SIMPLE
# ==========================================================

async def main():
    async with engine.begin() as conn:
        # ejemplo: limpiar tabla (TRUNCATE)
        # await conn.execute(text("TRUNCATE TABLE TestInterviews RESTART IDENTITY CASCADE;"))

        # ejemplo: solo probar SELECT
        result = await conn.execute(text("SELECT * FROM test_model LIMIT 2;"))
        rows = result.fetchall()
        for row in rows:
            print(row)

    await engine.dispose()

asyncio.run(main())
