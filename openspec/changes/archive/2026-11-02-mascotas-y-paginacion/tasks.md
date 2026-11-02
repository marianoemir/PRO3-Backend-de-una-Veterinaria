# Tareas: mascotas-y-paginacion

> Dueño: **Facundo**. Duración estimada total: **7–8 h**. Dependencias: `02` `modelos-y-esquema` y `03` `duenios-y-ficha` (ambos archivados).
> Alcance: **solo `app/modules/mascotas/{schemas,service,router}.py`**. No se toca `models.py`, `app/modules/duenios/*`, `app/main.py`, `reiniciar.py`, `test/**`, `README.md` ni `CHANGES.md`.

## Notas previas (leer antes de empezar)

- **La base debe estar poblada**: correr `python reiniciar.py` ([09]) antes de levantar la app. El seed deja dueño 1 = **Ana Gómez**, dueño 2 = **Bruno Díaz** y tres mascotas: `1` = **Toby** (perro, dueño 1), `2` = **Michi** (gato, dueño 1), `3` = **Rocco** (perro, dueño 2).
- **`app/main.py` ya registra el router** de `mascotas` ([01]); no se edita. El router declara su propio `prefix="/mascotas"`.
- **Sin `psql`**: se verifica con `uvicorn app.main:app` + peticiones HTTP (curl o un `.http` temporal **fuera del repo**, por ejemplo en `%TEMP%`) y consultas en pgAdmin. **No** se crea ningún archivo bajo `test/` (eso es [10]).
- **TDD**: cada tarea de código sigue **RED → GREEN → TRIANGULATE** con peticiones HTTP reales. El RED se observa antes de escribir el endpoint (404/405 porque la ruta no existe); el GREEN es la petición con el código esperado; el TRIANGULATE agrega los bordes (conflicto, parámetros inválidos, base vacía). La consola de `uvicorn` trae `echo=True`: sirve como evidencia del número de consultas.
- Comandos de ejemplo: `curl.exe -s -w "\n%{http_code}\n" http://localhost:8000/mascotas/` (PowerShell, JSON entre comillas simples). Los `{id}` se reemplazan por el id devuelto.

## 1. Preparación y RED de partida

- [x] **1.1 — Verificar dependencias, estado de partida y línea base** *(25 min)*
  - Comprobar que `[02]` y `[03]` están archivados, que `app/modules/mascotas/models.py` no cambia y que `schemas.py`/`service.py` están vacíos y `router.py` solo declara `APIRouter()`.
  - Levantar `python reiniciar.py` y `uvicorn app.main:app`.
  - **Verificación**: `GET /openapi.json` → **200** y **no** contiene ninguna ruta `/mascotas`; `GET /mascotas/` → **404** (RED de partida) y `GET /mascotas/1` → **404**. SQL en pgAdmin: `SELECT count(*) FROM mascota` = **3** y `SELECT id, nombre, especie, duenio_id FROM mascota ORDER BY id` devuelve Toby/1/perro/1, Michi/2/gato/1, Rocco/3/perro/2.

## 2. DTOs del módulo

- [x] **2.1 — `MascotaCreate`, `DuenioResumenRead`, `MascotaRead` y `PaginaMascotasRead`** *(30 min)*
  - `MascotaCreate`: `nombre`, `especie` (`min_length=1`, DD-12) y `duenio_id`; **sin `id`** (RN-10). `DuenioResumenRead`: `id`, `nombre` con `ConfigDict(from_attributes=True)`. `MascotaRead`: `id`, `nombre`, `especie`, `duenio: DuenioResumenRead` con `from_attributes`. `PaginaMascotasRead`: `items: list[MascotaRead]`, `total`, `page`, `size`, `pages`. El archivo **no** importa DTO de `duenios` (RN-10).
  - **Verificación**: `python -c "from app.modules.mascotas.schemas import MascotaCreate, MascotaRead, PaginaMascotasRead; d = MascotaCreate(nombre='X', especie='gato', duenio_id=1, id=999); assert not hasattr(d, 'id'); print(PaginaMascotasRead(items=[], total=0, page=1, size=20, pages=0).model_dump())"` imprime `{'items': [], 'total': 0, 'page': 1, 'size': 20, 'pages': 0}` sin error; `grep -n "duenios" app/modules/mascotas/schemas.py` no encuentra imports de `app.modules.duenios`.

## 3. Alta de mascota

- [x] **3.1 — `crear_mascota` + `POST /mascotas/` (GREEN del camino feliz)** *(50 min)*
  - Service: bloque de imports de `design.md` §9 (incluye `import app.modules.duenios.models` y `import app.modules.turnos.models` con `noqa: F401` para registrar los mappers de `Mascota.duenio` y `Mascota.turnos`). `Mascota(nombre=..., especie=..., duenio_id=...)` + `add` + `commit`; `IntegrityError` → `rollback()` → `HTTPException(409, "No existe un dueño con ese id")`, **sin `SELECT` previo** (DD-03). Después del `commit`, re-lectura `select(Mascota).options(joinedload(Mascota.duenio)).where(Mascota.id == mascota.id).execution_options(populate_existing=True)` para armar la respuesta (design §3). Router: `@router.post("/", response_model=MascotaRead, status_code=201)` con handler `async def`.
  - **Verificación**: `curl.exe -s -w "\n%{http_code}\n" -X POST http://localhost:8000/mascotas/ -H "Content-Type: application/json" -d '{"nombre":"Luna","especie":"gato","duenio_id":1}'` → **201** con `id`, `nombre`, `especie` y `"duenio": {"id": 1, "nombre": "Ana Gómez"}`; SQL `SELECT count(*) FROM mascota WHERE nombre='Luna'` = **1**; en la consola aparece el `INSERT` y **un** `SELECT` con `JOIN` a `duenio`, sin `MissingGreenlet`.

- [x] **3.2 — Triangular el alta: dueño inexistente, sin `SELECT` previo** *(35 min)*
  - Caso de negocio de la spec (C-04 de [10]).
  - **Verificación**: `POST /mascotas/` con `{"nombre":"Fantasma","especie":"perro","duenio_id":99999}` → **409** con mensaje propio; SQL `SELECT count(*) FROM mascota WHERE nombre='Fantasma'` = **0** y `SELECT count(*) FROM mascota` sigue en **4**; en la consola del 409 aparece el `INSERT` rechazado y su `ROLLBACK`, y **ningún** `SELECT ... FROM duenio WHERE id =` (evidencia de DD-03); inmediatamente después, un alta válida con `duenio_id: 2` → **201** (la sesión se recuperó con `rollback()`).

- [x] **3.3 — Triangular el alta: contrato del cuerpo e `id` del cliente** *(25 min)*
  - **Verificación**: `POST /mascotas/` sin `duenio_id` → **422**; con `"especie": ""` → **422**; con `"duenio_id": "abc"` → **422**; en los tres casos `SELECT count(*) FROM mascota` no cambia. `POST /mascotas/` con `{"id":999,"nombre":"Caro","especie":"gato","duenio_id":1}` → **201** con `id != 999` y SQL `SELECT count(*) FROM mascota WHERE id=999` = **0**.

## 4. Detalle de mascota con su dueño

- [x] **4.1 — `obtener_mascota` + `GET /mascotas/{id}`** *(35 min)*
  - Service: `select(Mascota).options(joinedload(Mascota.duenio)).where(Mascota.id == mascota_id)`; `None` → el router responde **404** con mensaje propio (RN-14, RN-15). Router: `@router.get("/{mascota_id}", response_model=MascotaRead)` con `mascota_id: int` (RN-17).
  - **Verificación**: `GET /mascotas/1` → **200** con `{"id":1,"nombre":"Toby","especie":"perro","duenio":{"id":1,"nombre":"Ana Gómez"}}`; `GET /mascotas/3` → **200** con `"duenio": {"id": 2, "nombre": "Bruno Díaz"}`; `GET /mascotas/99999` → **404** con mensaje propio; `GET /mascotas/abc` → **422**.

- [x] **4.2 — Triangular el detalle: una sola consulta y sin carga perezosa** *(20 min)*
  - **Verificación**: con la consola de `uvicorn` a la vista, `GET /mascotas/1` y `GET /mascotas/3` emiten **un solo `SELECT`** con `JOIN` a `duenio` cada uno; ninguna petición falla con `MissingGreenlet`; `GET /mascotas/abc` no genera ninguna sentencia SQL (el 422 ocurre antes del handler); SQL `SELECT count(*) FROM mascota` no cambia.

## 5. Listado paginado

> **Antes de 5.1**: correr `python reiniciar.py` y volver a levantar la app. Los grupos 3.x dejan mascotas extra (Luna, la del dueño 2 y Caro), así que 5.1 y 5.2 solo cuadran `total: 3` y la composición Toby/Michi/Rocco partiendo del seed.

- [x] **5.1 — `listar_mascotas` + `GET /mascotas/?page=&size=` (GREEN con defaults)** *(50 min)*
  - Service: `total = select(func.count()).select_from(Mascota)`; `pages = ceil(total/size) if total else 0`; `page > 1 and page > pages` → `HTTPException(422, "La página solicitada no existe")`; página con `select(Mascota).options(joinedload(Mascota.duenio)).order_by(Mascota.id).offset((page-1)*size).limit(size)`. Router: `page: int = Query(1, ge=1)`, `size: int = Query(20, ge=1, le=100)`, `response_model=PaginaMascotasRead`.
  - **Verificación**: `GET /mascotas/` → **200** con `"page": 1`, `"size": 20`, `"total": 3`, `"pages": 1` y `items` con Toby, Michi y Rocco en ese orden, cada uno con su `duenio` resumido; `GET /mascotas/?page=2&size=2` → **200** con `total: 3`, `pages: 2` e `items` con un solo elemento (Rocco, `id 3`); SQL `SELECT count(*) FROM mascota` = **3**.

- [x] **5.2 — Triangular el listado: `size` fuera de rango y `page` fuera de contrato** *(30 min)*
  - **Verificación**: `GET /mascotas/?size=0` → **422**; `GET /mascotas/?size=101` → **422**; `GET /mascotas/?size=-1` → **422**; `GET /mascotas/?page=0` → **422**; `GET /mascotas/?page=-1` → **422**; ninguna de esas peticiones emite un `SELECT` sobre `mascota` en la consola (el 422 lo produce FastAPI antes del handler); `GET /mascotas/?size=100` → **200** con `size: 100` y `total: 3`.

- [x] **5.3 — Triangular el listado: página más allá de `pages` y base vacía** *(40 min)*
  - Casos borde de RN-13.
  - **Verificación (a)**: `GET /mascotas/?page=99&size=20` sobre la base con 3 mascotas (`pages = 1`) → **422** con mensaje propio, y el cuerpo **no** es un envoltorio con `items: []`; SQL `SELECT count(*) FROM mascota` = **3**.
  - **Verificación (b, base vacía)**: en pgAdmin `DELETE FROM turno;` y después `DELETE FROM mascota;` (el turno del seed referencia a Toby: primero el turno, que arrastra `turno_practica` por `ON DELETE CASCADE`), y luego `GET /mascotas/` → **200** con `"items": []`, `"total": 0`, `"page": 1`, `"size": 20` y `"pages": 0` (no 422); `GET /mascotas/?page=2` → **422**. Al terminar, `python reiniciar.py` para dejar la base como estaba y confirmar por SQL `SELECT count(*) FROM mascota` = **3**.

- [x] **5.4 — Triangular el listado: dos consultas fijas** *(25 min)*
  - **Verificación**: con la consola a la vista, `GET /mascotas/` y `GET /mascotas/?page=2&size=2` emiten **exactamente dos `SELECT`** cada uno: un `COUNT` y un `SELECT` de la página con `JOIN` a `duenio`; repetir `GET /mascotas/?size=1` sobre la misma base sigue dando dos consultas (no crece con la cantidad de elementos ni con la cantidad de filas, RN-15); insertar por SQL dos mascotas extra (`INSERT INTO mascota (nombre, especie, duenio_id) VALUES ('Kira','perro',2), ('Nala','gato',2);`) y repetir `GET /mascotas/` → sigue en **dos consultas** y `total` pasa a **5**; después `python reiniciar.py`.

## 6. Contrato de rutas acotado

- [x] **6.1 — Verificar que solo existen los tres endpoints listados** *(20 min)*
  - **Verificación**: `GET /openapi.json` lista exactamente `POST /mascotas/`, `GET /mascotas/` y `GET /mascotas/{mascota_id}`; `curl.exe -s -o NUL -w "%{http_code}\n" -X DELETE http://localhost:8000/mascotas/1` → **405** y SQL `SELECT count(*) FROM mascota WHERE id=1` = **1**; `curl.exe -s -o NUL -w "%{http_code}\n" -X PATCH http://localhost:8000/mascotas/1 -H "Content-Type: application/json" -d '{"nombre":"X"}'` → **405**; no hay rutas `GET /mascotas/duenio/...` ni filtros por dueño.

## 7. Smoke de integración

- [x] **7.1 — Smoke completo del change** *(50 min)*
  - Con `python reiniciar.py` y `uvicorn app.main:app` levantados, ejecutar en orden (curl o `.http` temporal fuera del repo):
    1. `POST /mascotas/` con `{"nombre":"Luna","especie":"gato","duenio_id":1}` → **201** con `duenio.id = 1`.
    2. `POST /mascotas/` con `{"nombre":"Fantasma","especie":"perro","duenio_id":99999}` → **409**.
    3. `POST /mascotas/` sin `especie` → **422**.
    4. `GET /mascotas/1` → **200** con `duenio` resumido.
    5. `GET /mascotas/99999` → **404**.
    6. `GET /mascotas/` → **200** con `total: 4` y `pages: 1` (3 del seed + Luna).
    7. `GET /mascotas/?size=0` → **422**; `GET /mascotas/?size=101` → **422**.
    8. `GET /mascotas/?page=2&size=3` → **200** con `pages: 2` e `items` con un elemento (Luna).
    9. `GET /mascotas/?page=99` → **422**.
    10. `DELETE /mascotas/1` → **405**.
  - **Verificación**: los diez códigos coinciden con los esperados; al final SQL `SELECT count(*) FROM mascota` = **4** y `SELECT count(*) FROM mascota WHERE duenio_id=99999` = **0**. Guardar la salida de la consola como referencia para [10]; **no** se escribe en `test/`.

- [x] **7.2 — Regresión y contrato del módulo** *(25 min)*
  - Correr `python reiniciar.py` dos veces seguidas y volver a levantar la app.
  - **Verificación**: `GET /mascotas/` → **200** con `total: 3` y `pages: 1`; `GET /duenios/1/mascotas` (change [03]) → **200** con Toby y Michi, sin cambios de forma; si el change [07] está en `main`, `GET /turnos/1` → **200** con su mascota (si [07] no está mergeado, omitir esta línea y no contarla como fallo), para confirmar que el nuevo service no rompió los mappers compartidos; sin `MissingGreenlet` ni `InvalidRequestError` en la consola.

## Workflow follow-up

- Archivar el change con `/opsx:archive mascotas-y-paginacion` y marcar `[x]` **solo** la línea `[05]` de `CHANGES.md`, una vez revisado y mergeado.
- Avisar a Andrés ([10] `pruebas-http-y-evidencia`) que el caso C-04 (mascota con dueño inexistente → 409) y la verificación de paginación ya se pueden escribir, con la salida del smoke de 7.1 como referencia.
- Mencionar en el README ([11]) la decisión propia de `page` 1-based y el 409 por violación de FK, junto con DD-08 a DD-15.
