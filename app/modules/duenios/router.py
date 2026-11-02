from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.duenios import service
from app.modules.duenios.schemas import (
    DuenioCreate,
    DuenioRead,
    DuenioUpdate,
    FichaCreate,
    FichaRead,
    MascotaResumenRead,
)

router = APIRouter(prefix="/duenios", tags=["duenios"])


@router.post("/", response_model=DuenioRead, status_code=201)
async def crear_duenio_endpoint(
    dto: DuenioCreate, session: AsyncSession = Depends(get_session)
):
    return await service.crear_duenio(session, dto)


@router.get("/{duenio_id}", response_model=DuenioRead)
async def obtener_duenio_endpoint(
    duenio_id: int, session: AsyncSession = Depends(get_session)
):
    duenio = await service.obtener_duenio(session, duenio_id)
    if duenio is None:
        raise HTTPException(status_code=404, detail="No existe un dueño con ese id")
    return duenio


@router.patch("/{duenio_id}", response_model=DuenioRead)
async def actualizar_duenio_endpoint(
    duenio_id: int, dto: DuenioUpdate, session: AsyncSession = Depends(get_session)
):
    return await service.actualizar_duenio(session, duenio_id, dto)


@router.delete("/{duenio_id}", status_code=204)
async def borrar_duenio_endpoint(
    duenio_id: int, session: AsyncSession = Depends(get_session)
):
    await service.borrar_duenio(session, duenio_id)


@router.post("/{duenio_id}/ficha", response_model=FichaRead, status_code=201)
async def crear_ficha_endpoint(
    duenio_id: int, dto: FichaCreate, session: AsyncSession = Depends(get_session)
):
    return await service.crear_ficha(session, duenio_id, dto)


@router.get("/{duenio_id}/mascotas", response_model=list[MascotaResumenRead])
async def listar_mascotas_de_duenio_endpoint(
    duenio_id: int, session: AsyncSession = Depends(get_session)
):
    return await service.listar_mascotas_de_duenio(session, duenio_id)

