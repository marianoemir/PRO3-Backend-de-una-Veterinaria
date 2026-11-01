# Design — laboratorio-sin-bloqueo

## Context

Ver `proposal.md` — Why. El router del laboratorio ya está registrado en `app/main.py` desde la fundación (`[01]`) como `APIRouter()` vacío; este change solo le da contenido. No hay base de datos involucrada: `laboratorio` no tiene tablas (scope `[08]`, `models.py` queda vacío por diseño). La única integración externa del proyecto es la biblioteca sincrónica de la cátedra (`app/modules/laboratorio/cliente.py`), que hace `time.sleep(1)` y **no se modifica** (RN-18, SU-01, DD-15).

Restricciones vigentes que este diseño respeta:
- Todos los handlers `async def` (RN-17).
- Ningún handler ejecuta llamadas bloqueantes; la biblioteca sincrónica se invoca fuera del bucle de eventos (RN-18).
- `GET /health/live` no toca la base y debe responder de inmediato aunque haya consultas al laboratorio en curso (RN-19, RN-22).
- Solo los endpoints listados en `knowledge-base/02_descripcion_general.md` (IN-01/IN-02): acá, únicamente `GET /laboratorio/stock/{vacuna}`.
- `cliente.py` se crea con el código **exacto** del enunciado y **nunca** se modifica (regla dura del proyecto).

## Goals / Non-Goals

**Goals:**
- Exponer `GET /laboratorio/stock/{vacuna}` → 200 `{"vacuna": ..., "stock": ...}` con handler `async def`.
- Invocar `consultar_stock` fuera del event loop, de modo que `GET /health/live` responda de inmediato con consultas en curso (verificable con el smoke de concurrencia, caso C-09).
- Mantener `models.py` y `schemas.py` vacíos (sin tablas ni DTO: el laboratorio no persiste nada y no hay entidad que validar).
- Crear `cliente.py` con el código **byte a byte** del enunciado.

**Non-Goals:**
- No se agregan DTOs, modelos ni validaciones (no hay entidad laboratorio).
- No se toca `app/main.py`, `app/core/*`, `reiniciar.py`, ni ningún otro módulo.
- No se implementan `POST/PATCH/DELETE` ni ningún otro endpoint del laboratorio.
- No se añaden dependencias a `requirements.txt` (`asyncio` es estándar).
- No se escriben casos `.http`/`.sql` ni evidencia (change `[10]`).

## Decisions

### D-01 — Offloading de la llamada bloqueante con `asyncio.to_thread`

**Decisión**: el `service` invoca la biblioteca sincrónica con `await asyncio.to_thread(consultar_stock, vacuna)`.

**Contexto**: `consultar_stock` hace `time.sleep(1)`; llamarla directamente dentro de un handler `async def` bloquearía el event loop de uvicorn y haría que `GET /health/live` espere ~1 s por consulta, fallando RN-19 y el caso C-09.

**Alternativas consideradas**:
- Llamar `consultar_stock(vacuna)` directamente en el handler: descartada (viola RN-18 y bloquea el loop).
- `loop.run_in_executor(None, consultar_stock, vacuna)`: equivalente funcionalmente; se descarta por ser más verboso y por no aportar nada sobre `asyncio.to_thread` (SU-01 lo menciona como opción válida).
- Threadpool de Starlette (`run_in_threadpool`): equivalente; se descarta por consistencia con SU-01 y por ser la forma canónica en Python 3.9+.

**Justificación**: `asyncio.to_thread` es la forma estándar de Python 3.9+ para ejecutar una función síncrona en un hilo del pool por defecto, sin bloquear el event loop. Satisface RN-18 y RN-19 con el mínimo de código.

**Trade-off aceptado**: se usa un hilo por consulta; con tres consultas simultáneas habrá tres hilos viviendo ~1 s cada uno. Es aceptable para el TP y es exactamente lo que el caso C-09 quiere medir.

### D-02 — `cliente.py` con el código exacto de la cátedra, sin modificar

**Decisión**: `app/modules/laboratorio/cliente.py` se crea con el código **exacto** del enunciado y **nunca** se edita:

```python
import time

def consultar_stock(vacuna: str) -> int:
    """Biblioteca del laboratorio: sincrónica, tarda un segundo."""
    time.sleep(1)
    return 10 + len(vacuna)
```

**Contexto**: la consigna entrega esta biblioteca "sin modificarla" (02_descripcion_general.md §Integraciones externas, RN-18). Es código de la cátedra: el evaluador puede compararla byte a byte.

**Justificación**: cualquier cambio (incluso un `async`, un `await` o un `return` distinto) rompería el contrato del caso C-09 y la regla dura del proyecto. El offloading se hace en `service.py`, no en `cliente.py`.

**Verificación**: comparar el archivo resultante con el bloque de arriba por hash/diff; si difiere, es un defecto.

### D-03 — Sin `models.py` ni `schemas.py` (vacíos por diseño)

**Decisión**: `models.py` y `schemas.py` permanecen vacíos (0 bytes), como los dejó la fundación.

**Contexto**: el laboratorio no persiste nada: no hay tabla `laboratorio` en el ERD (`04_modelo_de_datos.md`, solo 6 tablas) ni entidad que validar. El endpoint recibe `vacuna` como path param (`str`) y devuelve un dict simple; no hay DTO que definir (RN-10 no aplica por ausencia de entidad).

**Alternativa considerada**: crear un `LaboratorioRead` con `vacuna` y `stock`. Descartada: agregaría un DTO sin entidad asociada, violando el espíritu de RN-10 ("DTO separado de los modelos de tabla") y el alcance mínimo del change. El contrato del endpoint es un dict fijo `{"vacuna", "stock"}`.

**Justificación**: mínimo indispensable; el alcance del change (`[08]`) es explícito: `cliente.py`, `service.py`, `router.py`.

### D-04 — Router con prefix `/laboratorio` y handler `async def`

**Decisión**: `app/modules/laboratorio/router.py` define `APIRouter(prefix="/laboratorio", tags=["laboratorio"])` y un único endpoint:

```python
@router.get("/stock/{vacuna}")
async def consultar_stock_endpoint(vacuna: str) -> dict:
    return await consultar_stock_service(vacuna)
```

**Contexto**: el endpoint listado es `GET /laboratorio/stock/{vacuna}` (02_descripcion_general.md §API REST). Los demás routers del proyecto (health) usan `prefix` en el propio `APIRouter`; acá se replica el patrón para que `app/main.py` no cambie.

**Justificación**: mantener el prefix en el router permite que `app/main.py` siga incluyendo el router sin argumentos (ya está así desde la fundación), respetando que `main.py` es archivo compartido de Mariano y no se toca.

### D-05 — `service.py` como única capa de lógica

**Decisión**: `service.py` expone una función asincrónica `consultar_stock_service(vacuna: str) -> dict` que hace `stock = await asyncio.to_thread(consultar_stock, vacuna)` y devuelve `{"vacuna": vacuna, "stock": stock}`. El router solo delega.

**Contexto**: la arquitectura por capas del proyecto (02_descripcion_general.md §Arquitectura general) reserva la lógica al `service.py`, que recibe la sesión como parámetro cuando aplica. Acá no hay sesión (sin base), así que el service no recibe parámetros de sesión.

**Justificación**: mantiene el patrón del proyecto (router delega, service contiene la lógica) y deja el offloading en un único lugar, testeable.

### D-06 — Tipo de retorno `dict` (sin DTO)

**Decisión**: el endpoint devuelve `dict` (FastAPI lo serializa a JSON) con las claves `vacuna` (str) y `stock` (int). No se define un `BaseModel`.

**Contexto**: el contrato del endpoint es fijo `{"vacuna": ..., "stock": ...}` (US-017, 02_descripcion_general.md). No hay entidad ni validación de entrada más allá del path param `str`.

**Justificación**: evitar un DTO vacío de propósito; el contrato es trivial y estable. Si en el futuro se agregaran campos, se introduciría un DTO en un change posterior.

## UI Mockups

No aplica: este change es puramente backend (sin páginas, pantallas, componentes ni estilos). `Decision: no (no UI)`.

## Risks / Trade-offs

- **[Riesgo] Llamada bloqueante directa en el handler** → Mitigación: D-01 obliga `asyncio.to_thread`; el smoke de concurrencia (3 consultas + `GET /health/live`) lo verifica; si health tarda ~1 s, hay un defecto.
- **[Riesgo] Modificación accidental de `cliente.py`** → Mitigación: D-02 lo deja byte a byte del enunciado; verificación por hash/diff contra el bloque de arriba.
- **[Riesgo] `vacuna` con caracteres especiales en el path** → Mitigación: FastAPI decodifica el path param; `len()` de Python cuenta caracteres (code points), que es lo que `consultar_stock` usa. Se cubre con el escenario de la spec.
- **[Trade-off] Un hilo por consulta simultánea** → Aceptado: ver D-01.
- **[Trade-off] Sin DTO ni modelo** → Aceptado: ver D-03/D-06; el contrato es fijo y trivial.

## Migration Plan

No aplica: no hay base de datos, migraciones ni cambios de esquema. El change solo agrega comportamiento a un router ya registrado. Rollback = revertir los tres archivos a su estado vacío previo (stubs).

## Open Questions

Ninguna. Todos los puntos relevantes están resueltos por la consigna (US-017, RN-17/18/19) y por las decisiones del equipo (SU-01, DD-15). No hay preguntas abiertas de prioridad Alta/Media que afecten este change.