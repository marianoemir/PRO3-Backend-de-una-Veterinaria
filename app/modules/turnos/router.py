from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.turnos import service
from app.modules.turnos.schemas import TurnoCreate, TurnoRead

router = APIRouter(prefix="/turnos", tags=["turnos"])


@router.post("/", response_model=TurnoRead, status_code=201)
async def crear_turno(
    datos: TurnoCreate,
    session: AsyncSession = Depends(get_session),
) -> TurnoRead:
    """Reserva un turno con sus prácticas (201, 409 o 422)."""
    try:
        return await service.crear_turno(session, datos)
    except service.PracticaInexistente as error:
        raise HTTPException(
            status_code=409,
            detail=f"no se pudo registrar el turno: {error}",
        ) from error
    except service.TurnoConflicto as error:
        raise HTTPException(
            status_code=409,
            detail=f"no se pudo registrar el turno: {error}",
        ) from error
