from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live():
    return {"estado": "vivo"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        return {"estado": "listo", "base": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"estado": "no_disponible", "base": "error"},
        )