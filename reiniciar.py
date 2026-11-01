"""reiniciar.py — reinicia la base de la veterinaria y carga el seed mínimo.

Qué hace
--------
1. Borra las tablas declaradas por los modelos (``SQLModel.metadata.drop_all``).
2. Las vuelve a crear con su esquema completo (``SQLModel.metadata.create_all``).
3. Carga el seed mínimo reproducible (2 dueños, 1 ficha, 3 mascotas, 4 prácticas,
   1 turno con 2 prácticas) con ids explícitos.
4. Resincroniza las secuencias para que el próximo turno reciba ``id = 2``.

Las cuatro etapas corren en una única transacción: si algo falla, PostgreSQL
revierte también el DDL y la base queda exactamente como estaba.

Cómo se ejecuta
---------------
    python reiniciar.py

La base destino es la de ``DATABASE_URL`` en el ``.env`` del proyecto (la misma
que usa la API) y se imprime en pantalla, enmascarada, antes de borrar nada.

ADVERTENCIA: el script BORRA TODO el contenido de esa base.

Códigos de salida
-----------------
- ``0``: reinicio completo.
- ``1``: ``DATABASE_URL`` ausente (lo emite ``app/core/config.py``, no se duplica).
- ``2``: error de conexión o de ejecución; la base no se modifica.
"""

import asyncio
import sys
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.database import crear_fabrica, crear_motor
from app.modules.duenios.models import Duenio, FichaDuenio  # noqa: F401
from app.modules.mascotas.models import Mascota  # noqa: F401
from app.modules.practicas.models import Practica  # noqa: F401
from app.modules.turnos.models import Turno, TurnoPractica  # noqa: F401

# Tablas que el metadata DEBE conocer: si falta una, ``create_all`` crearía un
# esquema incompleto y el primer INSERT fallaría por FK inexistente.
TABLAS_ESPERADAS: frozenset[str] = frozenset(
    {"duenio", "ficha_duenio", "mascota", "practica", "turno", "turno_practica"}
)

# Orden de impresión del resumen (de padres a hijos) y orden del grafo de FK.
TABLAS_ORDENADAS: tuple[str, ...] = (
    "duenio",
    "ficha_duenio",
    "mascota",
    "practica",
    "turno",
    "turno_practica",
)

# Tablas con ``id`` autoincremental a resincronizar. ``turno_practica`` no tiene
# secuencia: su PK es compuesta.
TABLAS_CON_SECUENCIA: tuple[str, ...] = (
    "duenio",
    "ficha_duenio",
    "mascota",
    "practica",
    "turno",
)

# --- Seed -------------------------------------------------------------------
# Fecha fija (no ``now()``): cada ejecución deja exactamente el mismo estado.
# Equivale a 2026-11-12T10:30:00-03:00, el instante del ejemplo de la consigna.
FECHA_TURNO_SEED: datetime = datetime(2026, 11, 12, 13, 30, tzinfo=timezone.utc)

DUENIOS_SEED: tuple[Duenio, ...] = (
    Duenio(id=1, nombre="Ana Gómez", email="ana.gomez@ejemplo.com"),
    Duenio(id=2, nombre="Bruno Díaz", email="bruno.diaz@ejemplo.com"),
)

FICHAS_SEED: tuple[FichaDuenio, ...] = (
    FichaDuenio(
        id=1,
        duenio_id=1,
        telefono="1145550001",
        direccion="Av. Ficticia 100",
    ),
)

MASCOTAS_SEED: tuple[Mascota, ...] = (
    Mascota(id=1, nombre="Toby", especie="perro", duenio_id=1),
    Mascota(id=2, nombre="Michi", especie="gato", duenio_id=1),
    Mascota(id=3, nombre="Rocco", especie="perro", duenio_id=2),
)

PRACTICAS_SEED: tuple[Practica, ...] = (
    Practica(id=1, nombre="Consulta", precio=Decimal("15000.00")),
    Practica(id=2, nombre="Desparasitación", precio=Decimal("8000.00")),
    Practica(id=3, nombre="Vacuna antirrábica", precio=Decimal("12000.00")),
    Practica(id=4, nombre="Castración", precio=Decimal("35000.00")),
)

# Precio vigente del catálogo, para COPIARLO en ``turno_practica`` (RN-06).
PRECIO_POR_PRACTICA: dict[int, Decimal] = {
    practica.id: practica.precio for practica in PRACTICAS_SEED if practica.id is not None
}

PRACTICAS_DEL_TURNO_SEED: tuple[int, ...] = (1, 3)

TURNO_PRACTICAS_SEED: tuple[TurnoPractica, ...] = tuple(
    TurnoPractica(
        turno_id=1,
        practica_id=practica_id,
        precio_unitario=PRECIO_POR_PRACTICA[practica_id],
    )
    for practica_id in PRACTICAS_DEL_TURNO_SEED
)

# ``total`` se CALCULA con ``Decimal``, nunca se escribe como literal (RN-06).
TOTAL_TURNO_SEED: Decimal = sum(
    (linea.precio_unitario for linea in TURNO_PRACTICAS_SEED), Decimal("0.00")
)

TURNO_SEED: Turno = Turno(
    id=1,
    mascota_id=1,
    fecha=FECHA_TURNO_SEED,
    motivo="Control anual",
    total=TOTAL_TURNO_SEED,
)


def verificar_metadata() -> None:
    """Aborta con código 2 si ``SQLModel.metadata`` no tiene las seis tablas.

    Se ejecuta antes de abrir la transacción: un ``models.py`` sin importar
    dejaría un esquema incompleto, y el error aparecería recién en un INSERT.
    """
    tablas = set(SQLModel.metadata.tables)
    faltantes = TABLAS_ESPERADAS - tablas
    sobrantes = tablas - TABLAS_ESPERADAS
    if faltantes or sobrantes:
        if faltantes:
            print(
                "ERROR: faltan tablas en SQLModel.metadata: "
                f"{', '.join(sorted(faltantes))}. Revisá los imports de models.py."
            )
        if sobrantes:
            print(
                "ERROR: hay tablas de más en SQLModel.metadata: "
                f"{', '.join(sorted(sobrantes))}."
            )
        sys.exit(2)


async def cargar_seed(session: AsyncSession) -> None:
    """Inserta el seed respetando el orden que impone el grafo de claves foráneas."""
    session.add_all(list(DUENIOS_SEED))
    await session.flush()

    session.add_all(list(FICHAS_SEED))
    session.add_all(list(MASCOTAS_SEED))
    await session.flush()

    session.add_all(list(PRACTICAS_SEED))
    await session.flush()

    session.add(TURNO_SEED)
    await session.flush()

    session.add_all(list(TURNO_PRACTICAS_SEED))
    await session.flush()


async def resincronizar_secuencias(session: AsyncSession) -> None:
    """Deja cada secuencia en ``max(id)`` con ``is_called = true``.

    Sin esto, el primer alta posterior chocaría con una PK repetida (409).
    Nota: ``nextval`` no es transaccional, por eso acá solo se usa ``setval``
    sobre la secuencia creada en esta misma transacción.
    """
    for tabla in TABLAS_CON_SECUENCIA:
        secuencia = await session.scalar(
            text("SELECT pg_get_serial_sequence(:tabla, 'id')"), {"tabla": tabla}
        )
        if not secuencia:
            raise RuntimeError(
                f"la tabla '{tabla}' no tiene secuencia asociada a su columna id "
                "(pg_get_serial_sequence devolvió NULL)"
            )
        await session.execute(
            text(
                "SELECT setval(pg_get_serial_sequence(:tabla, 'id'), "
                f"(SELECT max(id) FROM {tabla}), true)"
            ),
            {"tabla": tabla},
        )


async def contar_tablas(session: AsyncSession) -> dict[str, int]:
    """Devuelve el conteo de filas de las seis tablas del seed."""
    conteos: dict[str, int] = {}
    for tabla in TABLAS_ORDENADAS:
        total = await session.scalar(text(f"SELECT count(*) FROM {tabla}"))
        conteos[tabla] = int(total or 0)
    return conteos


def imprimir_resumen(conteos: dict[str, int]) -> None:
    """Imprime los conteos por tabla como evidencia en consola."""
    print("Reinicio completo. Conteos por tabla:")
    for tabla in TABLAS_ORDENADAS:
        print(f"  {tabla}: {conteos[tabla]}")
    resumen = " · ".join(f"{tabla} {conteos[tabla]}" for tabla in TABLAS_ORDENADAS)
    print(f"Resumen: {resumen}")


def mensaje_seguro(exc: Exception, engine: AsyncEngine) -> str:
    """Primer renglón del error, sin credenciales, para una línea legible."""
    detalle = str(exc).strip()
    primer_renglon = detalle.splitlines()[0] if detalle else "sin detalle del driver"
    password = engine.url.password
    if password:
        primer_renglon = primer_renglon.replace(password, "***")
    return primer_renglon


async def reiniciar(fabrica: async_sessionmaker[AsyncSession]) -> None:
    """Ejecuta DDL + seed + secuencias en una única transacción."""
    async with fabrica() as session:
        async with session.begin():
            conn = await session.connection()
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)
            await cargar_seed(session)
            await resincronizar_secuencias(session)
            conteos = await contar_tablas(session)
    imprimir_resumen(conteos)


async def main() -> None:
    """Punto de entrada: valida el metadata, reinicia y traduce errores a código 2."""
    verificar_metadata()

    engine = crear_motor(settings.DATABASE_URL)
    destino = engine.url.render_as_string(hide_password=True)
    try:
        print(f"Reiniciando {destino} (se borran todas las tablas y sus datos)")
        await reiniciar(crear_fabrica(engine))
    except Exception as exc:  # noqa: BLE001 — cualquier fallo se reporta como código 2
        print(
            f"ERROR: no se pudo reiniciar la base {destino} — "
            f"{type(exc).__name__}: {mensaje_seguro(exc, engine)}"
        )
        print("La base no se modificó: la transacción se revirtió por completo.")
        sys.exit(2)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
