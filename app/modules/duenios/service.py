from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

import app.modules.duenios.models  # noqa: F401
import app.modules.mascotas.models  # noqa: F401
import app.modules.turnos.models  # noqa: F401

from app.modules.duenios.models import Duenio, FichaDuenio
from app.modules.duenios.schemas import (
    DuenioCreate,
    DuenioRead,
    DuenioUpdate,
    FichaCreate,
)
from app.modules.mascotas.models import Mascota


async def crear_duenio(session: AsyncSession, dto: DuenioCreate) -> DuenioRead:
    """Alta de dueño: escribe y deja que el UNIQUE de email decida (DD-03)."""
    duenio = Duenio(nombre=dto.nombre, email=dto.email)
    session.add(duenio)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un dueño con ese email")
    # Sin refresh ni carga perezosa: un dueño recién creado no tiene ficha (decisión 3).
    return DuenioRead(id=duenio.id, nombre=duenio.nombre, email=duenio.email, ficha=None)


async def obtener_duenio(session: AsyncSession, duenio_id: int) -> Duenio | None:
    """Detalle con la ficha precargada en una sola consulta (RN-14, RN-15)."""
    resultado = await session.execute(
        select(Duenio).options(joinedload(Duenio.ficha)).where(Duenio.id == duenio_id)
    )
    return resultado.scalars().first()


async def actualizar_duenio(
    session: AsyncSession, duenio_id: int, dto: DuenioUpdate
) -> Duenio:
    """PATCH parcial: aplica solo los campos enviados (RN-11, DD-08)."""
    duenio = await obtener_duenio(session, duenio_id)
    if duenio is None:
        raise HTTPException(status_code=404, detail="No existe un dueño con ese id")
    for campo, valor in dto.model_dump(exclude_unset=True).items():
        setattr(duenio, campo, valor)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo actualizar: email ya registrado o dato inválido",
        )
    return duenio


async def borrar_duenio(session: AsyncSession, duenio_id: int) -> None:
    """Baja: decide la base (RESTRICT / NO ACTION), sin borrar hijas (RN-08, DD-13)."""
    try:
        resultado = await session.execute(
            delete(Duenio)
            .where(Duenio.id == duenio_id)
            .execution_options(synchronize_session=False)
        )
        if resultado.rowcount == 0:
            raise HTTPException(status_code=404, detail="No existe un dueño con ese id")
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede borrar el dueño: tiene mascotas o ficha asociada",
        )


async def crear_ficha(
    session: AsyncSession, duenio_id: int, dto: FichaCreate
) -> FichaDuenio:
    """Alta de ficha: solo se consulta el id del dueño; el UNIQUE decide el 409 (RN-03)."""
    resultado = await session.execute(select(Duenio.id).where(Duenio.id == duenio_id))
    if resultado.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="No existe un dueño con ese id")
    ficha = FichaDuenio(
        duenio_id=duenio_id, telefono=dto.telefono, direccion=dto.direccion
    )
    session.add(ficha)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="El dueño ya tiene una ficha registrada"
        )
    return ficha


async def listar_mascotas_de_duenio(
    session: AsyncSession, duenio_id: int
) -> list[Mascota]:
    """Mascotas del dueño: dos consultas fijas y lista simple ordenada por id (DD-10, DD-15)."""
    resultado = await session.execute(select(Duenio.id).where(Duenio.id == duenio_id))
    if resultado.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="No existe un dueño con ese id")
    resultado = await session.execute(
        select(Mascota).where(Mascota.duenio_id == duenio_id).order_by(Mascota.id)
    )
    return list(resultado.scalars().all())




