# Propuesta: reiniciar-y-seed

## Why

El change [02] `modelos-y-esquema` declaró las seis tablas, pero **nada las crea**: `create_all` ya estaba reservado a `reiniciar.py` ([09], DD-01) y ese archivo todavía no existe. Hoy el proyecto no tiene forma de dejar la base en un estado conocido, y sin eso no se puede correr ningún caso de prueba ni el alta de turno del Ej. 4, que el enunciado documenta **con datos concretos**: mascota `1` ("Toby", perro), práctica `1` ("Consulta", `15000.00`), práctica `3` ("Vacuna antirrábica", `12000.00`) y `"id": 2` como turno recién creado (`knowledge-base/02_descripcion_general.md` §Ejemplo de alta de turno, §Seed data inicial de `04_modelo_de_datos.md`).

Este change entrega el único artefacto que falta para eso: un script ejecutable que **reconstruye el esquema desde los modelos y lo puebla con datos ficticios reproducibles**, de modo que el evaluador (y el change [06]) partan siempre del mismo punto. Es el [09] del roadmap, dependencia directa de [06] `turnos-alta-transaccional`.

## What Changes

- **Se crea `reiniciar.py`** en la raíz del repo (dueño único: Mariano, `CHANGES.md` §Archivos compartidos). Es un script **asincrónico**: `asyncio.run(...)`, motor async de SQLAlchemy/SQLModel sobre `asyncpg`.
- **Configuración**: lee `DATABASE_URL` del **mismo `.env`** que la app, reutilizando `app.core.config.settings` y la fábrica de `app/core/database.py` (SU-04, RN-24). Si la variable falta, se hereda el mensaje `FATAL` de `config.py` y la ejecución termina con código distinto de 0.
- **Reconstrucción del esquema**: importa los modelos de los **cuatro módulos** (`app/modules/{duenios,mascotas,practicas,turnos}/models.py`) para poblar `SQLModel.metadata`, y ejecuta `drop_all` → `create_all` → seed. Sin Alembic (DD-01). Funciona tanto sobre una base **vacía** como sobre una ya poblada.
- **Seed mínimo** (`knowledge-base/04_modelo_de_datos.md` §Seed data inicial): 2 dueños (uno **con ficha**), 3 mascotas, 4 prácticas y 1 turno con 2 prácticas, con `precio_unitario` **copiado** del catálogo y `total` **calculado** (`Decimal`, nunca `float`).
- **Ids que hacen funcionar el ejemplo del enunciado**: `duenio` 1 con ficha y 2 sin ficha; `mascota` 1 = Toby (perro), del dueño 1; `practica` 1 = Consulta `15000.00`; `practica` 3 = Vacuna antirrábica `12000.00`; `turno` 1 con 2 prácticas.
- **Contrato de secuencia**: el **próximo turno** que se dé de alta después del seed MUST recibir `id = 2`. Si el seed inserta ids explícitos, la secuencia `turno.id` se resincroniza con `setval`.
- **Atomicidad y fallo legible**: todo el reinicio corre en **una sola transacción**; ante cualquier error se hace `rollback`, se imprime un mensaje claro en español (sin traceback críptico ni credenciales) y el proceso termina con **código de salida distinto de 0**. La base nunca queda a medio poblar.
- **Idempotencia por reconstrucción**: correr el script dos veces seguidas deja exactamente el mismo estado, sin duplicados ni violaciones de PK/UNIQUE.
- **Datos ficticios**: nombres, emails, teléfonos y direcciones inventados; nada real.

**BREAKING**: ninguno. `reiniciar.py` no existe todavía y ningún otro archivo cambia.

## Alcance

| ¿Qué incluye? | ¿Qué queda fuera? |
|---|---|
| `reiniciar.py` en la raíz: imports de los cuatro `models.py`, lectura de `DATABASE_URL` vía `app.core.config`, motor/fábrica de `app/core/database.py`, `drop_all` + `create_all` y seed en una transacción | **Cualquier otro archivo del repo**: `app/**` (incluidos `app/core/{config,database}.py`, que son de Mariano pero de otro change), `requirements.txt`, `env.example`, `.gitignore`, `CHANGES.md`, `README.md`, `test/**` |
| Datos del seed: 2 dueños, 1 ficha, 3 mascotas, 4 prácticas, 1 turno, 2 filas de `turno_practica`, con los ids del enunciado | **Endpoints, DTO y services** de dueños, mascotas, prácticas y turnos (changes [03]–[07]); el alta de turno que recibe `id = 2` es de [06] |
| Contrato de ids y de secuencia verificable (mascota 1, práctica 1, práctica 3, próximo `turno.id` = 2) | **Casos de prueba `.http`/`.sql` y evidencia** (change [10]); el README y su checklist (change [11]) |
| Códigos de salida, mensajes de error y comportamiento atómico del script | Migraciones versionadas (Alembic, DD-01), Docker/CI, auth, repositorios y colas (fuera de alcance global) |

El alcance de archivos es **literal**: este change toca **solo `reiniciar.py`**. Si durante el apply aparece la tentación de agregar un parámetro a `crear_motor` (por ejemplo para apagar `echo=True`), eso es un cambio de `app/core/database.py` y va por otro change, no acá.

## Capabilities

### New Capabilities

- `reinicio-de-base-datos`: deja la base en un estado conocido y reproducible — reconstruye el esquema desde los modelos, carga un seed mínimo con los identificadores que el enunciado usa en sus ejemplos, garantiza que el próximo turno reciba `id = 2`, se comporta igual sobre una base vacía o poblada, y falla de forma explícita y atómica cuando la configuración o la conexión no están disponibles.

### Modified Capabilities

Ninguna. `fundacion` describe el arranque de la API y `modelo-de-datos` el esquema; este change **no cambia el comportamiento especificado** por ninguna de las dos: solo agrega el proceso que materializa ese esquema y lo puebla. No se tocan sus requisitos ni sus escenarios.

## Reglas de negocio cubiertas

El seed **no relaja ninguna garantía**: los datos que carga satisfacen las reglas que la base exige, y el script no agrega validaciones nuevas.

- **RN-06** — el precio se copia del catálogo y el total lo calcula el servidor: el seed copia `15000.00` y `12000.00` a `turno_practica.precio_unitario` y deja `turno.total = 27000.00`, calculado con `Decimal` y no escrito a mano como constante suelta. Es justamente el valor que el enunciado espera en el alta de turno.
- **RN-04** — precio de práctica mayor que cero: las cuatro prácticas del seed tienen precio `> 0`, así pasan el `CHECK` y sirven de ejemplo válido para [04].
- **RN-01, RN-02, RN-03, RN-07, RN-08** — los datos del seed son consistentes con las garantías de unicidad y de PK: emails y nombres de práctica distintos, una sola ficha, y dos prácticas distintas en el turno 1 (la PK compuesta `(turno_id, practica_id)` no se viola).
- **RN-09** — el turno 1 tiene sus dos filas en `turno_practica`; borrarlo por `DELETE /turnos/{id}` ([07]) debe dejar 0 filas hijas, que es el dato de partida del caso C-05.
- **RN-23** — *todo o nada*: el seed aplica el mismo criterio en su propio ámbito (una transacción, `rollback` ante error), de modo que la base nunca queda a medio poblar.
- **RN-24** — `DATABASE_URL` sale del entorno (`.env` no versionado, `env.example` sin secretos); el script no hardcodea credenciales ni las imprime.

## Impact

- **Código afectado**: **`reiniciar.py` (nuevo, raíz del repo)**. Ningún otro archivo se modifica. `app/**`, `requirements.txt`, `env.example` y `test/**` quedan intactos.
- **Base de datos**: al ejecutarse, las seis tablas se **borran y se recrean** con el esquema de [02] y quedan pobladas con 2 dueños, 1 ficha, 3 mascotas, 4 prácticas, 1 turno y 2 filas de `turno_practica`. La secuencia `turno.id` queda en 1 para que el próximo alta reciba 2.
- **APIs**: ninguna. No hay endpoints, rutas ni DTO nuevos; el contrato HTTP no cambia.
- **Dependencias**: ninguna nueva. `sqlalchemy[asyncio]`, `sqlmodel`, `asyncpg` y `python-dotenv` ya están en `requirements.txt`; el script solo los consume.
- **Changes que desbloquea**: [06] `turnos-alta-transaccional` (depende de [09] porque se prueba con estos datos) y, a través de él, [07], [10] y [11].
- **Riesgo principal**: que el script apunte a una base distinta de la que usa la API (riesgo declarado en **SU-04**) o que la secuencia de `turno.id` quede desincronizada y el primer alta posterior falle con 409 por PK repetida. Ambos se atacan en `design.md` y se verifican en `tasks.md`.
- **Riesgo operativo**: el script **destruye** el contenido de la base indicada en `.env`. Es su propósito (US-018), no un efecto colateral: por eso imprime el destino antes de borrar y nunca se ejecuta contra una base que no esté configurada ahí.
