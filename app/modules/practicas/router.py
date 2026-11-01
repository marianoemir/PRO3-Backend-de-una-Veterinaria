from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.practicas.schemas import PracticaCreate, PracticaRead
from app.modules.practicas import service

router = APIRouter(prefix="/practicas", tags=["practicas"])


@router.post("/", response_model=PracticaRead, status_code=201)
async def crear_practica_endpoint(
    dto: PracticaCreate, session: AsyncSession = Depends(get_session)
):
    return await service.crear_practica(session, dto)


@router.get("/", response_model=list[PracticaRead])
async def listar_practicas_endpoint(session: AsyncSession = Depends(get_session)):
    return await service.listar_practicas(session)
