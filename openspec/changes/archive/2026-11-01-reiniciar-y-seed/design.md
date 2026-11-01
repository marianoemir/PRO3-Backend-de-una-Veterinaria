# Diseño: reiniciar-y-seed

## Contexto

Ver `proposal.md` §Why. El estado de partida que condiciona el diseño:

- **`reiniciar.py` no existe.** `create_all`/`drop_all` estaban reservados a este archivo desde [01]/[02] (DD-01) y hoy el esquema solo se creó, en el smoke de [02], con un `scratch_crear_esquema.py` no versionado. La base del equipo puede estar en cualquier estado: vacía, con tablas sin datos, o con tablas y datos.
- **Los modelos están completos** ([02] archivado): `app/modules/{duenios,mascotas,practicas,turnos}/models.py` declaran las seis tablas con `__tablename__` explícito, PK compuesta, UNIQUE, CHECK, FK con su acción de borrado e índices.
- **Configuración ya resuelta**: `app/core/config.py` carga `.env` con `python-dotenv` y expone `settings.DATABASE_URL`; si falta, imprime un mensaje `FATAL` y llama a `sys.exit(1)` **en el import**. `app/core/database.py` expone `crear_motor(url)` (con `echo=True`) y `crear_fabrica(engine)` (`async_sessionmaker`, `expire_on_commit=False`). `app/main.py` crea motor y fábrica en el `lifespan` — el script **no** debe importar `app.main`: no necesita la app para hablar con la base.
- **Punto crítico heredado de [02]**: importar un solo `models.py` no alcanza. `SQLModel.metadata` solo conoce las clases importadas, así que `create_all` crearía un subconjunto de tablas y el primer `INSERT` fallaría por FK inexistente. `reiniciar.py` debe importar **los cuatro** módulos ([02] §6).
- **Entorno del equipo**: Windows + PowerShell, sin `psql`; la inspección se hace en **pgAdmin** con consultas al catálogo. El intérprete local disponible es 3.13 (`.pyc` de `cpython-313`), compatible con el mínimo de 3.12 del stack.
- **`.env` local existe** y no está versionado (`git status` lo ignora); `env.example` trae una URL de ejemplo sin secretos (RN-24).

## Objetivos / No objetivos

**Objetivos**

- Dejar la base en un estado **determinista y reproducible**: mismos ids, mismos importes, misma fecha, en cualquier máquina y en cualquier ejecución.
- Materializar el **contrato de datos** que el enunciado usa en sus ejemplos: mascota 1 = Toby (perro), práctica 1 = Consulta `15000.00`, práctica 3 = Vacuna antirrábica `12000.00`, y el próximo turno con `id = 2`.
- Que el fallo sea **legible y no destructivo**: código de salida distinto de 0, mensaje en español, y base intacta si algo sale mal.
- Que el script se pueda correr **antes de cualquier caso de prueba** sin instrucciones adicionales.

**No objetivos**

- Endpoints, DTO, services o seeds de ejemplo para los casos de [10] (los `.http` y el alta de turno son de [06] y [10]).
- Cambiar `app/core/{config,database}.py`, `env.example`, `requirements.txt` o cualquier `models.py`, aunque una mejora sea evidente (ver Decisión 13).
- Migraciones, datos reales, carga masiva, `faker`, fixtures de pytest ni un seed configurable por CLI.
- Validar el seed con las reglas de negocio del API: el seed escribe datos **válidos**; las garantías las sigue dando la base (DD-03).

## Decisiones

### 1. Alcance literal: un solo archivo, `reiniciar.py` — [KB]

`CHANGES.md` §Archivos compartidos asigna `reiniciar.py` a Mariano para el change [09], y la definición de terminado de cada change exige no tocar archivos ajenos. El script **importa** `settings`, `crear_motor`, `crear_fabrica` y los modelos, pero **no modifica** ninguno. Consecuencia práctica: si algo del script necesita un cambio en `app/core/database.py` (por ejemplo apagar `echo=True`), ese cambio se pide o va en otro change; acá no se hace.

### 2. Misma configuración que la aplicación — [SUPUESTO] SU-04, [KB] RN-24

`reiniciar.py` hace `from app.core.config import settings` y usa `settings.DATABASE_URL`; no lee `os.environ` por su cuenta ni acepta una URL por parámetro. También construye el motor con `crear_motor(...)` y la fábrica con `crear_fabrica(...)`, para que la conexión tenga exactamente la misma forma que la de la API (`asyncpg`, `echo=True`, `expire_on_commit=False`).

- **Por qué**: SU-04 fija que el script opera sobre la misma base que la app. Dos caminos de configuración distintos se desincronizan en silencio, y el síntoma sería el peor posible: la API sirve una base y el evaluador mira otra.
- **Efecto lateral aceptado**: `echo=True` imprime cada sentencia con sus parámetros; el seed sale verboso. Es inocuo —y útil como evidencia— pero es ruido. Apagarlo exige tocar `app/core/database.py` (Decisión 1), así que se acepta.
- **Si falta `DATABASE_URL`**: el import de `settings` termina el proceso con el mensaje `FATAL` de `config.py` y código `1`. El script no duplica esa validación.

### 3. Importar los cuatro `models.py` y verificar que el metadata esté completo — [KB] [02] §6, [DECISIÓN]

```python
from app.modules.duenios.models import Duenio, FichaDuenio   # noqa: F401
from app.modules.mascotas.models import Mascota              # noqa: F401
from app.modules.practicas.models import Practica            # noqa: F401
from app.modules.turnos.models import Turno, TurnoPractica   # noqa: F401
```

Los imports son por efecto: registran las clases en `SQLModel.metadata`. Para que un olvido no se manifieste como un error de FK a mitad del seed, el script **verifica antes del DDL** que `SQLModel.metadata.tables` contenga exactamente las seis tablas esperadas y, si falta alguna, aborta con mensaje explícito (código `2`) diciendo cuál falta. Alternativa descartada: `import app.modules...` sin nombrar símbolos; funciona igual, pero el `# noqa: F401` con nombres concretos documenta qué se está registrando.

### 4. `drop_all` → `create_all` → seed, sin Alembic — [KB] DD-01

La consigna excluye Alembic y el esquema se materializa desde los modelos (DD-01). `drop_all` borra las tablas que conoce el metadata; `create_all` las vuelve a crear con todas sus restricciones e índices y **reinicia las secuencias**. Ese reinicio es lo que hace barato el contrato de ids (Decisión 6).

- **Orden de borrado**: SQLAlchemy ordena las tablas por dependencia de FK, así que `drop_all` no choca con las FK. Depende de que el metadata esté completo (Decisión 3).
- **Objetos fuera del metadata**: si alguien creó a mano una tabla que referencia a una de las seis, `drop_all` falla con un error de dependencia. No se parchea con `DROP SCHEMA CASCADE`: el script falla con mensaje explícito y la salida es `DROP DATABASE` + `CREATE DATABASE`, que es justamente el escenario de borde de la spec.

### 5. Todo el reinicio en una sola transacción — [DECISIÓN]

`drop_all`, `create_all`, el seed y la sincronización de secuencias corren en **una única transacción** sobre **una única conexión**:

```
async with AsyncSession(engine) as session:
    async with session.begin():
        conn = await session.connection()
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        ... seed ...
```

- **Por qué**: la KB no lo especifica (US-018 y el Flujo 9 solo dicen "borra, crea, carga"), pero el mismo criterio de RN-23 (*todo o nada*) aplica acá: el evaluador no puede quedarse con una base sin tablas o con el seed a medias. PostgreSQL ejecuta **DDL transaccional**, así que un fallo en el seed revierte también el `drop_all`/`create_all` y deja la base **exactamente como estaba**.
- **Alternativa descartada**: `async with engine.begin()` para el DDL y una sesión aparte para el seed. Son dos transacciones: si el seed falla, la base queda vacía (tablas creadas, sin datos) y el estado previo se perdió. Es precisamente lo que la spec prohíbe.
- **Alternativa descartada**: commit por bloque (dueños, mascotas, …). Deja estados intermedios observables y multiplica los puntos de fallo.
- **`EXPECTED_TABLES`**: la verificación de la Decisión 3 se hace antes de abrir la transacción, para no ensuciar el mensaje de error.

### 6. Ids explícitos + `setval` para que el próximo turno reciba 2 — [DECISIÓN]

El seed declara los ids en el código (`duenio` 1 y 2, `ficha_duenio` 1, `mascota` 1–3, `practica` 1–4, `turno` 1) y, **después de insertar**, resincroniza la secuencia de cada tabla con `pg_get_serial_sequence`:

```sql
SELECT setval(pg_get_serial_sequence('turno', 'id'), (SELECT max(id) FROM turno), true);
```

Con `is_called = true`, el siguiente `nextval` devuelve `max(id) + 1`; con `turno.id` en 1, el próximo turno recibe **2**. Se aplica igual a `duenio`, `ficha_duenio`, `mascota` y `practica` —una tabla con ids explícitos y secuencia sin sincronizar rompe el **primer** `POST` de cualquier módulo con un 409 por PK repetida, y ese síntoma aparecería recién en [03]/[04]/[05]/[06], lejos de la causa—. `turno_practica` no tiene secuencia (PK compuesta).

- **Por qué ids explícitos**: el contrato "duenio 1 con ficha, duenio 2 sin ficha, mascota 1 = Toby, práctica 1 = Consulta, práctica 3 = Vacuna antirrábica" es un requisito verificable, y con ids explícitos se lee en el archivo y no depende del **orden de inserción** ni del estado previo de las secuencias. Un seed que dependa del autoincremento se rompe en silencio el día que alguien agregue una práctica en el medio de la lista.
- **Alternativa descartada**: dejar que el autoincremento asigne todo. Funciona hoy (después de `drop_all`/`create_all` las secuencias arrancan en 1 y el orden de inserción es fijo), pero el acoplamiento es implícito y el requisito "mascota 1 = Toby" quedaría garantizado por casualidad.
- **Detalle de PostgreSQL — `setval` no se revierte**: los avances de secuencia no son transaccionales. Como el `setval` corre sobre la secuencia **creada en esta misma transacción**, un rollback la descarta junto con la tabla recreada y restaura la anterior con su estado; no hay fuga hacia el estado previo. Aun si la hubiera, el requisito que la spec protege es "no dejar la base a medio poblar", y una secuencia adelantada no deja datos inconsistentes: la próxima ejecución vuelve a recrear todo. La corrección **no** depende del rollback de secuencias.
- **Fallo explícito**: si `pg_get_serial_sequence` devolviera `NULL` (columna sin secuencia, por ejemplo si [02] cambiara a ids asignados por la app), el `setval` falla y el script aborta con código `2` en vez de seguir con una secuencia desincronizada.
- **Cómo se verifica, y cómo NO**: `nextval` **no es transaccional** —un `ROLLBACK` no devuelve el valor consumido—, así que ninguna verificación, tarea ni caso de prueba puede llamar `nextval` sobre las secuencias reales: el propio acto de comprobar dejaría la secuencia adelantada y el próximo turno recibiría `3` en lugar de `2`. La verificación es de **solo lectura**, con `SELECT last_value, is_called FROM turno_id_seq;` → `1, true`. Con `is_called = true`, el próximo `nextval` es `last_value + 1` = `2`, y ese valor se **infiere** de las columnas de la secuencia sin gastarlo. La comprobación definitiva, cuando [06] exista, es un `POST /turnos/` real que devuelva `"id": 2`.

### 7. Seed concreto y por qué esos valores — [KB] `04_modelo_de_datos.md` §Seed data inicial, [DECISIÓN]

| Tabla | `id` | Datos | Origen |
|---|---|---|---|
| `duenio` | 1 | "Ana Gómez" · `ana.gomez@ejemplo.com` · **con ficha** | [KB] "1: con ficha" |
| `duenio` | 2 | "Bruno Díaz" · `bruno.diaz@ejemplo.com` · **sin ficha** | [KB] "2: sin ficha" |
| `ficha_duenio` | 1 | `duenio_id` 1 · teléfono `1145550001` · dirección "Av. Ficticia 100" | [KB] "uno con ficha"; valores ficticios |
| `mascota` | 1 | **Toby** · `perro` · `duenio_id` 1 | [KB] obligatorio |
| `mascota` | 2 | Michi · `gato` · `duenio_id` 1 | [KB] "dos mascotas más (una del dueño 1 o 2)" |
| `mascota` | 3 | Rocco · `perro` · `duenio_id` 2 | ídem |
| `practica` | 1 | **Consulta** · `15000.00` | [KB] obligatorio |
| `practica` | 2 | Desparasitación · `8000.00` | [KB] precio a elección |
| `practica` | 3 | **Vacuna antirrábica** · `12000.00` | [KB] obligatorio |
| `practica` | 4 | Castración · `35000.00` | [KB] "una práctica más" |
| `turno` | 1 | `mascota_id` 1 · `motivo` "Control anual" · `total` `27000.00` · fecha fija | [KB] "de una mascota existente, con 2 prácticas" |
| `turno_practica` | (1, 1) | `precio_unitario` `15000.00` | [KB] RN-06 |
| `turno_practica` | (1, 3) | `precio_unitario` `12000.00` | [KB] RN-06 |

- **Turno 1 con las prácticas 1 y 3**: es la combinación del ejemplo de la consigna, así el seed ejercita el mismo `total` (`27000.00`) que [06] debe reproducir en el alta, y la verificación es directa. No colisiona con el caso C-06: la PK es `(turno_id, practica_id)`, el alta crea el turno 2 con las mismas prácticas y eso es válido.
- **Fecha fija, no `now()`**: `datetime(2026, 11, 12, 13, 30, tzinfo=timezone.utc)` (el mismo instante que `2026-11-12T10:30:00-03:00` del ejemplo, SU-02). Con `now()` cada ejecución dejaría datos distintos y la idempotencia dejaría de ser "estado idéntico" para pasar a ser "mismos conteos".
- **Valores de las prácticas 2 y 4**: la KB no los fija. Se eligen precios ficticios distintos y `> 0` (RN-04) para que el catálogo no sea monótono. Si la cátedra los fijara, se cambian solo estas constantes.
- **Nada real**: nombres, emails, teléfono y dirección son inventados; el dominio `@ejemplo.com` lo deja claro y no roza datos de personas.

### 8. Dinero con `Decimal`, nunca `float` — [KB] DD-06, RN-06

Las constantes se escriben como `Decimal("15000.00")`, jamás `15000.0` ni `Decimal(15000.0)` —`Decimal(float)` arrastra el error binario del `float`—. `turno.total` se **calcula**: `sum((linea.precio_unitario for linea in lineas), Decimal("0.00"))`, no se escribe `27000.00` como literal, porque el seed debe modelar la regla que [06] va a implementar (RN-06) y un literal que no coincida con las líneas rompería la coherencia sin que nadie lo note. Escala 2 en `NUMERIC(10,2)`/`NUMERIC(12,2)`: los valores del seed son exactos y no requieren `quantize`.

### 9. Orden de inserción: el que impone el grafo de FK — [KB] ERD

`duenio` (1, 2) → `ficha_duenio` (1) → `mascota` (1, 2, 3) → `practica` (1–4) → `turno` (1) → `turno_practica` ((1,1) y (1,3)).

- Las FK **no** son diferibles, así que el padre tiene que existir antes del hijo dentro de la transacción. `turno` va antes que `turno_practica` por la FK `turno_id`; `practica` antes que `turno_practica` por `practica_id`.
- **Alternativa descartada**: declarar las FK `DEFERRABLE INITIALLY DEFERRED` para insertar en cualquier orden. Cambiaría el esquema de [02] (fuera de alcance) y no aporta nada: el orden correcto es trivial de escribir.
- Los objetos se arman como instancias de los modelos reales (`Duenio`, `FichaDuenio`, `Mascota`, `Practica`, `Turno`, `TurnoPractica`) y se agregan con `session.add_all(...)`; **no** se escribe SQL de `INSERT` a mano. Ventaja: si un nombre de columna o un tipo cambia en los modelos, el seed rompe en desarrollo y no en la corrección. La única SQL cruda es el `setval` de la Decisión 6.

### 10. Idempotencia por reconstrucción, no por "upsert" — [KB] US-018, [DECISIÓN]

No hay `SELECT` previos del tipo "¿ya existe?", ni `ON CONFLICT`, ni borrados selectivos: `drop_all` es el mecanismo. Es el mismo principio de DD-03 aplicado al seed —la garantía viene de la base (el esquema se recrea entero), no de preguntar antes—. Corolario: la segunda ejecución no depende del contenido previo ni del orden en que hayan quedado las secuencias.

### 11. Fallo legible: mensajes en español y códigos de salida — [DECISIÓN]

La KB no define códigos de salida para el script. Se fijan así:

| Código | Situación | Mensaje |
|---|---|---|
| `0` | Reinicio completo | resumen de lo cargado (conteos por tabla) |
| `1` | `DATABASE_URL` ausente | el `FATAL` de `app/core/config.py`, heredado sin duplicar lógica |
| `2` | Conexión rechazada o error de ejecución (DDL, seed, `setval`) | una línea con qué falló y qué hacer, más el tipo de excepción |

- **Sin credenciales**: la URL se imprime con `engine.url.render_as_string(hide_password=True)`; el mensaje nunca incluye la contraseña (espíritu de RN-24).
- **Sin traceback como única salida**: se captura la excepción, se imprime el mensaje legible y se sale con `2`. Para diagnóstico se incluye `type(exc).__name__` y el primer renglón del mensaje del driver, que es lo que permite distinguir "no such host" de "password authentication failed" sin volcar el stack completo.
- **Antes de destruir**: se imprime el destino enmascarado (`Reiniciando <host>/<base> ...`) para que quede en la consola —y en la evidencia— contra qué base se corrió.
- **Siempre `dispose()`**: el cierre del motor va en un `finally`, para no dejar conexiones colgadas cuando el proceso sale por error.

### 12. `asyncio.run` sobre un `main()` async, sin `async def` sueltas — [KB] reglas duras del proyecto

Todo lo que hace I/O es `async def` (`main`, helpers que ejecutan SQL con la sesión) y el punto de entrada es `asyncio.run(main())`. Type hints en todas las funciones (`-> None`, `AsyncSession`, `Decimal`). `snake_case` en archivos, funciones y variables; `PascalCase` solo para los modelos que se instancian.

### 13. Lo que NO se hace, aunque sea tentador — [DECISIÓN]

| Tentación | Por qué no | Dónde iría |
|---|---|---|
| Agregar `echo:` a `crear_motor` para silenciar el seed | Toca `app/core/database.py` (archivo ajeno a este change, Decisión 1) | change propio de Mariano |
| Refactorizar los cuatro `models.py` para exponer constantes del seed | Archivos de [02], ya archivado; nadie más los toca | no |
| Crear endpoints o un `POST /admin/reset` | La tabla de endpoints de la consigna no lo incluye | no |
| Añadir `faker`, `pytest` o `alembic` a `requirements.txt` | Dependencias innecesarias; Alembic está excluido (DD-01) | no |
| Versionar el `.env` o poner la URL real en el código | RN-24: la URL sale del entorno | no |

## Riesgos / Trade-offs

| Riesgo | Mitigación |
|---|---|
| El script se ejecuta contra una base distinta de la que usa la API (SU-04) y destruye datos que no correspondía tocar. | Una sola fuente de configuración (`app.core.config`), sin parámetros alternativos, y mensaje con el destino enmascarado antes de borrar. El riesgo residual (dos `.env` en directorios distintos) es el mismo que ya tiene la app. |
| Secuencia de `turno.id` desincronizada → el primer alta posterior falla con 409 por PK repetida, lejos de la causa. | `setval(..., max(id), true)` para las cinco tablas con id explícito y verificación explícita y **de solo lectura**: `SELECT last_value, is_called FROM turno_id_seq;` → `1, true` (implica próximo `nextval` = 2). |
| Verificar la secuencia con `nextval` "protegido" por un `ROLLBACK`. | **No hacerlo**: `nextval` no es transaccional, el valor consumido no se devuelve y la secuencia quedaría en 2 → el próximo turno recibiría 3, rompiendo el contrato de la spec. La verificación usa `last_value`/`is_called`, que no modifica la secuencia. |
| `setval` no se revierte con el rollback. | Corre sobre la secuencia creada en la misma transacción, que el rollback descarta junto con la tabla; la corrección no depende de revertir secuencias. |
| `drop_all` falla si hay objetos fuera del metadata que referencian las tablas. | Error explícito con código `2`; salida documentada: `DROP DATABASE` + `CREATE DATABASE` (escenario de borde de la spec). |
| Olvidar importar un `models.py` y crear un subconjunto de tablas. | Verificación previa de que el metadata contiene exactamente las seis tablas (Decisión 3), con mensaje que dice cuál falta. |
| `echo=True` hace que la salida del seed sea muy verbosa. | Aceptado (Decisión 2). No se toca `database.py`; la evidencia del caso C-07 sigue funcionando igual. |
| Datos del seed que no coinciden con lo que esperan los casos de [10]. | Todos los ids y precios que usan los ejemplos del enunciado quedan fijados en la spec y se verifican en `tasks.md`; lo único a elección (prácticas 2 y 4, mascotas 2 y 3) no aparece en ningún ejemplo. |
| La fecha fija del turno 1 envejece (queda en el pasado). | Es un dato de ejemplo, no una regla de negocio; la consigna usa una fecha de `2026-11-12` en su propio ejemplo. Un `now()` rompería la reproducibilidad. |

## Plan de migración / rollback

No hay migraciones (DD-01). El "despliegue" es agregar un archivo ejecutable; la base la gestiona el propio script.

- **Aplicación**: con `02` mergeado y la rama al día, crear `reiniciar.py`; `python reiniciar.py` sobre la base de `.env`; verificaciones de `tasks.md` (conteos, ids, turno, secuencia, doble corrida, códigos de salida).
- **Rollback**: borrar `reiniciar.py`. La base queda como la dejó la última ejecución; si se necesita el esquema sin datos, se ejecuta `drop_all`/`create_all` con el script temporal de [02]. No hay datos productivos: es una base de cátedra.
- **Orden respecto del roadmap**: [06] depende de este change porque su caso de prueba se apoya en el seed (mascotas y prácticas ya cargadas). Hasta que `reiniciar.py` exista, [06] solo se puede probar con datos insertados a mano.

## UI Mockups

`Decision: no (no UI)`. Este change no toca pantallas, componentes ni estilos: es un script de línea de comandos sin interfaz gráfica. No aplica el gate de mockups ni el de sistema de diseño.

## Preguntas abiertas

Ninguna que bloquee el apply. Quedan dos puntos que la KB no fija y que se resolvieron como decisión propia (arriba): los valores de las prácticas 2 y 4 (Decisión 7) y los códigos de salida `1`/`2` (Decisión 11). Si la cátedra los fijara distinto, el cambio se limita a constantes del script y a un escenario de la spec; ni el enfoque ni el desglose de tareas se modifican.
