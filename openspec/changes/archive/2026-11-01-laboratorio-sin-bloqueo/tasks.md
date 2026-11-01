# Tasks — laboratorio-sin-bloqueo

## 1. Biblioteca del laboratorio (código exacto de la cátedra)

- [x] 1.1 Crear `app/modules/laboratorio/cliente.py` con el código exacto del enunciado (`import time`, `consultar_stock(vacuna: str) -> int`, `time.sleep(1)`, `return 10 + len(vacuna)`) y verificar que el archivo coincide byte a byte con el bloque de `design.md` §D-02 (diff/hash idéntico; cualquier diferencia es defecto).

## 2. Servicio (offloading fuera del event loop)

- [x] 2.1 Implementar `app/modules/laboratorio/service.py` con una función asincrónica `consultar_stock_service(vacuna: str) -> dict` que ejecute `await asyncio.to_thread(consultar_stock, vacuna)` e importe `consultar_stock` desde `.cliente`, y verificar con `python -c "import asyncio, inspect; from app.modules.laboratorio import service; print(inspect.iscoroutinefunction(service.consultar_stock_service))"` que es `True`.
- [x] 2.2 Verificar el contrato del servicio: con la app levantada, `python -c` o un request manual a `GET /laboratorio/stock/rabia` devuelve `{"vacuna": "rabia", "stock": 15}` (smoke HTTP: `curl http://127.0.0.1:8000/laboratorio/stock/rabia` → 200 con ese cuerpo).

## 3. Router (endpoint único)

- [x] 3.1 Implementar `app/modules/laboratorio/router.py` con `APIRouter(prefix="/laboratorio", tags=["laboratorio"])` y `@router.get("/stock/{vacuna}")` con handler `async def` que delega en `consultar_stock_service`, y verificar que `GET /openapi.json` lista la ruta `/laboratorio/stock/{vacuna}` con método `GET` y respuesta 200.
- [x] 3.2 Verificar que `models.py` y `schemas.py` permanecen vacíos (0 bytes) y que no se modificó `app/main.py` (diff contra `main` previo: solo los tres archivos del módulo laboratorio cambian).

## 4. Verificación de no bloqueo (smoke de concurrencia, caso C-09)

- [x] 4.1 Con la app levantada (`uvicorn app.main:app`), lanzar tres solicitudes simultáneas a `GET /laboratorio/stock/{vacuna}` (por ejemplo con `curl` en paralelo o un script `asyncio`/`httpx`) y, mientras están en curso, solicitar `GET /health/live`; verificar que `/health/live` responde `200 {"estado": "vivo"}` de inmediato (latencia ≪ 1 s) y que las tres consultas al laboratorio terminan con `200` y su `stock` correspondiente. Anotar las latencias para el caso C-09 (change `[10]`).
- [x] 4.2 Verificar el caso borde de la spec: `GET /laboratorio/stock/vacuna%20antirrabica` responde `200` con `{"vacuna": "vacuna antirrabica", "stock": 28}` (request HTTP esperado).

## Workflow follow-up

- Archivar el change (`/opsx:archive laboratorio-sin-bloqueo`) tras la revisión y marcar `[x]` solo la línea `[08]` en `CHANGES.md`.
- Verificar el resultado archivado.