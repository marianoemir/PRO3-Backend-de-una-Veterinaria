# CHANGES — Secuencia de Implementación

> Índice canónico de los changes del proyecto **PRO3 — Backend de una Veterinaria**.
> **Revisión 2 (31/10/2026)**: se reemplazó el roadmap de 19 changes por **11 changes** (cada uno con un solo dueño). Nada estaba archivado todavía, así que no se perdió trabajo.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.** Quién hace qué, en qué orden y con qué comandos: `docs/DIVISION-DEL-EQUIPO.md`.

**Fuente de verdad**: `docs/MiniTP_Cap1a4_Consigna.pdf` + `knowledge-base/`.
**Equipo**: Mariano, Facundo y Andrés.
**Alcance**: solo backend. Sin frontend, CI/CD, Docker ni devops.

> **Nomenclatura**: los changes se identifican por su nombre (`fundacion-proyecto`) y un número `[01]`…`[11]`. Los **casos de prueba de la cátedra** se llaman "caso C-01…C-09 (cátedra)" y sus archivos son `test/caso_C-0X.http` (más `test/caso_C-08.sql`).

---

## Reglas de trabajo del equipo

- **No se hace `propose` de un change hasta que todas sus dependencias estén archivadas y mergeadas en `main`** (y cada uno haya hecho `git pull`). Mientras tanto solo se lee la KB y se revisan artefactos de otros.
- **Un change, un dueño.** Los archivos compartidos tienen dueño único (tabla de abajo). Si necesitás un cambio en un archivo ajeno, lo pedís al dueño.
- **Modelos antes que CRUD**: ningún `service`/`router` se propone antes de que `modelos-y-esquema` esté archivado.
- **Los DTO (`schemas.py`) viven en el change de cada módulo**, no en `modelos-y-esquema`. Ningún módulo importa DTO de otro: cada `schemas.py` define sus propias vistas resumidas.
- **No inventar reglas de negocio.** Lo que la consigna no dice está resuelto como decisión del equipo en `knowledge-base/09_decisiones_y_supuestos.md` (DD-08 a DD-15) o es pregunta abierta en `10_preguntas_abiertas.md`. Se justifica en el `design.md` y se menciona en el README como decisión propia.
- **No crear endpoints no listados** (`GET /duenios/`, `DELETE /mascotas/{id}`, `DELETE /practicas/{id}`, etc.).
- **Los tests no parchean código**: si un caso falla, se reporta al dueño del módulo y se corrige en una rama suya.
- **Si un change crece más de una jornada, se parte antes de empezar**, no a mitad de camino.

### Definición de terminado (por change)

- Dependencias archivadas y `openspec/changes/<change>/` completo en español, con ≥ 3 escenarios por spec.
- La app levanta con `uvicorn app.main:app` y el contrato del change responde lo esperado (smoke del change ejecutado, con salida real).
- `python reiniciar.py` sigue funcionando (si ya existe).
- Sin credenciales reales ni `.env` versionado.
- Change archivado **en la rama**, solo la línea propia marcada `[x]` en este archivo, PR revisado por otra persona y mergeado.

---

## Árbol de dependencias

```
[01] fundacion-proyecto                        Mariano
 ├── [02] modelos-y-esquema                    Mariano   ← CRÍTICO (30 %)
 │    ├── [03] duenios-y-ficha                 Facundo
 │    │    └── [05] mascotas-y-paginacion      Facundo
 │    ├── [04] practicas-catalogo              Andrés
 │    └── [09] reiniciar-y-seed                Mariano
 │         └── [06] turnos-alta-transaccional  Mariano   ← CRÍTICO
 │              └── [07] turnos-lecturas-y-baja Mariano  ← CRÍTICO
 └── [08] laboratorio-sin-bloqueo              Andrés

[03]+[04]+[05]+[06]+[07]+[08]+[09] ──▶ [10] pruebas-http-y-evidencia   Andrés
[10] ──────────────────────────────▶ [11] readme-y-entrega            Facundo
```

### Dependencias que conviene tener presentes

- **[08] solo necesita [01]**: Andrés puede arrancarlo apenas se mergea la fundación, en paralelo con los modelos.
- **[06] depende de [09] y no de [04]/[05]**: el alta de turno se prueba con los datos del seed (mascotas y prácticas ya cargadas por `reiniciar.py`), sin esperar los CRUD de esos módulos. Por eso `reiniciar-y-seed` va justo después de los modelos.
- **[03] y [05] son secuenciales** (misma persona): `[05]` se prueba mejor con dueños ya creados por API.
- **[10] espera a todos los endpoints** porque ejecuta los 9 casos de la cátedra de punta a punta.

---

## Archivos compartidos (dueño único)

| Archivo | Dueño | Regla |
|---|---|---|
| `app/main.py` | Mariano | `[01]` lo deja con los **seis routers ya incluidos** (vacíos); nadie más lo edita. |
| `app/core/config.py`, `app/core/database.py` | Mariano | Cambios de `echo`, pool o sesión se piden a Mariano. |
| `requirements.txt`, `env.example`, `.gitignore` | Mariano | Si un change necesita una dependencia, se la pide. |
| `AGENTS.md`, `CLAUDE.md` | Mariano | Siempre **idénticos** (verificar por hash). |
| `app/modules/duenios/*`, `app/modules/mascotas/*` (salvo `models.py`) | Facundo | |
| `app/modules/practicas/*` (salvo `models.py`), `app/modules/laboratorio/*` | Andrés | |
| `app/modules/*/models.py` (los cuatro) | Mariano | Se escriben todos en `[02]`, una sola mano; nadie más los toca. |
| `app/modules/turnos/*` | Mariano | |
| `reiniciar.py` | Mariano | `[09]`. |
| `test/**` | Andrés | `[10]`. |
| `README.md` | Facundo | `[11]`. Recibe de Andrés la evidencia del caso C-07. |
| `CHANGES.md` | cada uno su línea | Marcar `[x]` **solo** la línea del propio change, al archivarlo. |

---

## Tabla resumen

| # | Change | Dueño | Depende de | Cubre | Riesgo |
|---|---|---|---|---|---|
| 01 | `fundacion-proyecto` | Mariano | — | Ej. 1 (10 %) | CRITICO |
| 02 | `modelos-y-esquema` | Mariano | 01 | Ej. 3 (30 %) | CRITICO |
| 03 | `duenios-y-ficha` | Facundo | 02 | Ej. 2 (dueños, ficha) | ALTO |
| 04 | `practicas-catalogo` | Andrés | 02 | Ej. 2 (prácticas) | MEDIO |
| 05 | `mascotas-y-paginacion` | Facundo | 03 | Ej. 2 + Ej. 4 (alta mascota) | ALTO |
| 06 | `turnos-alta-transaccional` | Mariano | 02, 09 | Ej. 4 (15 %) | CRITICO |
| 07 | `turnos-lecturas-y-baja` | Mariano | 06 | Ej. 5 (15 %) | CRITICO |
| 08 | `laboratorio-sin-bloqueo` | Andrés | 01 | Ej. 6 (10 %) | ALTO |
| 09 | `reiniciar-y-seed` | Mariano | 02 | Ej. 3 (`reiniciar.py`) | MEDIO |
| 10 | `pruebas-http-y-evidencia` | Andrés | 03, 04, 05, 06, 07, 08, 09 | casos C-01..C-09 + evidencia | MEDIO |
| 11 | `readme-y-entrega` | Facundo | 10 | README + checklist | BAJO |

---

## [01] `fundacion-proyecto`

- **Estado**: `[x]` archivado · **Dueño**: Mariano · **Dependencias**: ninguna
- **Scope**:
  - Crear `app/__init__.py`, `app/core/{__init__,config,database}.py`, `app/main.py` y `app/modules/<módulo>/{__init__,models,schemas,service,router}.py` para `health`, `duenios`, `mascotas`, `practicas`, `turnos` y `laboratorio` (stubs; `router.py` = `APIRouter()` vacío salvo `health`).
  - `app/main.py`: `lifespan` que llama a `crear_motor(settings.DATABASE_URL)` y `crear_fabrica(engine)` desde `app/core/database.py`, guarda el engine y la fábrica en `app.state` y **cierra el motor** al apagar; incluye **los seis routers**. Sin `create_all` en el arranque (DD-01).
  - `app/core/database.py`: `crear_motor(url)` con `create_async_engine(url, echo=True)` y `crear_fabrica(engine)` con `async_sessionmaker(engine, expire_on_commit=False)`, más `get_session()` (una sesión por petición, desde `app.state`). `echo=True` habilita la evidencia del caso C-07.
  - `app/core/config.py`: carga `.env` con `python-dotenv`, expone `DATABASE_URL`; si falta, **falla con mensaje explícito** al arrancar.
  - `health`: `GET /health/live` → 200 `{"estado": "vivo"}` sin tocar la base; `GET /health/ready` → `SELECT 1`, 200 `{"estado": "listo", "base": "ok"}` o **503** `{"estado": "no_disponible", "base": "error"}` (DD-14). Handlers `async def`.
  - `requirements.txt` (`fastapi[standard]>=0.111`, `sqlmodel>=0.0.24`, `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.30`, `python-dotenv>=1.0`), `env.example` sin secretos.
- **Smoke**: `pip install -r requirements.txt`; `uvicorn app.main:app` levanta; `/openapi.json` 200; `/health/live` 200; `/health/ready` 200 con la base arriba y **503** con PostgreSQL detenido (mientras `/health/live` sigue en 200); sin `DATABASE_URL` el arranque falla con mensaje claro.
- **Leer antes**:
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico, §Arquitectura general, §API REST
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Dependencias
  - `knowledge-base/06_funcionalidades.md` §US-001, §US-002
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/05_reglas_de_negocio.md` RN-17, RN-20, RN-21, RN-22, RN-24
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-01, DD-02, DD-14

---

## [02] `modelos-y-esquema`

- **Estado**: `[x]` archivado · **Dueño**: Mariano · **Dependencias**: `01`
- **Scope** (solo `models.py`; **sin DTO, sin endpoints**):
  - `duenios/models.py`: `Duenio` (`email` UNIQUE) y `FichaDuenio` (`duenio_id` FK UNIQUE). `Duenio.ficha` devuelve **un objeto** (`uselist=False`).
  - `mascotas/models.py`: `Mascota` (`duenio_id` FK **ON DELETE RESTRICT**, índice en `duenio_id`).
  - `practicas/models.py`: `Practica` (`nombre` UNIQUE, `precio` `NUMERIC(10,2)` con **CHECK `precio > 0`**).
  - `turnos/models.py`: `Turno` (`mascota_id` FK con índice, `fecha` con zona horaria, `motivo`, `total` `NUMERIC(12,2)` con **CHECK `total >= 0`**) y `TurnoPractica` (**PK compuesta `(turno_id, practica_id)`**, `turno_id` FK **ON DELETE CASCADE**, `practica_id` FK con índice, `precio_unitario` `NUMERIC(10,2)` con **CHECK `precio_unitario > 0`**; **sin** índice propio en `turno_id`).
  - `Relationship(back_populates=...)` en **ambos extremos** de cada relación (`Duenio.ficha`/`FichaDuenio.duenio`, `Duenio.mascotas`/`Mascota.duenio`, `Mascota.turnos`/`Turno.mascota`, `Turno.practicas`/`TurnoPractica.turno`, `Practica.turnos`/`TurnoPractica.practica`).
  - `Turno.practicas` con **`passive_deletes=True`**: el borrado lo decide la base.
  - Dinero con `Decimal`; ids enteros autoincrementales (DD documentada en `04_modelo_de_datos.md`).
  - Justificar en `design.md` el lado de cada FK y cada regla de borrado (es el 30 % de la nota).
- **Smoke** (con `psql` y un script temporal **no versionado** que haga `create_all`): `\d` de las 6 tablas muestra UNIQUE, CHECK, FK con RESTRICT/CASCADE, PK compuesta e índices; `configure_mappers()` no da error; por SQL: precio 0 rechazado, dos filas iguales `(turno_id, practica_id)` rechazadas, borrar un dueño con mascotas rechazado, borrar un turno borra sus `turno_practica`.
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (completo)
  - `knowledge-base/05_reglas_de_negocio.md` RN-01 a RN-09, RN-14, RN-16
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-05, DD-06, DD-07, DD-13
  - `knowledge-base/10_preguntas_abiertas.md` IN-03

---

## [03] `duenios-y-ficha`

- **Estado**: `[ ]` pendiente · **Dueño**: Facundo · **Dependencias**: `02`
- **Scope** (`duenios/schemas.py`, `service.py`, `router.py`):
  - DTO: `DuenioCreate` (sin `id`), `DuenioUpdate` (`nombre`, `email` opcionales; DD-08), `DuenioRead` (con ficha), `FichaCreate` (teléfono y dirección obligatorios; DD-12), `FichaRead`, y una vista resumida de mascota **propia de este módulo** para `GET /duenios/{id}/mascotas`.
  - `POST /duenios/` → 201, 409 (email repetido: se escribe y se captura `IntegrityError` → `rollback()`; **sin `SELECT` previo**), 422.
  - `GET /duenios/{id}` → 200 con ficha (`joinedload(Duenio.ficha)`), 404, 422 si el id no es entero.
  - `PATCH /duenios/{id}` → solo campos enviados (`exclude_unset`); 200, 404, 409, 422.
  - `DELETE /duenios/{id}` → 204, 404, **409** si tiene mascotas (lo rechaza la base por `RESTRICT`; `rollback()`).
  - `POST /duenios/{id}/ficha` → 201, 404, **409** si ya tiene ficha.
  - `GET /duenios/{id}/mascotas` → lista simple (DD-10); `[]` si no tiene; 404 si el dueño no existe.
  - **No** implementar `GET /duenios/` ni `DELETE` de ficha.
- **Smoke**: email repetido 409; `/duenios/abc` 422; PATCH parcial no borra lo no enviado; segunda ficha 409; dueño inexistente 404; borrar dueño con mascotas 409 (con datos del seed si `09` ya está mergeado, o insertando por SQL).
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-003 a §US-007, §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 2, §Flujo 3, §Flujo 7
  - `knowledge-base/05_reglas_de_negocio.md` RN-01, RN-03, RN-08, RN-10 a RN-12, RN-14, RN-15
  - `knowledge-base/04_modelo_de_datos.md` §`duenio`, §`ficha_duenio`
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-03, DD-04, DD-08, DD-09, DD-10, DD-12

---

## [04] `practicas-catalogo`

- **Estado**: `[x]` archivado · **Dueño**: Andrés · **Dependencias**: `02`
- **Scope** (`practicas/schemas.py`, `service.py`, `router.py`):
  - DTO: `PracticaCreate` (sin `id`; precio mayor que cero validado **también** en el DTO, RN-04) y `PracticaRead`. Precio `Decimal`, serializado como string.
  - `POST /practicas/` → 201, 409 (nombre repetido por `IntegrityError`, sin `SELECT` previo), 422 (precio ≤ 0).
  - `GET /practicas/` → 200 con el catálogo, ordenado por `id` (DD-15).
  - Sin `PATCH` ni `DELETE`.
- **Smoke**: nombre repetido 409; precio 0 → 422; precio negativo → 422; el listado devuelve las prácticas; el precio sale como string (`"15000.00"`).
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-012, §US-013
  - `knowledge-base/05_reglas_de_negocio.md` RN-02, RN-04, RN-10, RN-12
  - `knowledge-base/04_modelo_de_datos.md` §`practica`
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-06, DD-15

---

## [05] `mascotas-y-paginacion`

- **Estado**: `[ ]` pendiente · **Dueño**: Facundo · **Dependencias**: `03`
- **Scope** (`mascotas/schemas.py`, `service.py`, `router.py`):
  - DTO: `MascotaCreate` (recibe `duenio_id`, sin `id`; `especie` texto libre no vacío), `MascotaRead` (con dueño resumido, vista propia de este módulo) y el envoltorio de paginación.
  - `POST /mascotas/` → 201, **409** si el dueño no existe (la FK lo rechaza; sin `SELECT` previo), 422.
  - `GET /mascotas/{id}` → 200 con su dueño (`joinedload(Mascota.duenio)`), 404.
  - `GET /mascotas/?page=&size=` → `{ items, total, page, size, pages }`; `size` 20 por defecto y de 1 a 100; página más allá de `pages` → 422; **la primera página siempre responde 200** (base vacía → `items: []`, `total: 0`, `pages: 0`). `total` con `count(*)`, página con `offset`/`limit`, orden por `id`. Dos consultas fijas, sin N+1.
  - **No** implementar `DELETE /mascotas/{id}`.
- **Smoke**: dueño inexistente 409; `size=0` y `size=101` → 422; `page` fuera de rango → 422; base vacía → 200 vacío; el detalle trae el dueño sin consultas extra.
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-008 a §US-010
  - `knowledge-base/07_flujos_principales.md` §Flujo 7
  - `knowledge-base/05_reglas_de_negocio.md` RN-10 a RN-15
  - `knowledge-base/02_descripcion_general.md` §Envoltorio de paginación
  - `knowledge-base/04_modelo_de_datos.md` §`mascota`
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-03, DD-04, DD-12, DD-15

---

## [06] `turnos-alta-transaccional`

- **Estado**: `[x]` completado · **Dueño**: Mariano · **Dependencias**: `02`, `09`
- **Scope** (`turnos/schemas.py`, `service.py`, `router.py`):
  - DTO: `TurnoCreate` (`mascota_id`, `fecha`, `motivo` obligatorio, `practicas` con **al menos una**), `TurnoPracticaCreate` (solo `practica_id`), `TurnoRead` (mascota resumida y prácticas con `practica_id`, `nombre`, `precio_unitario`; sin id de fila, DD-11). **Ni precio ni total en la entrada** (RN-06). Vistas resumidas propias de este módulo. `fecha` de salida en UTC.
  - `POST /turnos/` en **una sola transacción**: leer del catálogo las prácticas pedidas; si **alguna no existe** → `rollback()` → 409 y **no queda nada** (ni turno ni filas de `turno_practica`, RN-23); copiar `precio` → `precio_unitario`; calcular `total` con `Decimal`; persistir `Turno` + `TurnoPractica`; práctica repetida → PK compuesta → `IntegrityError` → `rollback()` → 409 (RN-07); mascota inexistente → 409 por FK; lista vacía → 422.
  - La respuesta se arma **sin carga perezosa** (re-consulta con carga anticipada o armado desde los objetos ya cargados).
- **Smoke**: turno válido con dos prácticas → 201, precios copiados y total correcto (`"27000.00"` con las prácticas 1 y 3 del seed); práctica inexistente → 409 y `SELECT count(*) FROM turno` no cambia; práctica repetida → 409; lista vacía → 422; cambiar el precio en el catálogo después no altera el turno ya creado.
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-014
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/05_reglas_de_negocio.md` RN-05, RN-06, RN-07, RN-14, RN-23
  - `knowledge-base/04_modelo_de_datos.md` §`turno`, §`turno_practica`, §Justificación del lado de cada clave foránea
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-03, DD-06, DD-07, DD-11, DD-12, SU-02
  - `knowledge-base/02_descripcion_general.md` §API REST (ejemplo de alta de turno)

---

## [07] `turnos-lecturas-y-baja`

- **Estado**: `[ ]` pendiente · **Dueño**: Mariano · **Dependencias**: `06`
- **Scope**:
  - `GET /turnos/{id}`: una consulta base con `joinedload(Turno.mascota)` y `selectinload(Turno.practicas).joinedload(TurnoPractica.practica)`. 200 con turno, mascota y prácticas; 404. **Número fijo de consultas**: no crece con la cantidad de prácticas (RN-15).
  - `DELETE /turnos/{id}`: buscar, borrar y `commit`; la base borra `turno_practica` por `ON DELETE CASCADE` y `passive_deletes` evita que el ORM las toque. 204; 404.
  - **Evidencia del caso C-07**: con `echo=True`, capturar la consola del detalle de un turno con 1 práctica y con 3; mismas consultas. Guardar la salida para `[10]`.
- **Smoke**: el detalle con 1 y con 3 prácticas ejecuta la **misma cantidad de `SELECT`**; borrar un turno y comprobar por SQL que no quedan filas hijas; borrar un turno inexistente → 404; ninguna lectura falla con `MissingGreenlet`.
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-015, §US-016
  - `knowledge-base/07_flujos_principales.md` §Flujo 5, §Flujo 6
  - `knowledge-base/05_reglas_de_negocio.md` RN-09, RN-14, RN-15, RN-16
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-04, DD-05
  - `knowledge-base/04_modelo_de_datos.md` §Por qué `turno_practica.turno_id` no necesita índice propio

---

## [08] `laboratorio-sin-bloqueo`

- **Estado**: `[x]` archivado · **Dueño**: Andrés · **Dependencias**: `01`
- **Scope** (`laboratorio/`):
  - `cliente.py`: el código **exacto** que entrega la cátedra (`consultar_stock(vacuna: str) -> int` con `time.sleep(1)`), **sin modificarlo**.
  - `service.py`: `await asyncio.to_thread(consultar_stock, vacuna)`.
  - `router.py`: `GET /laboratorio/stock/{vacuna}` → 200 `{"vacuna": ..., "stock": ...}`, handler `async def`.
- **Smoke**: tres consultas simultáneas al laboratorio y un `GET /health/live` en el medio: el de salud responde de inmediato (anotar latencias para el caso C-09).
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-017
  - `knowledge-base/07_flujos_principales.md` §Flujo 8
  - `knowledge-base/05_reglas_de_negocio.md` RN-17, RN-18, RN-19
  - `knowledge-base/09_decisiones_y_supuestos.md` SU-01, DD-15
  - `knowledge-base/02_descripcion_general.md` §Integraciones externas

---

## [09] `reiniciar-y-seed`

- **Estado**: `[x]` archivado · **Dueño**: Mariano · **Dependencias**: `02`
- **Scope** (`reiniciar.py`):
  - Asincrónico; carga `DATABASE_URL` del mismo `.env` que la app (SU-04); importa los modelos de los cuatro módulos para poblar `SQLModel.metadata`.
  - `drop_all` → `create_all` → seed mínimo: **2 dueños (uno con ficha), 3 mascotas, 4 prácticas, 1 turno con 2 prácticas** (con `precio_unitario` copiado y `total` calculado). Ids que hacen funcionar el ejemplo del enunciado: mascota 1 = Toby (perro), práctica 1 = Consulta `15000.00`, práctica 3 = Vacuna antirrábica `12000.00`; el próximo turno recibe `id = 2`.
  - Funciona sobre base **vacía** y sobre base ya poblada. Datos ficticios.
- **Smoke**: correrlo dos veces seguidas; contar filas por tabla; sobre una base recién creada (`DROP DATABASE` + `CREATE DATABASE`) también funciona.
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial
  - `knowledge-base/06_funcionalidades.md` §US-018
  - `knowledge-base/07_flujos_principales.md` §Flujo 9
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-01, SU-04

---

## [10] `pruebas-http-y-evidencia`

- **Estado**: `[ ]` pendiente · **Dueño**: Andrés · **Dependencias**: `03`, `04`, `05`, `06`, `07`, `08`, `09`
- **Scope** (`test/`): un archivo `.http` por caso, cada uno con la respuesta esperada en un comentario, para correr después de `python reiniciar.py`.
  - `caso_C-01.http` `/duenios/abc` → 422 · `caso_C-02.http` email y nombre repetidos → 409 con mensaje propio · `caso_C-03.http` segunda ficha → 409 · `caso_C-04.http` mascota con dueño inexistente → 409; turno con práctica inexistente → 409 y nada guardado · `caso_C-05.http` borrar dueño con mascotas → 409; borrar turno → 204 y sin prácticas · `caso_C-06.http` turno válido con dos prácticas → 201 con precios y total · `caso_C-07.http` detalle con 1 y con 3 prácticas → misma cantidad de consultas · `caso_C-08.sql` (+ `.http` con el precio antes y después) · `caso_C-09.http` tres consultas al laboratorio y `/health/live`.
  - `test/evidencia_C-07.txt`: fragmento de consola con las consultas del detalle con 1 y con 3 prácticas. **Entregable obligatorio.**
  - Si un caso falla, se reporta al dueño del módulo; **no** se parchea código desde `test/`.
- **Leer antes**:
  - `docs/MiniTP_Cap1a4_Consigna.pdf` §Casos de prueba mínimos
  - `knowledge-base/06_funcionalidades.md` §US-019
  - `knowledge-base/05_reglas_de_negocio.md` RN-01 a RN-09, RN-12, RN-15, RN-19
  - `knowledge-base/08_arquitectura_propuesta.md` §Entregables del repositorio
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-15, SU-02

---

## [11] `readme-y-entrega`

- **Estado**: `[ ]` pendiente · **Dueño**: Facundo · **Dependencias**: `10`
- **Scope** (`README.md`):
  - Pasos desde cero: requisitos (Python 3.12+, PostgreSQL 16+), entorno virtual, `pip install -r requirements.txt`, copiar `env.example` a `.env`, crear la base, `python reiniciar.py`, `uvicorn app.main:app`.
  - Tabla de endpoints y códigos; cómo correr los `.http` y el `.sql` del caso C-08.
  - Explicación en **1–2 líneas** de por qué `turno_practica.turno_id` no necesita índice propio: la PK compuesta `(turno_id, practica_id)` ya tiene un B-tree con `turno_id` como primera columna. Requisito explícito de la consigna.
  - Enlace a `test/evidencia_C-07.txt` y a los casos.
  - Sección "Decisiones propias del equipo" con DD-08 a DD-15 (no presentarlas como reglas de la cátedra).
  - Checklist final: `requirements.txt`, `env.example`, `reiniciar.py`, `test/`, `README.md`, sin `.env` ni credenciales.
- **Verificación**: Mariano sigue el README **al pie de la letra** desde una base vacía y un entorno virtual nuevo.
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Entregables del repositorio
  - `knowledge-base/04_modelo_de_datos.md` §Por qué `turno_practica.turno_id` no necesita índice propio
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico, §API REST
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-08 a DD-15
