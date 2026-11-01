# Tareas: turnos-alta-transaccional

> Dueño: **Mariano**. Duración estimada total: **7–9 h**. Dependencias: `02` `modelos-y-esquema` y `09` `reiniciar-y-seed` (ambos archivados y mergeados).
> Alcance: **solo `app/modules/turnos/{schemas,service,router}.py`**. Ningún otro archivo se crea ni se modifica (`models.py`, `app/core/**`, `app/main.py`, `reiniciar.py`, `test/**` quedan intactos).

## Notas previas (leer antes de empezar)

- **Entorno virtual primero**: en PowerShell, `.venv\Scripts\Activate.ps1`. Si el prompt no muestra `(.venv)`, todos los `python` de abajo mienten (el `python` del sistema es el *stub* del Microsoft Store).
- **Base en estado conocido**: el smoke arranca siempre con `python reiniciar.py` (dependencia `09`). Eso deja `turno` con 1 fila, `turno_practica` con 2 y `turno_id_seq` en `1, true`, o sea el próximo alta recibe **`id = 2`**.
- **Toda prueba que espere `"id": 2` tiene que arrancar con `python reiniciar.py`.** El `"id": 2` no es una propiedad permanente de la base: es el estado del seed, y cualquier alta previa —exitosa o fallida— lo deja atrás.
- **Nunca `nextval`**: prohibido comprobar secuencias con `nextval` (no es transaccional y consume ids). Solo `SELECT last_value, is_called FROM turno_id_seq;` (solo lectura) o el `"id"` real que devuelve el `POST`.
- **Un `INSERT` que falla SÍ consume el id**: el `nextval` del `DEFAULT` de la columna se evalúa **antes** de que PostgreSQL chequee la FK o la PK, y el `ROLLBACK` no lo devuelve. Provocar un 409 que llegue al `INSERT` deja un hueco en la numeración de `turno.id`; es comportamiento normal de PostgreSQL, no un bug del endpoint (task 5.10).
- **Sin `psql`**: toda consulta SQL se corre en **pgAdmin → Query Tool**. Las peticiones HTTP, con `Invoke-RestMethod` en PowerShell o con un `.http` temporal **fuera del repo** (`test/` es de [10] y no se toca).
- **Sin suite `pytest` obligatoria** (config del proyecto): cada task se verifica con la petición HTTP y/o la consulta SQL que se indica, y ese es el criterio de aceptación. Donde dice **RED** se espera una salida concreta **antes** de implementar; donde dice **GREEN**, la salida esperada después.
- **`echo=True` está activo** en el motor: la consola de `uvicorn` muestra cada sentencia. Sirve como evidencia y es la forma de contar consultas.

## 1. Preparación y línea base (RED)

- [x] **1.1 — Confirmar precondiciones, rama y estado de la base** *(30 min)*
  - `git log --oneline -5` muestra los merges de `modelos-y-esquema` y `reiniciar-y-seed`; rama al día con `main`.
  - `python reiniciar.py` termina con código `0` e imprime el resumen de conteos.
  - **Verificación**: en pgAdmin,
    ```sql
    SELECT (SELECT count(*) FROM turno) AS turnos,
           (SELECT count(*) FROM turno_practica) AS lineas,
           (SELECT last_value FROM turno_id_seq) AS seq,
           (SELECT is_called FROM turno_id_seq) AS llamada;
    ```
    devuelve `1, 2, 1, true`. Si no coincide, el smoke no puede afirmar `"id": 2` y hay que reiniciar antes de seguir.

- [x] **1.2 — Capturar la línea base: hoy `POST /turnos/` no existe** *(30 min)*
  - `uvicorn app.main:app` y probar el endpoint **antes** de escribir código.
  - **Verificación (RED)**: `POST /turnos/` con el cuerpo del ejemplo responde **404** (el router está vacío) y `GET /openapi.json` **no** lista `/turnos/`. Anotar la respuesta: es el estado del que hay que salir.

## 2. DTO del módulo (`schemas.py`)

- [x] **2.1 — Escribir los cinco DTO de `turnos/schemas.py`** *(1 h)*
  - `TurnoPracticaCreate` (`practica_id: int`), `TurnoCreate` (`mascota_id`, `fecha`, `motivo`, `practicas` con `min_length=1`), `MascotaResumenRead` (`id`, `nombre`, `especie`), `TurnoPracticaRead` (`practica_id`, `nombre`, `precio_unitario`), `TurnoRead` (`id`, `fecha`, `motivo`, `total`, `mascota`, `practicas`).
  - `total` y `precio_unitario` como `Decimal`; `fecha` como `datetime`. **Sin** `precio` ni `total` en la entrada. Ningún import desde `app/modules/{mascotas,practicas,duenios}`.
  - **Verificación (GREEN)**: `python -c "from app.modules.turnos.schemas import TurnoCreate, TurnoRead; print(sorted(TurnoCreate.model_fields)); print(sorted(TurnoRead.model_fields))"` imprime `['fecha', 'mascota_id', 'motivo', 'practicas']` y `['fecha', 'id', 'mascota', 'motivo', 'practicas', 'total']`; `Select-String -Path app/modules/turnos/schemas.py -Pattern "from app.modules"` no devuelve coincidencias.

## 3. Alta transaccional (`service.py`)

> **Nota de orden**: las verificaciones HTTP de las tasks 3.2 a 3.5 necesitan el `POST /turnos/` ya publicado, es decir la task **4.1** hecha antes. Dos opciones válidas: (a) adelantar 4.1 (un `@router.post` mínimo que delegue) y después volver acá, o (b) mantener el orden y verificar 3.2–3.5 por lo que sí es observable en ese momento —la consola de `uvicorn` con las sentencias del service ejecutadas desde un script temporal **fuera del repo**, y los conteos en pgAdmin—, dejando las aserciones HTTP para la repetición de 3.2–3.5 al terminar 4.1. Lo que **no** vale es dar por buena una task de esta sección sin haber visto su sentencia en la consola o su efecto en la base.

- [x] **3.1 — Esqueleto del service, excepciones de dominio e imports de modelos** *(45 min)*
  - `crear_turno(session, datos) -> TurnoRead`, más `PracticaInexistente` y `TurnoConflicto` (excepciones propias, sin `HTTPException`).
  - Importar `Mascota` y `Practica` además de `Turno`/`TurnoPractica` (Decisión 11 del `design.md`: sin esos imports `configure_mappers()` falla con `expression 'Mascota' failed to locate a name`).
  - **Verificación**: `python -c "import app.modules.turnos.service"` termina sin error; `python -c "import app.modules.turnos.service, sqlalchemy.orm as o; o.configure_mappers(); print('mappers ok')"` imprime `mappers ok` (si se comenta el import de `Mascota` o `Practica`, falla: probarlo y restaurarlo).

- [x] **3.2 — Leer el catálogo y fallar sin escribir si falta una práctica** *(1 h)*
  - `select(Practica).where(Practica.id.in_(<ids deduplicados>))`; si la cantidad encontrada no cubre los ids pedidos → `rollback()` → `PracticaInexistente` con los ids faltantes.
  - **Verificación**: con el endpoint ya conectado al router (task 4.1), `POST /turnos/` con `[{"practica_id": 1}, {"practica_id": 99999}]` responde **409**; en la consola de `uvicorn` se ve **un** `SELECT` del catálogo seguido de `ROLLBACK` y **ningún** `INSERT`; en pgAdmin los conteos siguen en `turno = 1`, `turno_practica = 2`.

- [x] **3.3 — Construir una fila por práctica pedida, copiar precio y calcular el total** *(1 h)*
  - Iterar la **lista del DTO** (no el resultado de la consulta) y asignar `precio_unitario` desde el `Decimal` del catálogo; `total = sum(..., Decimal("0.00")).quantize(Decimal("0.01"))`.
  - **Verificación**: `Select-String -Path app/modules/turnos/service.py -Pattern "float"` sin coincidencias; en la consola, un alta válida con 2 prácticas emite **2** `INSERT INTO turno_practica`. Con dos elementos iguales (`[{"practica_id": 1}, {"practica_id": 1}]`) el intento emite **2** `INSERT` (no 1): la lista pedida no se colapsa.

- [x] **3.4 — `flush()`, traducción de `IntegrityError` por `sqlstate` y `rollback()`** *(1.5 h)*
  - `try: await session.flush() / except IntegrityError`: `23505` → `TurnoConflicto("...práctica repetida...")`, `23503` → `TurnoConflicto("...mascota no existe...")`, otro → `TurnoConflicto` genérico; **siempre** `await session.rollback()` antes de levantar.
  - **Verificación**: repetida → **409** y conteos intactos; mascota `99999` → **409** con el mensaje de mascota; en ambos casos la consola muestra el `INSERT` fallido seguido de `ROLLBACK`. Después del 409, una petición válida al mismo servidor responde **201** (la sesión no quedó en estado fallido).

- [x] **3.5 — Releer el turno con carga anticipada y armar la respuesta** *(1 h)*
  - Relectura con `joinedload(Turno.mascota)` + `selectinload(Turno.practicas).joinedload(TurnoPractica.practica)` dentro de la misma transacción; normalizar `fecha` con `.astimezone(timezone.utc)`; ordenar las prácticas por `practica_id`; `commit()` al final.
  - **Verificación**: la respuesta del alta trae `mascota` y `practicas` **completas** (sin `MissingGreenlet`); en la consola, el alta ejecuta exactamente **3** `SELECT` de lectura (catálogo + turno con mascota + prácticas con práctica) y ningún `SELECT` adicional por práctica.

## 4. Router (`router.py`)

- [x] **4.1 — Publicar `POST /turnos/` y traducir los conflictos** *(45 min)*
  - `APIRouter(prefix="/turnos", tags=["turnos"])`, `@router.post("/", status_code=201, response_model=TurnoRead)`, handler `async def` con `Depends(get_session)`; `PracticaInexistente`/`TurnoConflicto` → `HTTPException(409, detail=...)`.
  - **Verificación (GREEN de 1.2)**: `/openapi.json` lista `POST /turnos/`; la petición del ejemplo responde **201** sin redirección 307 (SU-05). `git diff --stat` no muestra cambios en `app/main.py`.

## 5. Verificación de los escenarios de la spec

> Cada task de esta sección cierra uno o más escenarios de `specs/turnos/spec.md`. Las que afirman `"id": 2` (5.1, 5.2, 5.3, 5.7, 5.8) arrancan con `python reiniciar.py`, porque el `2` es el estado del seed: cualquier alta previa —exitosa o fallida— lo deja atrás (ver 5.10 y las notas previas).

- [x] **5.1 — Escenario esperado: alta válida con dos prácticas** *(45 min)*
  - Cuerpo: `{"mascota_id": 1, "fecha": "2026-11-12T10:30:00-03:00", "motivo": "Control anual", "practicas": [{"practica_id": 1}, {"practica_id": 3}]}`.
  - **Verificación**:
    ```powershell
    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/turnos/ -ContentType "application/json" -Body '<el cuerpo de arriba>'
    ```
    responde `201` con `id = 2`, `fecha = 2026-11-12T13:30:00Z`, `total = "27000.00"`, `mascota = {1, "Toby", "perro"}` y `practicas = [{1,"Consulta","15000.00"}, {3,"Vacuna antirrábica","12000.00"}]`, **sin** campo `id` en las prácticas. En pgAdmin:
    ```sql
    SELECT (SELECT count(*) FROM turno) AS turnos,
           (SELECT count(*) FROM turno_practica) AS lineas,
           (SELECT total FROM turno WHERE id = 2) AS total2;
    ```
    devuelve `2, 4, 27000.00`.

- [x] **5.2 — Escenario: el total del cliente no se respeta** *(30 min)*
  - Repetir 5.1 agregando `"total": "1.00"` al cuerpo y `"precio": "1.00"` dentro de cada práctica.
  - **Verificación**: responde **201** con `"total": "27000.00"`; `SELECT turno_id, practica_id, precio_unitario FROM turno_practica WHERE turno_id = 2 ORDER BY practica_id;` devuelve `15000.00` y `12000.00`, y `SELECT total FROM turno WHERE id = 2;` devuelve `27000.00` (string en JSON, `numeric` en la base).

- [x] **5.3 — Escenario de error de negocio: práctica inexistente no guarda nada** *(45 min)*
  - Cuerpo con `[{"practica_id": 1}, {"practica_id": 99999}]`, sobre la base recién reiniciada.
  - **Verificación**: **409**; `SELECT (SELECT count(*) FROM turno) AS turnos, (SELECT count(*) FROM turno_practica) AS lineas;` sigue en `1, 2` (ni siquiera la práctica válida 1 quedó guardada); `SELECT count(*) FROM turno WHERE id = 2;` = `0` (no quedó ningún turno con ese id). El mensaje menciona `99999`. **Este caso no llega a ningún `INSERT`**, así que la secuencia no se mueve: `last_value` sigue en `1` (se comprueba en 5.10).

- [x] **5.4 — Escenario de error de negocio: práctica repetida** *(30 min)*
  - Cuerpo con `[{"practica_id": 1}, {"practica_id": 1}]`.
  - **Verificación**: **409** con mensaje de práctica repetida; conteos `1, 2` sin cambios; en la consola, el segundo `INSERT INTO turno_practica` falla con `sqlstate` `23505` y sigue un `ROLLBACK`. Repetir con la práctica 3 repetida: mismo resultado.

- [x] **5.5 — Escenario de error de negocio: mascota inexistente** *(30 min)*
  - Cuerpo con `"mascota_id": 99999` y prácticas válidas.
  - **Verificación**: **409** con mensaje de mascota inexistente; conteos `1, 2` sin cambios; en la consola, el `INSERT INTO turno` falla con `sqlstate` `23503` y sigue un `ROLLBACK`.

- [x] **5.6 — Escenario de borde: contrato del cuerpo (422)** *(30 min)*
  - Probar `"practicas": []`, el cuerpo sin `motivo`, el cuerpo sin `mascota_id` y el cuerpo sin `practicas`.
  - **Verificación**: los cuatro responden **422**; en la consola **no aparece ningún `SELECT`** (el handler no llegó a ejecutarse); conteos `1, 2` sin cambios.

- [x] **5.7 — Escenario de borde: fecha en UTC, con y sin offset** *(30 min)*
  - Dos altas separadas, cada una después de `python reiniciar.py`: una con `"fecha": "2026-11-12T10:30:00-03:00"` (la de 5.1) y otra con `"fecha": "2026-11-12T13:30:00"` (sin zona horaria).
  - **Verificación**: ambas respuestas traen `"fecha": "2026-11-12T13:30:00Z"`; `SELECT id, fecha FROM turno ORDER BY id;` muestra el mismo instante (`2026-11-12 13:30:00+00`) en las dos filas, de modo que la `Z` no depende del offset de entrada ni de la zona de la sesión de PostgreSQL.

- [x] **5.8 — Escenario de borde: el precio queda congelado** *(30 min)*
  - Crear el turno de 5.1 y después, por SQL: `UPDATE practica SET precio = 99000.00 WHERE id = 1;`.
  - **Verificación**: `SELECT turno_id, practica_id, precio_unitario FROM turno_practica WHERE turno_id = 2 ORDER BY practica_id;` sigue mostrando `15000.00` y `12000.00`; `SELECT total FROM turno WHERE id = 2;` sigue en `27000.00`. Restaurar el precio con `UPDATE practica SET precio = 15000.00 WHERE id = 1;` (o `python reiniciar.py`).

- [x] **5.9 — Escenario: misma cantidad de consultas con 1 y con 3 prácticas** *(45 min)*
  - Después de `python reiniciar.py`, un alta con 1 práctica (`[{"practica_id": 2}]`) y otra con 3 (`[{"practica_id": 1}, {"practica_id": 2}, {"practica_id": 3}]`), copiando la consola de `uvicorn` en cada caso.
  - **Verificación**: en las dos capturas hay **3 `SELECT` de lectura** (catálogo, turno+mascota, prácticas+práctica) y la diferencia entre ambas es solo la cantidad de `INSERT INTO turno_practica`; ninguna petición falla con `MissingGreenlet`. Guardar las dos capturas para [07] y [10].

- [x] **5.10 — Comprobar el efecto de los caminos de error sobre la secuencia de `turno.id`** *(30 min)*
  - **(a) Errores que no llegan a ningún `INSERT`**: sobre la base recién reiniciada, provocar 5.3 (práctica inexistente) y las cuatro variantes de 5.6 (422).
    - **Verificación**: `SELECT last_value, is_called FROM turno_id_seq;` devuelve `1, true`. Es correcto: el 409 del catálogo se resuelve antes de construir el turno y el 422 lo resuelve FastAPI sin ejecutar el handler, así que no hay ningún `nextval` de por medio.
  - **(b) Errores que sí llegan al `INSERT`**: `python reiniciar.py` y después provocar 5.4 (práctica repetida) y 5.5 (mascota inexistente).
    - **Verificación**: `SELECT last_value, is_called FROM turno_id_seq;` devuelve `2, true` —o más, si los dos casos se provocaron sobre la misma corrida—. El `nextval` del `DEFAULT` de `turno.id` se evalúa **antes** de que PostgreSQL chequee la PK de `turno_practica` o la FK de la mascota, y el `ROLLBACK` no lo devuelve; por eso `last_value` quedó por encima de `1`. Al mismo tiempo `SELECT count(*) FROM turno;` sigue en `1`: el id se consumió, el turno no se guardó.
    - **Es comportamiento normal de PostgreSQL, no un bug del endpoint.** Las secuencias no son transaccionales y los huecos en la numeración son esperados. Lo que el endpoint garantiza es **no dejar filas** (RN-23), no *no dejar huecos*.
  - **(c) Consecuencia para el resto del smoke**: después de (b), un alta válida devuelve `"id": 3`, no `"id": 2`; por eso toda prueba que espere `"id": 2` arranca con `python reiniciar.py`. **No** ejecutar `nextval` en ningún momento para comprobar nada.

## 6. Cierre

- [x] **6.1 — Confirmar que solo cambiaron los tres archivos del alcance** *(30 min)*
  - **Verificación**: `git status --short` muestra únicamente `app/modules/turnos/schemas.py`, `app/modules/turnos/service.py`, `app/modules/turnos/router.py` (más el directorio del change en `openspec/`); `git diff --stat` no incluye `models.py`, `app/core/**`, `app/main.py`, `reiniciar.py`, `requirements.txt`, `env.example` ni `test/**`. `python -c "import app.main"` sigue funcionando.

- [x] **6.2 — Validar el change con OpenSpec** *(15 min)*
  - **Verificación**: `openspec validate "turnos-alta-transaccional" --type change --strict` responde `is valid`; `openspec status --change "turnos-alta-transaccional" --json` marca los cuatro artefactos como completos.

- [x] **6.3 — Dejar la evidencia para [07], [10] y [11]** *(30 min)*
  - Guardar en el mensaje de cierre del change (fuera del repo): respuesta 201 con `"id": 2` y `"total": "27000.00"`, los tres 409 con sus mensajes, el 422 de la lista vacía, los conteos antes/después de cada error, el `last_value` de `turno_id_seq` antes y después de los casos de 5.10 (con la aclaración de que el hueco es normal) y las dos capturas de 5.9.
  - **Verificación**: [10] puede escribir `caso_C-04.http` (práctica inexistente → 409 sin nada guardado), `caso_C-06.http` (alta válida → 201 con precios y total) y `caso_C-08` (precio congelado) sin volver a deducir el contrato; [07] hereda los 3 `SELECT` de lectura como línea base para C-07.

## Observaciones del apply (2026-11-01)

- Tasks marcadas `[x]`: **1.1, 1.2, 2.1, 3.1 a 3.5, 4.1, 5.1, 5.3, 5.4, 5.5, 5.6 y 5.10**.
- Task 3.1: el import de los modelos del grafo quedó en **cuatro** módulos (`duenios`, `mascotas`, `practicas`, `turnos`), no en tres: `Mascota` referencia `"Duenio"`, que tampoco se había registrado.
- Tasks **no ejecutadas** en este apply: **5.2** (total enviado por el cliente no se respeta), **5.7** (fecha sin offset), **5.8** (precio congelado), **5.9** (misma cantidad de consultas con 1 y 3 prácticas) y las de cierre **6.1 a 6.3**.
- Smoke de este apply, con `python reiniciar.py` antes de cada prueba:
  - **1.1/1.2**: RED previo capturado (`POST /turnos/` → 404 sin router); GREEN con el primer alta válida.
  - **5.1**: 201 con `id=2`, `fecha=2026-11-12T13:30:00Z`, `total="27000.00"`; SQL: turno 2 con total 27000.00 y 2 filas hijas con precios 15000.00/12000.00.
  - **5.3**: 409 con la práctica inexistente; conteos `turnos=1, lineas=2` sin cambios y `last_value` en `1, true` (no llegó al INSERT).
  - **5.4**: 409 con la práctica repetida (el `INSERT` duplicado falló); conteos sin cambios.
  - **5.5**: 409 con la mascota inexistente (el `INSERT` del turno falló); conteos sin cambios.
  - **5.6**: 422 en la lista vacía y en el cuerpo sin `motivo`; sin `SELECT` al handler.
  - **5.10**: confirmada con salida real — error que no llega al `INSERT` → `last_value` queda en `1, true`; error que llega al `INSERT` (mascota inexistente) → `last_value` pasa a `2, true` y el `ROLLBACK` no lo devuelve, con los conteos sin cambios.

## Workflow follow-up

- Archivar con `/opsx:archive turnos-alta-transaccional` y marcar `[x]` **solo** la línea de `[06]` en `CHANGES.md`, cuando el PR esté revisado y mergeado.
- Avisar a Andrés (dueño de [10]) que C-04 y C-06 ya tienen evidencia, y a Facundo (dueño de [11]) las cinco decisiones propias de la Decisión 16 del `design.md` para la sección "Decisiones propias del equipo".
- Antes de proponer [07] `turnos-lecturas-y-baja`: reutilizar la relectura con carga anticipada de 3.5 como punto de partida del `GET /turnos/{id}`, y **no** volver a introducir el prefijo `/turnos` en `app/main.py`.
