from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

# Estos imports no se usan por su nombre acá: registran los mappers del grafo que este
# endpoint recorre (`Turno.mascota`, `Mascota.duenio`, `TurnoPractica.practica`). Sin ellos, la
# primera consulta falla con "expression 'Mascota'|'Duenio' failed to locate a name"
# (design.md, Decisión 11).
from app.modules.duenios.models import Duenio  # noqa: F401
from app.modules.mascotas.models import Mascota  # noqa: F401
from app.modules.practicas.models import Practica  # noqa: F401
from app.modules.turnos.models import Turno, TurnoPractica
from app.modules.turnos.schemas import (
    MascotaResumenRead,
    TurnoCreate,
    TurnoPracticaRead,
    TurnoRead,
)

CENTAVO = Decimal("0.01")


class PracticaInexistente(Exception):
    """Alguna de las prácticas pedidas no está en el catálogo (RN-23: no se guarda nada)."""


class TurnoConflicto(Exception):
    """La base rechazó el alta del turno (PK compuesta o FK de la mascota)."""


def _mensaje_conflicto(error: IntegrityError) -> str:
    """Traduce el rechazo de PostgreSQL a un mensaje propio, sin exponer SQL ni restricciones."""
    sqlstate = getattr(error.orig, "sqlstate", None)
    if sqlstate == "23505":
        return "una de las prácticas está repetida en el turno"
    if sqlstate == "23503":
        return "la mascota indicada no existe"
    return "la base rechazó el registro del turno"


async def _leer_practicas(
    session: AsyncSession, ids_pedidos: set[int]
) -> dict[int, Practica]:
    """Lee del catálogo las prácticas pedidas: acá se obtienen los precios que hay que copiar."""
    resultado = await session.execute(
        select(Practica).where(Practica.id.in_(ids_pedidos))
    )
    return {practica.id: practica for practica in resultado.scalars().all()}


def _fecha_en_utc(fecha: datetime) -> datetime:
    """Normaliza a UTC; una fecha sin offset se interpreta como UTC (design.md, Decisión 9)."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


async def _leer_turno(session: AsyncSession, turno_id: int) -> TurnoRead:
    """Relee el turno creado con carga anticipada declarada: 2 consultas fijas, sin carga perezosa."""
    resultado = await session.execute(
        select(Turno)
        .where(Turno.id == turno_id)
        .options(
            joinedload(Turno.mascota),
            selectinload(Turno.practicas).joinedload(TurnoPractica.practica),
        )
    )
    turno = resultado.scalars().one()
    return TurnoRead(
        id=turno.id,
        fecha=turno.fecha.astimezone(timezone.utc),
        motivo=turno.motivo,
        total=turno.total,
        mascota=MascotaResumenRead(
            id=turno.mascota.id,
            nombre=turno.mascota.nombre,
            especie=turno.mascota.especie,
        ),
        practicas=[
            TurnoPracticaRead(
                practica_id=fila.practica_id,
                nombre=fila.practica.nombre,
                precio_unitario=fila.precio_unitario,
            )
            for fila in sorted(turno.practicas, key=lambda fila: fila.practica_id)
        ],
    )


async def crear_turno(session: AsyncSession, datos: TurnoCreate) -> TurnoRead:
    """Reserva un turno con sus prácticas en una sola transacción: o queda todo, o no queda nada."""
    ids_pedidos = {practica.practica_id for practica in datos.practicas}
    catalogo = await _leer_practicas(session, ids_pedidos)

    faltantes = sorted(ids_pedidos - catalogo.keys())
    if faltantes:
        # La lectura ya abrió la transacción: hay que cerrarla antes de responder 409.
        await session.rollback()
        detalle = ", ".join(str(practica_id) for practica_id in faltantes)
        raise PracticaInexistente(
            f"la(s) práctica(s) {detalle} no existe(n) en el catálogo"
        )

    # Una fila por práctica PEDIDA, no por fila encontrada: así una práctica repetida
    # llega con dos filas y la rechaza la PK compuesta (RN-07).
    practicas = [catalogo[pedida.practica_id] for pedida in datos.practicas]
    total = sum(
        (practica.precio for practica in practicas), Decimal("0.00")
    ).quantize(CENTAVO)

    turno = Turno(
        mascota_id=datos.mascota_id,
        fecha=_fecha_en_utc(datos.fecha),
        motivo=datos.motivo,
        total=total,
    )
    turno.practicas = [
        TurnoPractica(practica_id=practica.id, precio_unitario=practica.precio)
        for practica in practicas
    ]
    session.add(turno)

    try:
        await session.flush()
        # Relectura dentro de la misma transacción: lo que se devuelve es lo que se va a confirmar.
        respuesta = await _leer_turno(session, turno.id)
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise TurnoConflicto(_mensaje_conflicto(error)) from error

    return respuesta
