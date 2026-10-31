# 02_descripcion_general.md

> **Fuente normativa**: consigna "Veterinaria — trabajo práctico breve con FastAPI y PostgreSQL" (Unidades 1 a 4). Todo lo que no está acá ni en la consigna va a `10_preguntas_abiertas.md`.

## Stack tecnológico

**Impuesto por la consigna: no se cambia ni se bajan las versiones mínimas.**

| Capa | Tecnología | Versión mínima |
|---|---|---|
| Lenguaje | Python | 3.12 |
| Framework web | FastAPI (todos los handlers `async def`) | 0.111 |
| ORM | SQLModel + SQLAlchemy 2.0 asincrónico | 0.0.24 / 2.0 |
| Driver | asyncpg | 0.30 |
| Base de datos | PostgreSQL | 16 |
| Entorno | python-dotenv | 1.0 |
| Servidor | uvicorn (el que instala `fastapi[standard]`) | — |

- `DATABASE_URL` se lee del entorno, definida en un `.env` **que no se versiona**; el repo incluye `env.example` con la forma del valor y **sin secretos**.
- Forma del valor: `postgresql+asyncpg://usuario:clave@localhost:5432/veterinaria`.
- No hay frontend, ni Docker, ni CI, ni autenticación, ni Alembic, ni repositorios, ni colas.

## Arquitectura general

- **Un solo servicio** FastAPI organizado **por módulo funcional**; todos los módulos repiten la misma estructura (`models.py`, `schemas.py`, `service.py`, `router.py`).
- Módulos mínimos: `health`, `duenios`, `mascotas`, `practicas`, `turnos`, `laboratorio`. `FichaDuenio` vive en `duenios` y `TurnoPractica` en `turnos`.
- **Ciclo de vida**: el motor asincrónico y la fábrica de sesiones se crean en el `lifespan`, se guardan en `app.state` y el motor se cierra al apagar.
- **Sesión por petición**: `Depends(get_session)`, creada con `expire_on_commit=False`.
- **Capas**: `router.py` recibe, delega y declara la respuesta; `service.py` contiene la lógica y recibe la sesión como parámetro; `models.py` define tablas y relaciones; `schemas.py` define los DTO.
- El esquema se crea con `SQLModel.metadata.create_all` desde `reiniciar.py`.

Detalle de estructura: [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md).

## Integraciones externas

**Una sola**: la biblioteca del laboratorio, `app/modules/laboratorio/cliente.py`, entregada por la cátedra. Es **sincrónica** (`time.sleep(1)`) y **no se modifica**:

```python
import time

def consultar_stock(vacuna: str) -> int:
    """Biblioteca del laboratorio: sincrónica, tarda un segundo."""
    time.sleep(1)
    return 10 + len(vacuna)
```

Se invoca **fuera del bucle de eventos** (por ejemplo con `await asyncio.to_thread(...)`), para que `GET /health/live` responda de inmediato aunque haya varias consultas en marcha. No hay pagos, email ni otros servicios externos.

## API REST

**Solo estos endpoints** (no se crean otros: ver IN-01 e IN-02):

| Método | Ruta | Cuerpo | Respuesta | Códigos |
|---|---|---|---|---|
| GET | `/health/live` | — | `{"estado": "vivo"}` | 200 |
| GET | `/health/ready` | — | estado de la base | 200, 503 |
| POST | `/duenios/` | `DuenioCreate` | `DuenioRead` | 201, 409, 422 |
| GET | `/duenios/{id}` | — | dueño con su ficha | 200, 404, 422 |
| PATCH | `/duenios/{id}` | `DuenioUpdate` | dueño con su ficha | 200, 404, 409, 422 |
| DELETE | `/duenios/{id}` | — | — | 204, 404, 409 |
| POST | `/duenios/{id}/ficha` | `FichaCreate` | `FichaRead` | 201, 404, 409 |
| GET | `/duenios/{id}/mascotas` | — | mascotas del dueño | 200, 404 |
| POST | `/mascotas/` | `MascotaCreate` | `MascotaRead` | 201, 409, 422 |
| GET | `/mascotas/` | `page`, `size` | envoltorio con mascotas | 200, 422 |
| GET | `/mascotas/{id}` | — | mascota con su dueño | 200, 404 |
| POST | `/practicas/` | `PracticaCreate` | `PracticaRead` | 201, 409, 422 |
| GET | `/practicas/` | — | catálogo de prácticas | 200 |
| POST | `/turnos/` | `TurnoCreate` con `practicas` | turno con mascota y prácticas | 201, 409, 422 |
| GET | `/turnos/{id}` | — | turno con mascota y prácticas | 200, 404 |
| DELETE | `/turnos/{id}` | — | — | 204, 404 |
| GET | `/laboratorio/stock/{vacuna}` | — | `{"vacuna": ..., "stock": ...}` | 200 |

Códigos: **201** al crear, **204** al borrar, **404** si no existe, **409** si la base rechaza la escritura, **422** si cuerpo o parámetros no cumplen el contrato.

### Envoltorio de paginación

`GET /mascotas/?page=&size=` responde:

```json
{ "items": [ ... ], "total": 0, "page": 1, "size": 20, "pages": 0 }
```

- `size` vale **20** por defecto y va de **1 a 100**.
- Una página **más allá de `pages`** responde **422**.
- **La primera página siempre responde**, aunque no haya resultados.

### Ejemplo de alta de turno (de la consigna)

Cuerpo (no viajan precios ni total):

```json
{"mascota_id": 1, "fecha": "2026-11-12T10:30:00-03:00", "motivo": "Control anual", "practicas": [{"practica_id": 1}, {"practica_id": 3}]}
```

Respuesta esperada:

```json
{"id": 2, "fecha": "2026-11-12T13:30:00Z", "motivo": "Control anual", "total": "27000.00",
 "mascota": {"id": 1, "nombre": "Toby", "especie": "perro"},
 "practicas": [
   {"practica_id": 1, "nombre": "Consulta", "precio_unitario": "15000.00"},
   {"practica_id": 3, "nombre": "Vacuna antirrábica", "precio_unitario": "12000.00"}
 ]}
```

## Principios de diseño

- Las garantías (FK, UNIQUE, CHECK) las da **la base**; el `service` traduce `IntegrityError` → rollback → 409 con mensaje propio.
- Lecturas con **carga anticipada** declarada en la misma consulta; nunca carga perezosa.
- Dinero siempre `Decimal`.

## Requisitos no funcionales (los que enuncia la consigna)

- La app **levanta** y crea su esquema con `python reiniciar.py` sobre una base **vacía**.
- Ningún handler ejecuta llamadas bloqueantes.
- Sin credenciales reales en el repo (descalifica la corrección hasta subsanarlo).
- Entrega: código, `requirements.txt`, `env.example`, `reiniciar.py`, carpeta `test/`, `README.md` y la evidencia del caso C-07.
