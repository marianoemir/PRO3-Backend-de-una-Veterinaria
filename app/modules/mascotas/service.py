import math

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

import app.modules.duenios.models  # noqa: F401
import app.modules.mascotas.models  # noqa: F401
import app.modules.turnos.models  # noqa: F401

from app.modules.mascotas.models import Mascota
from app.modules.mascotas.schemas import MascotaCreate, MascotaRead, PaginaMascotasRead


async def crear_mascota(session: AsyncSession, dto: MascotaCreate) -> Mascota:
    """Alta de mascota: escribe y deja que la FK valide el dueño (DD-03)."""
    mascota = Mascota(nombre=dto.nombre, especie=dto.especie, duenio_id=dto.duenio_id)
    session.add(mascota)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="No existe un dueño con ese id")
    # Re-lectura con carga anticipada: el objeto recién insertado no trae el dueño (decisión 3).
    resultado = await session.execute(
        select(Mascota)
        .options(joinedload(Mascota.duenio))
        .where(Mascota.id == mascota.id)
        .execution_options(populate_existing=True)
    )
    return resultado.scalars().one()


async def obtener_mascota(session: AsyncSession, mascota_id: int) -> Mascota | None:
    """Detalle con el dueño precargado en una sola consulta (RN-14, RN-15)."""
    resultado = await session.execute(
        select(Mascota)
        .options(joinedload(Mascota.duenio))
        .where(Mascota.id == mascota_id)
    )
    return resultado.scalars().first()


async def listar_mascotas(
    session: AsyncSession, page: int, size: int
) -> PaginaMascotasRead:
    """Listado paginado: `count(*)` + una página con el dueño precargado (RN-13, RN-15)."""
    total = (await session.execute(select(func.count()).select_from(Mascota))).scalar_one()
    pages = math.ceil(total / size) if total else 0
    if page > 1 and page > pages:
        raise HTTPException(status_code=422, detail="La página solicitada no existe")
    resultado = await session.execute(
        select(Mascota)
        .options(joinedload(Mascota.duenio))
        .order_by(Mascota.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [
        MascotaRead.model_validate(mascota) for mascota in resultado.scalars().all()
    ]
    return PaginaMascotasRead(
        items=items, total=total, page=page, size=size, pages=pages
    )
