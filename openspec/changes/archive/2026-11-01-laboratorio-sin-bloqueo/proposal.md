# Propuesta: laboratorio-sin-bloqueo

## Why

El módulo `laboratorio` existe como stub desde la fundación (`[01]`): `app/modules/laboratorio/router.py` es un `APIRouter()` vacío y `service.py`, `schemas.py` y `models.py` están vacíos. La cátedra entrega una biblioteca sincrónica (`app/modules/laboratorio/cliente.py`, con `time.sleep(1)`) que **no se puede modificar** y que el servicio debe invocar **sin bloquear el event loop** (US-017, RN-18, RN-19). Hoy no hay ningún endpoint que consulte el stock de una vacuna, y si se llamara directamente la función bloqueante desde un handler `async def`, el `GET /health/live` quedaría bloqueado ~1 segundo por consulta, haciendo fallar el caso C-09. Este change cierra esa brecha: expone `GET /laboratorio/stock/{vacuna}` y garantiza que las consultas concurrentes no detengan el servicio.

## What Changes

- **Se crea `app/modules/laboratorio/cliente.py`** con el código **exacto** que entrega la cátedra (`consultar_stock(vacuna: str) -> int` con `time.sleep(1)`), **sin modificarlo jamás** (SU-01, DD-15). Es el único archivo del módulo que la cátedra provee; el resto lo escribimos nosotros.
- **Se implementa `app/modules/laboratorio/service.py`**: una función asincrónica que ejecuta `consultar_stock` fuera del bucle de eventos con `await asyncio.to_thread(consultar_stock, vacuna)` (o equivalente del threadpool), y arma la respuesta `{"vacuna": ..., "stock": ...}`.
- **Se implementa `app/modules/laboratorio/router.py`**: `APIRouter(prefix="/laboratorio", tags=["laboratorio"])` con `GET /stock/{vacuna}` → 200 `{"vacuna": ..., "stock": ...}`, handler `async def`. Sin DTOs ni modelos: `laboratorio` no tiene tablas en la base (scope de `[08]`).
- **`models.py` y `schemas.py` permanecen vacíos** por diseño: el laboratorio no persiste nada; no hay tablas ni DTOs que validar (RN-10 no aplica por ausencia de entidad).
- **Sin cambios en `app/main.py`**: el router del laboratorio ya está incluido desde la fundación; solo se le da contenido (no se toca el archivo compartido, dueño Mariano).

**BREAKING**: ninguno. El router ya estaba registrado como vacío; este change solo le da comportamiento.

## Capabilities

### New Capabilities

- `laboratorio`: consulta de stock de una vacuna en el laboratorio externo sin bloquear el event loop; invoca la biblioteca sincrónica de la cátedra fuera del bucle y responde `{"vacuna", "stock"}`.

### Modified Capabilities

Ninguna. `fundacion` describe el arranque de la API y el router vacío del laboratorio; este change **no cambia** sus requisitos, solo materializa el comportamiento del endpoint que la tabla de endpoints de `02_descripcion_general.md` ya prometía. No se tocan sus specs ni escenarios.

## Alcance

| ¿Qué incluye? | ¿Qué queda fuera? |
|---|---|
| `app/modules/laboratorio/cliente.py` con el código **exacto** de la cátedra, sin modificar | Cualquier otro módulo: `app/modules/{health,duenios,mascotas,practicas,turnos}/*` |
| `app/modules/laboratorio/service.py` con `asyncio.to_thread` | `app/main.py`, `app/core/{config,database}.py` (archivos compartidos de Mariano) |
| `app/modules/laboratorio/router.py` con `GET /laboratorio/stock/{vacuna}` | `reiniciar.py`, `test/**`, `README.md` (changes `[09]`, `[10]`, `[11]`) |
| `models.py` y `schemas.py` vacíos (por diseño, sin tablas ni DTO) | Migraciones (Alembic), auth, repositorios, colas, Docker, CI (fuera de alcance global) |
| Smoke de concurrencia: 3 consultas simultáneas + `GET /health/live` en el medio | Casos `.http`/`.sql` y evidencia (change `[10]`) |

El alcance de archivos es **literal**: este change toca **solo** `app/modules/laboratorio/{cliente,service,router}.py`. Si aparece la tentación de agregar un DTO o un modelo, eso es un cambio de alcance y va por otro change.

## Reglas de negocio cubiertas

- **RN-17** — todos los handlers son `async def`: el handler de `GET /laboratorio/stock/{vacuna}` es `async def`.
- **RN-18** — ningún handler ejecuta una llamada bloqueante: `consultar_stock` (con `time.sleep(1)`) se ejecuta fuera del bucle de eventos vía `asyncio.to_thread`, sin modificar `cliente.py`.
- **RN-19** — mientras hay consultas al laboratorio en curso, `GET /health/live` responde de inmediato: verificable con el smoke de concurrencia (caso C-09).
- **RN-12** — código de respuesta 200 para la consulta de stock (único endpoint del módulo, listado en `02_descripcion_general.md`).

## Impact

- **Código afectado**: `app/modules/laboratorio/{cliente,service,router}.py` (los tres nuevos/llenados). `models.py` y `schemas.py` quedan vacíos por diseño. `app/main.py` no se toca (el router ya estaba incluido).
- **Base de datos**: ninguna. `laboratorio` no tiene tablas; `reiniciar.py` no cambia.
- **APIs**: se materializa `GET /laboratorio/stock/{vacuna}` → 200 `{"vacuna": ..., "stock": ...}`, ya listado en la tabla de endpoints de `02_descripcion_general.md` (IN-01/IN-02 respetados: no se crea ningún endpoint no listado).
- **Dependencias**: ninguna nueva. `asyncio` es de la librería estándar; no se agrega nada a `requirements.txt`.
- **Changes que desbloquea**: `[10] pruebas-http-y-evidencia` (caso C-09) y, a través de él, `[11] readme-y-entrega`.
- **Riesgo principal**: que la función sincrónica se invoque directamente dentro del handler y bloquee el event loop (riesgo declarado en **SU-01**). Se ataca en `design.md` (offloading con `asyncio.to_thread`) y se verifica con el smoke de concurrencia.
- **Riesgo secundario**: modificar `cliente.py` por error (regla dura: **nunca**). El código se copia **byte a byte** y se verifica por hash/diff contra el enunciado.