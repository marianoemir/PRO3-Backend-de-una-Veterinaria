from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def crear_motor(url: str) -> AsyncEngine:
    """Crea el motor asincrónico (con echo=True para la evidencia del caso C-07)."""
    return create_async_engine(url, echo=True)


def crear_fabrica(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Crea la fábrica de sesiones (una por petición, sin expire_on_commit)."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request):
    """Toma el async_sessionmaker de app.state, crea una sesión y la cierra al terminar."""
    async with request.app.state.session_local() as session:
        yield session