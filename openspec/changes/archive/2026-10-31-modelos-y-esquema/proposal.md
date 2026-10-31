# Propuesta: modelos-y-esquema

## Why

La fundación ([01] `fundacion-proyecto`) dejó los cuatro `models.py` de dominio como stubs vacíos: hoy el proyecto no tiene ninguna tabla declarada, y ningún change posterior (dueños, mascotas, prácticas, turnos, seed, pruebas) puede escribir, leer ni validar nada. Este change materializa el **modelo de datos normativo** de `knowledge-base/04_modelo_de_datos.md` en modelos SQLModel, de modo que `create_all` genere el esquema completo con sus restricciones y que la base —no el código— sea la garante de las reglas RN-01 a RN-09. Es el change [02] del roadmap y el prerrequisito de los nueve changes que siguen.

## What Changes

- **`app/modules/duenios/models.py`**: se declaran `Duenio` (tabla `duenio`, `email` UNIQUE) y `FichaDuenio` (tabla `ficha_duenio`, `duenio_id` FK UNIQUE). `Duenio.ficha` es una relación **a uno** (`uselist=False`).
- **`app/modules/mascotas/models.py`**: se declara `Mascota` (tabla `mascota`, `duenio_id` FK **ON DELETE RESTRICT** con índice propio).
- **`app/modules/practicas/models.py`**: se declara `Practica` (tabla `practica`, `nombre` UNIQUE, `precio` `NUMERIC(10,2)` con CHECK `precio > 0`).
- **`app/modules/turnos/models.py`**: se declaran `Turno` (tabla `turno`, `mascota_id` FK con índice, `fecha` `TIMESTAMP WITH TIME ZONE`, `total` `NUMERIC(12,2)` con CHECK `total >= 0`) y `TurnoPractica` (tabla `turno_practica`, **PK compuesta `(turno_id, practica_id)`**, `turno_id` FK **ON DELETE CASCADE**, `practica_id` FK con índice propio, `precio_unitario` `NUMERIC(10,2)` con CHECK `precio_unitario > 0`).
- **Relaciones en ambos extremos** con `back_populates`: `Duenio.ficha` ↔ `FichaDuenio.duenio`, `Duenio.mascotas` ↔ `Mascota.duenio`, `Mascota.turnos` ↔ `Turno.mascota`, `Turno.practicas` ↔ `TurnoPractica.turno`, `Practica.turnos` ↔ `TurnoPractica.practica`. `Turno.practicas` lleva **`passive_deletes=True`** (DD-05): el borrado en cascada lo decide la base.
- **`__tablename__` explícito** en las seis clases y nombres de tabla/columna **exactamente** los de la KB (no renombrar ni quitar columnas).
- **Dinero con `Decimal`** (`NUMERIC`), nunca `float` (DD-06); ids enteros autoincrementales.

**BREAKING**: ninguno. Los cuatro `models.py` estaban vacíos; no hay consumidores previos del modelo.

## Alcance

| ¿Qué incluye? | ¿Qué queda fuera? |
|---|---|
| Declaraciones de modelo en los cuatro `models.py` (`Duenio`, `FichaDuenio`, `Mascota`, `Practica`, `Turno`, `TurnoPractica`) | **DTO / `schemas.py`** — cada módulo en su change ([03], [04], [05], [06], [07]) |
| `__tablename__`, columnas, PK compuesta, UNIQUE, CHECK, FK con su regla de borrado e índices | **Endpoints / `router.py`**, `service.py`, manejo de `IntegrityError` y códigos HTTP |
| Relaciones `Relationship` con `back_populates` y `passive_deletes=True` | **`reiniciar.py`** (`create_all`/`drop_all` y seed) — change [09] `reiniciar-y-seed` |
| Verificación del esquema por SQL en **pgAdmin** y del mapeo ORM con `configure_mappers()` | Tests HTTP y evidencia — change [10] `pruebas-http-y-evidencia`; migraciones **Alembic**, auth, repositorios y colas (fuera de alcance global) |

Este change **no crea la base**: `create_all` vive en `reiniciar.py` ([09], DD-01). La verificación asume que las tablas ya existen (creadas por un `create_all` manual desde un script temporal no versionado).

## Capabilities

### New Capabilities

- `modelo-de-datos`: declara y garantiza en la base el esquema del dominio veterinario — las seis tablas, sus columnas y tipos, la PK compuesta de `turno_practica`, las restricciones UNIQUE y CHECK, la acción de borrado de cada clave foránea, los índices y las relaciones del ORM en ambos extremos. Es la capability que consumen todos los módulos funcionales.

### Modified Capabilities

Ninguna. `fundacion` (única capability existente) no cambia sus requisitos: la fundación ya declaró que los `models.py` se completan en este change.

## Reglas de negocio cubiertas

Garantizadas **en la base** (no con consultas previas "¿ya existe?", DD-03):

- **RN-01** — email de dueño único → `UNIQUE` en `duenio.email`.
- **RN-02** — nombre de práctica único → `UNIQUE` en `practica.nombre`.
- **RN-03** — máximo una ficha por dueño → `UNIQUE` en `ficha_duenio.duenio_id`.
- **RN-04** — precio de práctica mayor que cero → `CHECK (precio > 0)`.
- **RN-07** — una práctica no aparece dos veces en un turno → **PK compuesta `(turno_id, practica_id)`** de `turno_practica`.
- **RN-08** — no se borra un dueño con mascotas → `ON DELETE RESTRICT` en `mascota.duenio_id`.
- **RN-09** — al borrar un turno se borran sus prácticas → `ON DELETE CASCADE` en `turno_practica.turno_id`, con `passive_deletes=True` en `Turno.practicas` (DD-05).
- **RN-05 / RN-06** — el precio se congela en la relación y el total lo calcula el servidor → las columnas `turno_practica.precio_unitario` y `turno.total` existen en el esquema con sus CHECK (el cálculo es del `service`, change [06]).
- **RN-14 / RN-16** — ninguna relación se declara con carga perezosa; el modelo no habilita `lazy="select"` implícito y las lecturas se resolverán con carga anticipada en cada consulta.

## Impact

- **Código afectado**: `app/modules/duenios/models.py`, `app/modules/mascotas/models.py`, `app/modules/practicas/models.py` y `app/modules/turnos/models.py`. Ningún otro archivo se toca.
- **Base de datos**: aparecen las seis tablas `duenio`, `ficha_duenio`, `mascota`, `practica`, `turno`, `turno_practica` con sus PK, UNIQUE, CHECK, FK, acciones de borrado e índices, al ejecutarse `create_all`.
- **APIs**: ninguna. Sin routers ni DTO, el contrato HTTP no cambia.
- **Dependencias**: ninguna nueva. Solo `sqlmodel` / `sqlalchemy`, ya presentes en `requirements.txt`.
- **Changes que desbloquea**: [03] `duenios-y-ficha`, [04] `practicas-catalogo`, [09] `reiniciar-y-seed` (dependen directo de [02]); a través de ellos, [05], [06], [07], [08], [10] y [11].
- **Riesgo principal**: el orden de las columnas de la PK compuesta y la ausencia de índice propio en `turno_practica.turno_id` son puntos que la corrección revisa; se fijan en `design.md` y se verifican por SQL.
