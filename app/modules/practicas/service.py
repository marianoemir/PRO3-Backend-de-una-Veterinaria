from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

import app.modules.duenios.models  # noqa: F401
import app.modules.mascotas.models  # noqa: F401
import app.modules.turnos.models  # noqa: F401

from app.modules.practicas.models import Practica
from app.modules.practicas.schemas import PracticaCreate


async def crear_practica(session: AsyncSession, dto: PracticaCreate) -> Practica:
    practica = Practica(nombre=dto.nombre, precio=dto.precio)
    session.add(practica)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una práctica con ese nombre")
    await session.refresh(practica)
    return practica


async def listar_practicas(session: AsyncSession) -> list[Practica]:
    result = await session.execute(select(Practica).order_by(Practica.id))
    return list(result.scalars().all())
