from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.mascotas import service
from app.modules.mascotas.schemas import (
    MascotaCreate,
    MascotaRead,
    PaginaMascotasRead,
)

router = APIRouter(prefix="/mascotas", tags=["mascotas"])


@router.post("/", response_model=MascotaRead, status_code=201)
async def crear_mascota_endpoint(
    dto: MascotaCreate, session: AsyncSession = Depends(get_session)
):
    return await service.crear_mascota(session, dto)


@router.get("/", response_model=PaginaMascotasRead)
async def listar_mascotas_endpoint(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    return await service.listar_mascotas(session, page, size)


@router.get("/{mascota_id}", response_model=MascotaRead)
async def obtener_mascota_endpoint(
    mascota_id: int, session: AsyncSession = Depends(get_session)
):
    mascota = await service.obtener_mascota(session, mascota_id)
    if mascota is None:
        raise HTTPException(status_code=404, detail="No existe una mascota con ese id")
    return mascota
