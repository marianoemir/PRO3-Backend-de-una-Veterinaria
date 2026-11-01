# Tareas: reiniciar-y-seed

> Dueño: **Mariano**. Duración estimada total: **6–8 h**. Dependencia: `02` `modelos-y-esquema` (archivado y mergeado).
> Alcance: **solo `reiniciar.py`** (archivo nuevo, raíz del repo). Ningún otro archivo se crea ni se modifica.

## Notas previas (leer antes de empezar)

- **Sin `psql`**: el equipo trabaja en Windows con **pgAdmin**. Toda inspección se hace con consultas al catálogo o `SELECT` de conteo ejecutados en **Query Tool**. Las consolas de comandos son **PowerShell**: el código de salida de la última ejecución se lee con `$LASTEXITCODE` (en `cmd` sería `%ERRORLEVEL%`).
- **TDD**: no hay suite `pytest` obligatoria. La verificación es (a) el smoke del script con su código de salida, (b) consultas SQL de conteo y de ids, y (c) las tres corridas de los escenarios de la spec. Queda escrito acá porque no hay tests unitarios que escribir.
- **`reiniciar.py` destruye la base de `.env`.** Antes de cada corrida de prueba, confirmar en la consola el destino impreso por el script (`Reiniciando <host>/<base>`). Nunca apuntar `.env` a una base con datos que importen.
- **Importar los cuatro `models.py`** no es opcional: sin eso `SQLModel.metadata` conoce un subconjunto de tablas y `create_all` crea un esquema incompleto (`design.md` §3).
- **El script no debe importar `app.main`**: no necesita la app y el `lifespan` crearía un segundo motor.

## 1. Preparación y precondiciones

- [x] **1.1 — Confirmar precondiciones (dependencia, `.env`, PostgreSQL, rama)** *(30 min)*
  - `git log --oneline -5` muestra el merge de `modelos-y-esquema`; la rama está al día con `main`.
  - El `.env` tiene `DATABASE_URL` con el driver `postgresql+asyncpg://` y PostgreSQL 16 está corriendo.
  - **Activar el entorno virtual antes de cualquier comando `python`**: en PowerShell, `.venv\Scripts\Activate.ps1`. El `python` del sistema es un *stub* del Microsoft Store y falla o abre la tienda en lugar de ejecutar el intérprete del proyecto; si el prompt no muestra `(.venv)`, todos los `python -c` de estas tasks mienten.
  - **Verificación**: con el entorno virtual activo (`python -c "import sys; print(sys.prefix)"` apunta a `.venv`), `python -c "from app.core.config import settings; u = settings.DATABASE_URL; print(u.split('@')[-1])"` imprime `host:puerto/base` **sin credenciales** y no lanza `FATAL`; `python -c "from app.modules.duenios.models import Duenio; from app.modules.mascotas.models import Mascota; from app.modules.practicas.models import Practica; from app.modules.turnos.models import Turno"` termina sin error.

- [x] **1.2 — Crear el esqueleto de `reiniciar.py`** *(45 min)*
  - Docstring de cabecera (qué hace, cómo se ejecuta, qué base usa, advertencia de que **borra** todo).
  - Imports: `asyncio`, `sys`, `datetime/timezone`, `Decimal`, `SQLModel`, `AsyncSession`, `text` de SQLAlchemy, `settings` de `app.core.config`, `crear_motor`/`crear_fabrica` de `app.core.database` y **los cuatro** `models.py` (con `# noqa: F401`, ver `design.md` §3).
  - `async def main() -> None:` y el bloque `if __name__ == "__main__": asyncio.run(main())`.
  - **Verificación**: `python -c "import reiniciar; print('import ok')"` imprime `import ok` **sin conectarse** a la base (el `asyncio.run` no corre al importar). Y `python -c "import reiniciar; from sqlmodel import SQLModel; print(sorted(SQLModel.metadata.tables))"` imprime exactamente `['duenio', 'ficha_duenio', 'mascota', 'practica', 'turno', 'turno_practica']` — si falta una, el import de ese módulo está mal.

- [x] **1.3 — Agregar la verificación previa del metadata** *(30 min)*
  - Antes de abrir la transacción, comparar `set(SQLModel.metadata.tables)` con las seis tablas esperadas; si falta alguna, imprimir qué tabla falta y salir con código `2` (`design.md` §3).
  - **Verificación**: comentar temporalmente (en el editor, sin guardar el cambio) el import de `app.modules.practicas.models` y correr `python reiniciar.py`: debe abortar con un mensaje que nombra `practica` y `$LASTEXITCODE` = `2`, **sin** haber tocado la base. Restaurar el import y repetir la tarea 1.2 para confirmar el estado bueno.

## 2. Reconstrucción del esquema

- [x] **2.1 — Motor, fábrica y transacción única en `main()`** *(1 h)*
  - `engine = crear_motor(settings.DATABASE_URL)` y `fabrica = crear_fabrica(engine)` (misma configuración que la app, SU-04).
  - Una sola transacción: `async with AsyncSession(engine) as session: async with session.begin():` con `conn = await session.connection()`.
  - `engine.dispose()` en un `finally`.
  - Imprimir el destino enmascarado **antes** de borrar: `engine.url.render_as_string(hide_password=True)`.
  - **Verificación**: `python reiniciar.py` con el cuerpo del seed todavía vacío sale con `$LASTEXITCODE` = `0`, imprime el destino sin contraseña y el resumen con conteos en `0`.

- [x] **2.2 — `drop_all` + `create_all` dentro de la transacción** *(45 min)*
  - `await conn.run_sync(SQLModel.metadata.drop_all)` y después `await conn.run_sync(SQLModel.metadata.create_all)`, en ese orden y **sin** `engine.begin()` aparte (`design.md` §4–§5).
  - **Verificación**: correr el script y en pgAdmin
    ```sql
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' ORDER BY 1;
    ```
    devuelve las **6** tablas. Correr el script **otra vez** produce el mismo resultado sin error de dependencia de FK (el `drop_all` ordena por FK).

- [x] **2.3 — Confirmar que el reinicio funciona sobre base vacía y sobre base poblada** *(30 min)*
  - Con la base recién creada por el script (vacía de datos) y con datos de prueba insertados a mano, el script debe dejar el mismo esquema.
  - **Verificación**: insertar una fila cualquiera por SQL (`INSERT INTO practica (nombre, precio) VALUES ('scratch', 1000.00);`), correr el script y comprobar con `SELECT count(*) FROM practica;` que la fila desapareció porque la tabla se recreó. Repetir el script: mismo resultado.

## 3. Datos iniciales del seed

- [x] **3.1 — Definir las constantes del seed con `Decimal`** *(45 min)*
  - Dueños 1 y 2 (el 1 con ficha), ficha del dueño 1, mascotas 1–3 (mascota 1 = Toby / perro / dueño 1), prácticas 1–4 (1 = Consulta `15000.00`, 3 = Vacuna antirrábica `12000.00`), turno 1 y sus dos líneas (prácticas 1 y 3), con la fecha fija `2026-11-12T13:30:00+00:00` (`design.md` §7).
  - Importes como `Decimal("15000.00")`, **nunca** `float` ni literales flotantes.
  - **Verificación**: `Select-String -Path reiniciar.py -Pattern "float"` no devuelve coincidencias; `python -c "import reiniciar; print(reiniciar.PRACTICAS_SEED)"` (o el nombre que se les dé) muestra los cuatro precios con dos decimales y `type(...)` = `Decimal`.

- [x] **3.2 — Insertar dueños, ficha y mascotas en el orden del grafo de FK** *(1 h)*
  - `session.add_all(...)` con instancias de `Duenio`, `FichaDuenio` y `Mascota` (ids explícitos), en ese orden (`design.md` §9). Sin SQL de `INSERT` a mano.
  - **Verificación**: correr el script y en pgAdmin
    ```sql
    SELECT (SELECT count(*) FROM duenio) AS duenios,
           (SELECT count(*) FROM ficha_duenio) AS fichas,
           (SELECT count(*) FROM mascota) AS mascotas;
    ```
    devuelve `duenios = 2`, `fichas = 1`, `mascotas = 3`. Y `SELECT id, duenio_id FROM ficha_duenio;` devuelve `(1, 1)`; `SELECT id, nombre, especie, duenio_id FROM mascota ORDER BY id;` devuelve Toby/perro/1 primero.

- [x] **3.3 — Insertar prácticas, turno y sus dos líneas con `total` calculado** *(1.5 h)*
  - Prácticas con ids 1–4; `Turno` con `mascota_id = 1`, `motivo = "Control anual"`, `total` **calculado** como `sum(precio_unitario, Decimal("0.00"))` —no literal—; `TurnoPractica` con `precio_unitario` copiado del catálogo (`design.md` §7–§8).
  - **Verificación**: correr el script y en pgAdmin
    ```sql
    SELECT p.id, p.nombre, p.precio FROM practica p ORDER BY p.id;
    SELECT id, mascota_id, motivo, total FROM turno;
    SELECT turno_id, practica_id, precio_unitario FROM turno_practica ORDER BY practica_id;
    SELECT data_type, numeric_precision, numeric_scale FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'turno' AND column_name = 'total';
    ```
    esperado: 4 prácticas (1 Consulta `15000.00`, 3 Vacuna antirrábica `12000.00`); 1 turno con `total = 27000.00`; 2 filas (`1,1,15000.00` y `1,3,12000.00`); `total` es `numeric` 12/2 (nunca `double precision`).

- [x] **3.4 — Imprimir el resumen final de conteos** *(30 min)*
  - Al terminar el seed, contar las seis tablas y imprimir una línea por tabla, para que la evidencia quede en consola.
  - **Verificación**: la última salida del script muestra `duenio 2 · ficha_duenio 1 · mascota 3 · practica 4 · turno 1 · turno_practica 2` y `$LASTEXITCODE` = `0`.

## 4. Contrato de identificadores y secuencia del turno

- [x] **4.1 — Resincronizar las secuencias con `setval`** *(1 h)*
  - Para `duenio`, `ficha_duenio`, `mascota`, `practica` y `turno`, ejecutar `setval(pg_get_serial_sequence('<tabla>', 'id'), (SELECT max(id) FROM <tabla>), true)` con `await session.execute(text(...))`, dentro de la misma transacción y después de insertar (`design.md` §6). `turno_practica` no tiene secuencia.
  - **Verificación**: correr el script y en pgAdmin
    ```sql
    SELECT last_value, is_called FROM turno_id_seq;
    ```
    devuelve `1, true`. Repetir para `duenio_id_seq`, `mascota_id_seq` y `practica_id_seq` (`2, true`, `3, true`, `4, true`).

- [x] **4.2 — Verificar que el próximo turno recibe `id = 2` (sin consumir la secuencia)** *(30 min)*
  - **NO ejecutar `nextval` sobre las secuencias reales**: en PostgreSQL los avances de secuencia **no son transaccionales**; un `ROLLBACK` no devuelve el valor consumido. Un `BEGIN; SELECT nextval('turno_id_seq'); ROLLBACK;` dejaría la secuencia en 2 y el próximo turno recibiría `3`, rompiendo exactamente el contrato que se quiere comprobar.
  - Chequeo correcto, solo lectura:
    ```sql
    SELECT last_value, is_called FROM turno_id_seq;
    ```
  - **Verificación**: la consulta anterior devuelve `1, true`. Con `is_called = true`, el próximo `nextval` es `last_value + 1` = `2`, y eso implica que el próximo turno recibe `2` **sin haber consumido nada**. Repetir la consulta después de la verificación: debe seguir dando `1, true` (prueba de que no se gastó el valor). *(Cuando [06] esté implementado, la comprobación definitiva es `POST /turnos/` → respuesta con `"id": 2`; se anota para [10].)*

## 5. Fallo explícito, códigos de salida y atomicidad

- [x] **5.1 — Captura de errores con mensaje legible y código `2`** *(1 h)*
  - Envolver el cuerpo de `main()` en `try/except` (errores de conexión/ejecución de SQLAlchemy y cualquier excepción inesperada): imprimir una línea en español con qué falló, el tipo de excepción y el primer renglón del mensaje del driver, y salir con `2`. Sin volcar el stack como única salida y **sin** imprimir la contraseña (usar `render_as_string(hide_password=True)`).
  - **Verificación**: apuntar `DATABASE_URL` a un puerto cerrado (por ejemplo `...@localhost:5433/veterinaria`), correr el script y comprobar: una línea de error legible que menciona que no se pudo conectar, ninguna contraseña en pantalla, y `$LASTEXITCODE` = `2`. Restaurar el `.env`.

- [x] **5.2 — Verificar el caso `DATABASE_URL` ausente (código `1`)** *(30 min)*
  - El mensaje `FATAL` lo emite `app/core/config.py`; el script no lo duplica.
  - **Verificación**: en una consola, `$env:DATABASE_URL = $null` **y** con el `.env` renombrado temporalmente (`Rename-Item .env .env.bak`), correr `python reiniciar.py`; debe imprimir el `FATAL` que nombra `DATABASE_URL` y `env.example`, y `$LASTEXITCODE` = `1`. Renombrar el `.env` de vuelta y confirmar que el script vuelve a funcionar.

- [x] **5.3 — Verificar que un fallo no deja la base a medio poblar** *(1 h)*
  - Todo (`drop_all`, `create_all`, seed, `setval`) va en la misma transacción: un fallo revierte también el DDL (`design.md` §5). Esa es la propiedad a demostrar acá.
  - **Verificación**: (a) con el seed ya funcionando, anotar los conteos de las seis tablas (`SELECT count(*)` de cada una) y guardar una fila testigo de `practica`; (b) introducir a mano en el código, **temporalmente**, un error que estalle **después** del `drop_all`/`create_all` y a mitad del seed —por ejemplo, un `id` de `mascota` duplicado (dos insert con `id = 1`), o un `raise` explícito tras el segundo `flush`—; (c) correr `python reiniciar.py`: el proceso sale con `2` y un mensaje legible; (d) en pgAdmin, comprobar que **las seis tablas y todos los datos previos siguen intactos**, con los mismos conteos del paso (a) y la fila testigo todavía presente; (e) **restaurar el código** (quitar el error temporal) y volver a correr el script para confirmar que sale con `0`.
  - **No** se usan roles sin permisos ni se detiene PostgreSQL: los dos probaban el fallo equivocado (permisos o caída de red) y no la atomicidad del seed.

## 6. Verificación de integración: los tres escenarios de la spec

- [x] **6.1 — Escenario esperado: base vacía → conteos, ids y turno** *(45 min)*
  - Con la base vacía (`DROP TABLE` de las seis tablas o `DROP DATABASE` + `CREATE DATABASE`), correr `python reiniciar.py`.
  - **Verificación** (todo en una consulta para no depender del último `SELECT` de pgAdmin):
    ```sql
    SELECT (SELECT count(*) FROM duenio) AS duenios,
           (SELECT count(*) FROM ficha_duenio) AS fichas,
           (SELECT count(*) FROM mascota) AS mascotas,
           (SELECT count(*) FROM practica) AS practicas,
           (SELECT count(*) FROM turno) AS turnos,
           (SELECT count(*) FROM turno_practica) AS lineas,
           (SELECT nombre FROM mascota WHERE id = 1) AS mascota1,
           (SELECT nombre || ' ' || precio FROM practica WHERE id = 1) AS practica1,
           (SELECT nombre || ' ' || precio FROM practica WHERE id = 3) AS practica3,
           (SELECT total FROM turno WHERE id = 1) AS total1;
    ```
    esperado: `2, 1, 3, 4, 1, 2, Toby, "Consulta 15000.00", "Vacuna antirrábica 12000.00", 27000.00`. `$LASTEXITCODE` = `0`.

- [x] **6.2 — Escenario de error de negocio: configuración y conexión** *(30 min)*
  - Repetir 5.2 (sin `DATABASE_URL`) y 5.1 (base inalcanzable) como escenarios formales y anotar en la evidencia: comando, mensaje impreso y código de salida.
  - **Verificación**: `1` para configuración ausente y `2` para conexión fallida, en ambos casos con mensaje legible; en el segundo caso, además, `SELECT count(*) FROM turno;` conserva el valor previo a la corrida.

- [x] **6.3 — Escenario de borde: doble corrida y base recién creada** *(45 min)*
  - **(a) Doble corrida**: `python reiniciar.py; $LASTEXITCODE` dos veces seguidas. Comparar los dos resúmenes de conteos y las consultas de 6.1: idénticos, sin errores de PK/UNIQUE.
  - **(b) Base recién creada**: en pgAdmin, `DROP DATABASE veterinaria;` + `CREATE DATABASE veterinaria;` (con la app detenida), y correr el script sobre esa base vacía.
  - **Verificación**: (a) ambas corridas con código `0` y conteos idénticos en las seis tablas, con `mascota` 1 = Toby y `SELECT last_value, is_called FROM turno_id_seq;` = `1, true` al final de cada corrida (es decir, el próximo turno recibe `2`, sin haber consumido el valor: **nunca** comprobar con `nextval`, que no se revierte con `ROLLBACK`); (b) el script funciona sin pasos manuales previos, deja las seis tablas y los conteos de 6.1.

## 7. Cierre

- [x] **7.1 — Confirmar que el script no toca ningún otro archivo** *(30 min)*
  - Revisar el diff y el estado del repo.
  - **Verificación**: `git status --short` muestra **solo** `?? reiniciar.py` (y el directorio del change en `openspec/`); `git diff --stat` está vacío porque no se modificó ningún archivo versionado. `Select-String -Path reiniciar.py -Pattern "os.getenv|os.environ"` no devuelve coincidencias (la URL sale de `settings`), y `app/`, `requirements.txt`, `env.example` y `.gitignore` no aparecen en el diff. `python -c "import app.main"` sigue funcionando.

- [x] **7.2 — Validar el change con OpenSpec** *(15 min)*
  - **Verificación**: `openspec validate "reiniciar-y-seed" --type change --strict` responde `is valid`, y `openspec status --change "reiniciar-y-seed" --json` marca los cuatro artefactos como completos.

- [x] **7.3 — Dejar la evidencia de las corridas para [10] y [11]** *(30 min)*
  - Guardar (fuera del repo o en el propio mensaje de cierre del change) la salida de: corrida exitosa con resumen de conteos, doble corrida, código de salida `1` y `2`, y la consulta de ids/total de 6.1.
  - **Verificación**: existe la transcripción de las cuatro corridas con sus mensajes y códigos de salida; [10] puede apoyarse en ella para los casos C-01..C-09 y [11] para los pasos del README.

## Workflow follow-up

- Archivar el change con `/opsx:archive reiniciar-y-seed` y marcar `[x]` **solo** la línea de `[09]` en `CHANGES.md`, cuando el PR esté revisado y mergeado.
- Avisar a Mariano (dueño de [06] `turnos-alta-transaccional`) que el seed ya está disponible: el alta de turno con `mascota_id: 1` y `practicas: [{1}, {3}]` debe devolver `"id": 2` y `"total": "27000.00"`.
- Al escribir el `README.md` ([11]): incluir `python reiniciar.py` en los pasos desde cero y mencionar como decisión propia los códigos de salida `1`/`2`, los valores elegidos para las prácticas 2 y 4, y que el script **borra** la base de `.env`.
