# Tareas: duenios-y-ficha

> Dueño: **Facundo**. Duración estimada total: **9–10 h**. Dependencias: `02` `modelos-y-esquema` (archivado).
> Alcance: **solo `app/modules/duenios/{schemas,service,router}.py`**. No se toca `models.py`, `app/main.py`, `reiniciar.py`, `test/**`, `README.md` ni `CHANGES.md`.

## Notas previas (leer antes de empezar)

- **La base debe existir** para verificar: correr `python reiniciar.py` (change [09], archivado) antes de levantar la app. El seed deja dos dueños: **dueño 1 = Ana Gómez**, **con ficha** y **dos mascotas** — Toby (`id 1`, perro) y Michi (`id 2`, gato); **dueño 2 = Bruno Díaz**, **sin ficha** y **con una mascota** — Rocco (`id 3`, perro). Ninguno de los dos sirve como caso de lista vacía: para el `[]` y para el 204 de la baja hay que crear un dueño nuevo por API.
- **`app/main.py` ya registra el router** de `duenios` (change [01]); no se edita. El router declara su propio `prefix="/duenios"`.
- **Sin `psql`**: la verificación se hace con `uvicorn app.main:app` + peticiones HTTP (curl o un `.http` temporal **fuera del repo**, por ejemplo en `%TEMP%`) y consultas en pgAdmin. **No** se crea ningún archivo bajo `test/` (eso es [10]) ni un script versionado: si hace falta un script temporal, se guarda fuera del repo y se borra.
- **Strict TDD**: cada tarea de código sigue **RED → GREEN → TRIANGULATE** con peticiones HTTP reales. El RED se observa antes de escribir el endpoint (404/405 porque la ruta no existe); el GREEN es la petición con el código esperado; el TRIANGULATE agrega los bordes (caso vacío, conflicto, id inválido). La consola de `uvicorn` ya trae `echo=True`: sirve como evidencia del número de consultas.

## 1. Preparación

- [x] **1.1 — Verificar dependencias y estado de partida** *(20 min)*
  - Comprobar que `[02]` está archivado y que los tres archivos del módulo son stubs.
  - Levantar la app: `python reiniciar.py` y `uvicorn app.main:app`.
  - **Verificación**: `GET /openapi.json` → **200** y no contiene la ruta `/duenios/`; `GET /duenios/1` → **404** (RED de partida, la ruta todavía no existe). SQL en pgAdmin: `SELECT count(*) FROM duenio` = **2** y `SELECT count(*) FROM ficha_duenio` = **1** (seed de [09]).

## 2. Alta de dueño

- [x] **2.1 — DTOs del alta: `DuenioCreate`, `FichaRead`, `DuenioRead`** *(20 min)*
  - `DuenioCreate`: `nombre: str`, `email: str`, **sin `id`**. `FichaRead`: `id`, `duenio_id`, `telefono`, `direccion` con `from_attributes`. `DuenioRead`: `id`, `nombre`, `email`, `ficha: FichaRead | None` con `from_attributes` (RN-10).
  - **Verificación**: `python -c "from app.modules.duenios.schemas import DuenioCreate, DuenioRead; d = DuenioCreate(nombre='X', email='x@y.com', id=999); assert not hasattr(d, 'id'); print(DuenioRead(id=1, nombre='X', email='x@y.com', ficha=None).model_dump())"` imprime `ficha: None` y no falla; SQL `SELECT count(*) FROM duenio` no cambia (la verificación no escribe).

- [x] **2.2 — `crear_duenio` + `POST /duenios/`** *(45 min)*
  - Service: arranca con el bloque de imports del `design.md` §11 —al estilo de `practicas/service.py`, con `import app.modules.duenios.models  # noqa: F401` e `import app.modules.mascotas.models  # noqa: F401` para registrar los mappers de las relaciones (`Duenio.ficha`, `Duenio.mascotas`), más los imports nominales de `Duenio`, `FichaDuenio` y `Mascota`; los `noqa: F401` son solo para registrar mappers, no para usar esos nombres—. Luego `Duenio(...)` + `add` + `commit`; `IntegrityError` → `rollback()` → `HTTPException(409, "Ya existe un dueño con ese email")`. **Sin `SELECT` previo** (DD-03). Sin `refresh` (decisión 3 del `design.md`).
  - Router: `@router.post("/", response_model=DuenioRead, status_code=201)` con handler `async def` y `Depends(get_session)`.
  - **Verificación**: `POST /duenios/` con `{"nombre":"Ana Smoke","email":"ana@smoke.com"}` → **201** con `id`, `email` y `"ficha": null`; el mismo body otra vez → **409** con mensaje propio; SQL `SELECT count(*) FROM duenio WHERE email='ana@smoke.com'` = **1**.

- [x] **2.3 — Triangular el alta** *(25 min)*
  - Casos borde de la spec: `id` enviado por el cliente, email con distinto casing y sesión reutilizable tras el 409.
  - **Verificación**: `POST /duenios/` con `{"id":999,"nombre":"Caro","email":"caro@smoke.com"}` → **201** con `id ≠ 999` y SQL `SELECT count(*) FROM duenio WHERE id=999` = **0**; `POST /duenios/` con `{"nombre":"Dani","email":"Dani@Smoke.com"}` cuando ya existe `dani@smoke.com` → **201** (DD-09); después de un 409, un alta con email nuevo → **201**; `POST /duenios/` sin `email` → **422** y SQL `SELECT count(*) FROM duenio` no cambia; en la consola del 409 aparece el `INSERT` rechazado y el `ROLLBACK`, y **ningún** `SELECT ... WHERE email =` (evidencia de DD-03).

## 3. Detalle de dueño con su ficha

- [x] **3.1 — `obtener_duenio` + `GET /duenios/{id}`** *(40 min)*
  - Service: una consulta `select(Duenio).options(joinedload(Duenio.ficha)).where(Duenio.id == duenio_id)`; `None` → 404 (RN-14, RN-15).
  - Router: `@router.get("/{duenio_id}", response_model=DuenioRead)` con `duenio_id: int` (RN-17).
  - **Verificación**: `GET /duenios/1` (dueño con ficha del seed) → **200** con `ficha` completa; `GET /duenios/2` (sin ficha) → **200** con `"ficha": null`; `GET /duenios/99999` → **404**; `GET /duenios/abc` → **422**.

- [x] **3.2 — Triangular el detalle y la carga anticipada** *(20 min)*
  - **Verificación**: con la consola de `uvicorn` a la vista, `GET /duenios/1` y `GET /duenios/2` emiten **un solo `SELECT`** de lectura del dueño con `LEFT OUTER JOIN` a `ficha_duenio` en ambos casos (misma cantidad de consultas, RN-15); ninguna petición falla con `MissingGreenlet`; `GET /duenios/abc` no genera ninguna sentencia SQL (el 422 ocurre antes del handler).

## 4. PATCH parcial

- [x] **4.1 — `DuenioUpdate` + `actualizar_duenio` + `PATCH /duenios/{id}`** *(50 min)*
  - DTO: `nombre: str | None = None`, `email: str | None = None` (DD-08). Service: cargar con `joinedload(Duenio.ficha)`, 404 si no existe, aplicar `dto.model_dump(exclude_unset=True)` y `commit()`; `IntegrityError` → `rollback()` → `HTTPException(409, "No se pudo actualizar: email ya registrado o dato inválido")` con ese texto **exacto** (el alta y la ficha conservan sus mensajes propios) (RN-11). Router: `@router.patch("/{duenio_id}", response_model=DuenioRead)`.
  - **Verificación**: `PATCH /duenios/{id}` con `{"nombre":"Ana Actualizada"}` sobre el dueño creado en 2.2 → **200** con el nombre nuevo y el **email igual**; SQL `SELECT nombre, email FROM duenio WHERE id={id}` muestra el nombre nuevo y el email original.

- [x] **4.2 — Triangular el PATCH** *(30 min)*
  - **Verificación**: `PATCH` con `{}` → **200** y SQL `SELECT nombre, email FROM duenio WHERE id={id}` idéntico al anterior; `PATCH` con el email de otro dueño existente → **409** y SQL muestra el email original intacto; `PATCH /duenios/99999` con body válido → **404**; `PATCH` con `{"email":123}` → **422** y SQL sin cambios; después del 409, un `PATCH` válido → **200** (la sesión se recuperó con `rollback()`).

## 5. Baja de dueño

- [x] **5.1 — `borrar_duenio` + `DELETE /duenios/{id}`** *(40 min)*
  - Service: `try:` que envuelve **todo** el bloque — `delete(Duenio).where(...).execution_options(synchronize_session=False)`, el chequeo de `rowcount == 0` → 404 y el `commit()` —; `except IntegrityError` → `rollback()` → 409. El `try` **no** puede empezar en el `commit`: `RESTRICT`/`NO ACTION` se disparan al **ejecutar** el `DELETE`, y un `try` tardío deja escapar el `IntegrityError` sin `rollback()`. **No** usar `session.delete()` (decisión 6 del `design.md`). Router: `@router.delete("/{duenio_id}", status_code=204)` que no devuelve cuerpo.
  - **Verificación**: crear un dueño nuevo por API (`POST /duenios/` con `baja@smoke.com`) y `DELETE /duenios/{id}` → **204** sin cuerpo; SQL `SELECT count(*) FROM duenio WHERE id={id}` = **0**; `DELETE /duenios/99999` → **404**.

- [x] **5.2 — Triangular la baja bloqueada por la base** *(40 min)*
  - **Verificación**: `DELETE /duenios/1` (dueño con mascotas del seed) → **409** con mensaje propio; SQL `SELECT count(*) FROM mascota WHERE duenio_id=1` no cambia y el dueño sigue existiendo; en la consola aparece **un solo `DELETE FROM duenio`** y **ningún** `UPDATE mascota` ni `SELECT ... FROM mascota` previo (evidencia de que decide la base, RN-08); `DELETE` de un dueño con ficha y sin mascotas (creado por API + `POST /duenios/{id}/ficha`) → **409** y SQL `SELECT count(*) FROM ficha_duenio WHERE duenio_id={id}` = **1** (consecuencia de DD-13/IN-03); `DELETE /duenios/abc` → **422**.

## 6. Alta de ficha

- [x] **6.1 — `FichaCreate`/`FichaRead` + `crear_ficha` + `POST /duenios/{id}/ficha`** *(40 min)*
  - DTO: `telefono` y `direccion` obligatorios (DD-12). Service: comprobar que el dueño exista con `select(Duenio.id).where(Duenio.id == duenio_id)` y `scalar_one_or_none() is None` → 404 (**sin** `joinedload` de la ficha); crear `FichaDuenio(duenio_id=..., telefono=..., direccion=...)` y `commit()`; `IntegrityError` → `rollback()` → 409. **No** se inspecciona `duenio.ficha` para decidir el 409 (decisión 7 del `design.md`). Router: `@router.post("/{duenio_id}/ficha", response_model=FichaRead, status_code=201)`.
  - **Verificación**: crear un dueño por API y `POST /duenios/{id}/ficha` con `{"telefono":"1144556677","direccion":"Calle Falsa 123"}` → **201** con `id`, `duenio_id`, `telefono` y `direccion`; SQL `SELECT count(*) FROM ficha_duenio WHERE duenio_id={id}` = **1**; `GET /duenios/{id}` → **200** con esa ficha anidada.

- [x] **6.2 — Triangular la ficha** *(30 min)*
  - **Verificación**: repetir el mismo `POST /duenios/{id}/ficha` → **409** y SQL `SELECT count(*) FROM ficha_duenio WHERE duenio_id={id}` = **1**, con los datos originales; `POST /duenios/99999/ficha` → **404** y SQL `SELECT count(*) FROM ficha_duenio` no cambia; `POST /duenios/{id}/ficha` sin `telefono` → **422** y sin fila nueva; `POST /duenios/{id}/ficha` sin `direccion` → **422**; en la consola del 409 **no** aparece ningún `SELECT ... FROM ficha_duenio WHERE duenio_id =` previo al `INSERT` (evidencia de DD-03/RN-03).

## 7. Mascotas del dueño

- [x] **7.1 — `MascotaResumenRead` + `listar_mascotas_de_duenio` + `GET /duenios/{id}/mascotas`** *(35 min)*
  - DTO propio del módulo: `id`, `nombre`, `especie` (sin importar DTO de `mascotas`). Service: `select(Duenio.id).where(...)` para el 404 y `select(Mascota).where(Mascota.duenio_id == duenio_id).order_by(Mascota.id)`. Router: `@router.get("/{duenio_id}/mascotas", response_model=list[MascotaResumenRead])`.
  - **Verificación**: `GET /duenios/1/mascotas` (Ana Gómez, seed) → **200** con `[{id:1, nombre:"Toby", especie:"perro"}, {id:2, nombre:"Michi", especie:"gato"}]` ordenado por `id`; `GET /duenios/2/mascotas` (Bruno Díaz, seed) → **200** con `[{id:3, nombre:"Rocco", especie:"perro"}]`; el caso de lista vacía se verifica con un dueño **creado por API** (`POST /duenios/` con `vacio@smoke.com`): `GET /duenios/{id}/mascotas` → **200** con `[]`; `GET /duenios/99999/mascotas` → **404**.

- [x] **7.2 — Triangular el listado de mascotas** *(20 min)*
  - **Verificación**: el cuerpo de `GET /duenios/1/mascotas` es un **arreglo JSON**, sin las claves `items`, `total`, `page`, `size` ni `pages` (DD-10); el orden es por `id` ascendente (Toby `1` antes que Michi `2`) y `GET /duenios/2/mascotas` devuelve **solo** Rocco (`id 3`), sin Toby ni Michi (aislamiento entre dueños); el `[]` del dueño creado por API no responde 404; en la consola se ven **dos `SELECT` fijos** (existencia del dueño + listado) y la cantidad no cambia si el dueño tiene más mascotas (RN-15).

## 8. Smoke de integración

- [x] **8.1 — Smoke completo del contrato** *(50 min)*
  - Con `python reiniciar.py` y `uvicorn app.main:app` levantados, ejecutar en orden (curl o `.http` temporal fuera del repo):
    1. `POST /duenios/` con `{"nombre":"Smoke","email":"smoke@test.com"}` → **201** con `"ficha": null`.
    2. Mismo body → **409**.
    3. `GET /duenios/abc` → **422**.
    4. `GET /duenios/99999` → **404**.
    5. `PATCH /duenios/{id}` con `{"nombre":"Smoke 2"}` → **200** con el email original.
    6. `POST /duenios/{id}/ficha` con teléfono y dirección → **201**.
    7. Segunda ficha para el mismo dueño → **409**.
    8. `GET /duenios/{id}/mascotas` → **200** con `[]`.
    9. `DELETE /duenios/1` (dueño con mascotas) → **409**.
    10. Borrar por SQL la ficha del dueño creado en el paso 1 (`DELETE FROM ficha_duenio WHERE duenio_id={id}`) y luego `DELETE /duenios/{id}` → **204**.
  - **Verificación**: los diez códigos coinciden con los esperados; al final SQL `SELECT count(*) FROM duenio` vuelve al valor del seed (2) y `SELECT count(*) FROM ficha_duenio` = **1**. Guardar la salida de la consola para pasársela a [10]; **no** se escribe en `test/`.

- [x] **8.2 — Regresión y contrato de rutas** *(20 min)*
  - Correr `python reiniciar.py` dos veces seguidas y volver a levantar la app.
  - **Verificación**: `GET /openapi.json` → **200** y lista exactamente `POST /duenios/`, `GET /duenios/{duenio_id}`, `PATCH /duenios/{duenio_id}`, `DELETE /duenios/{duenio_id}`, `POST /duenios/{duenio_id}/ficha` y `GET /duenios/{duenio_id}/mascotas`; **no** existe `GET /duenios/` (IN-01); `GET /duenios/1` → **200** después del reinicio; no hay `MissingGreenlet` en la consola.

## Workflow follow-up

- Archivar el change con `/opsx:archive duenios-y-ficha` y marcar `[x]` **solo** la línea `[03]` de `CHANGES.md`, una vez revisado y mergeado.
- Avisar a [05] `mascotas-y-paginacion` que el padrón de dueños ya está disponible por API (`POST /duenios/`, `GET /duenios/{id}`).
- Avisar a Andrés ([10] `pruebas-http-y-evidencia`) que los casos C-01, C-02, C-03 y C-05 ya se pueden escribir, con la salida del smoke de 8.1 como referencia.
