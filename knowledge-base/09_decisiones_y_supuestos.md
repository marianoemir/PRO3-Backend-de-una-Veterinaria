# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Esquema creado con `create_all`, sin Alembic
**Decisión**: el esquema se crea desde los modelos con `SQLModel.metadata.create_all`.
**Contexto**: TP integrador de las unidades 1 a 4.
**Alternativas consideradas**: Alembic (migraciones versionadas).
**Justificación**: la consigna excluye Alembic explícitamente.
**Trade-offs aceptados**: cualquier cambio de modelo exige `reiniciar.py`; no hay historial de migraciones.

### DD-02 — Lógica en `service` que recibe la sesión, sin repositorios ni UoW
**Decisión**: `service.py` recibe `AsyncSession` como parámetro y ejecuta la lógica.
**Contexto**: la consigna fija esta organización.
**Justificación**: el alcance evaluado es FastAPI + SQLModel, no patrones de persistencia.
**Trade-offs aceptados**: acoplamiento del service a SQLAlchemy.

### DD-03 — Conflictos resueltos por la base, no por consulta previa
**Decisión**: se escribe y se captura `IntegrityError` → `rollback` → 409.
**Contexto**: sección 4.10 de la cátedra; ventana de carrera entre "¿existe?" y el `INSERT`.
**Alternativas consideradas**: verificar con `SELECT` antes de escribir.
**Justificación**: la base es la única garante atómica de unicidad y de FK.
**Trade-offs aceptados**: el mensaje de error depende de la restricción violada.

### DD-04 — Carga anticipada explícita en cada consulta de lectura
**Decisión**: `joinedload` para relaciones «a uno», `selectinload` para colecciones.
**Contexto**: asincronía + objetivo de evitar N+1.
**Justificación**: la carga perezosa no es lenta en async: falla con `MissingGreenlet`.
**Trade-offs aceptados**: consultas más explícitas y algo más largas.

### DD-05 — El borrado en cascada lo decide la base
**Decisión**: `passive_deletes` en `Turno.practicas`; el ORM no vacía ni borra las filas hijas.
**Contexto**: RN-09 exige `ON DELETE CASCADE` en la base.
**Justificación**: una sola fuente de verdad para el borrado; evita que el ORM emita `UPDATE`/`DELETE` extra.
**Trade-offs aceptados**: la sesión debe tratar el objeto como borrado tras el `commit`.

### DD-06 — Dinero con `Decimal`, nunca `float`
**Decisión**: `NUMERIC(10,2)` / `NUMERIC(12,2)` y `Decimal` en Python; en JSON se serializa como string decimal.
**Contexto**: sección 2.7 y ejemplos de respuesta de la consigna (`"total": "27000.00"`).
**Justificación**: exactitud en importes.
**Trade-offs aceptados**: hay que castear en los DTO y en los cálculos.

### DD-07 — El precio se congela en la relación, no en la práctica
**Decisión**: `turno_practica.precio_unitario` copia el precio del catálogo al reservar; `total` se calcula en el servidor.
**Contexto**: RN-06; un cambio posterior de precio no altera turnos ya reservados.
**Trade-offs aceptados**: duplicación deliberada del precio (histórico).

## Supuestos inferidos

### SU-01 — `consultar_stock` se ejecuta en un hilo aparte
**Supuesto**: la llamada sincrónica se offloadea con `asyncio.to_thread` (o equivalente del threadpool), sin modificar `cliente.py`.
**Origen**: "La cátedra entrega el módulo… sin modificarla" + objetivo de no bloquear el event loop.
**Riesgo si es falso**: C-09 fallaría (el health quedaría bloqueado ~1 s por consulta).
**Cómo validar**: correr C-09 con tres consultas simultáneas y medir la latencia de `/health/live`.

### SU-02 — `fecha` se devuelve en UTC
**Supuesto**: la respuesta serializa `fecha` en UTC (`...Z`), aunque la entrada venga con offset `-03:00`.
**Origen**: el ejemplo de la consigna muestra entrada `-03:00` y salida `Z`.
**Riesgo si es falso**: discrepancia de formato en la corrección.
**Cómo validar**: comparar la respuesta de C-06 con el ejemplo textual de la consigna.

### SU-03 — Un `PATCH` de dueño con email repetido responde 409
**Supuesto**: aplicar la tabla de códigos del endpoint (`200, 404, 409, 422`) implica que la colisión de email en el update también es 409.
**Origen**: tabla de endpoints de la consigna.
**Riesgo si es falso**: código incorrecto en un caso no listado explícitamente.
**Cómo validar**: consultar a la cátedra (ver [10_preguntas_abiertas.md](10_preguntas_abiertas.md)).

### SU-04 — `reiniciar.py` usa el mismo `DATABASE_URL` que la app
**Supuesto**: el script lee la configuración del mismo `.env` y opera sobre la misma base.
**Origen**: la consigna pide "deja la base en un estado conocido" sin especificar otro origen de configuración.
**Riesgo si es falso**: el script apuntaría a una base distinta de la que usa la API.
**Cómo validar**: correr `reiniciar.py` y luego `GET /mascotas/`.

### SU-05 — Los nombres de endpoints llevan barra final donde la consigna la muestra
**Supuesto**: se respetan literalmente las rutas de la tabla (`/duenios/`, `/mascotas/`, `/practicas/`, `/turnos/`) y las de detalle sin barra final (`/duenios/{id}`).
**Origen**: "Endpoints de referencia".
**Riesgo si es falso**: redirecciones 307 que confunden los casos de prueba.
**Cómo validar**: correr los `.http` y verificar que no haya redirects.

## Decisiones del equipo (31/10/2026)

> La consigna no las define. Las tomó el equipo para no bloquear la entrega. Son **decisiones propias**, no reglas de la cátedra: se registran en el `design.md` del change que las usa y se mencionan en el README.

### DD-08 — `DuenioUpdate` acepta `nombre` y `email`, ambos opcionales
**Decisión**: `DuenioUpdate` tiene `nombre: str | None` y `email: str | None`. El PATCH aplica solo lo enviado (`exclude_unset`). Un cuerpo vacío `{}` responde 200 sin cambios. Un email que colisiona responde 409 (la tabla de códigos del PATCH en la consigna incluye 409).
**Justificación**: son las dos columnas editables de `duenio`; `id` no se modifica.

### DD-09 — El email no se normaliza
**Decisión**: se guarda tal cual llega; el `UNIQUE` de PostgreSQL es sensible a mayúsculas, así que `A@x.com` y `a@x.com` son distintos.
**Justificación**: normalizar sería agregar una regla que la consigna no enuncia; la garantía es la del `UNIQUE` en la base. Se documenta en el README.

### DD-10 — `GET /duenios/{id}/mascotas` devuelve una lista simple
**Decisión**: arreglo JSON de `MascotaRead` (vacío → `[]`, 200); dueño inexistente → 404. El envoltorio paginado solo aplica a `GET /mascotas/` (RN-13).
**Justificación**: la consigna exige paginación únicamente para el listado de mascotas.

### DD-11 — El detalle de turno no incluye id de fila de `turno_practica`
**Decisión**: cada práctica del turno trae `practica_id`, `nombre` y `precio_unitario`, como el ejemplo de la consigna.
**Justificación**: `turno_practica` no tiene columna `id`; su PK es `(turno_id, practica_id)`.

### DD-12 — Validaciones mínimas de los DTO
**Decisión**: `especie` es texto libre, no vacío. `motivo` es obligatorio. `FichaCreate` exige `telefono` y `direccion`. No se valida `fecha` contra el pasado ni contra turnos duplicados. El `email` es `str`, sin validar formato.
**Justificación**: la consigna no pide más; agregar reglas es riesgo sin puntaje.

### DD-13 — `ON DELETE` sin especificar queda en el default de PostgreSQL
**Decisión**: `ficha_duenio.duenio_id`, `turno.mascota_id` y `turno_practica.practica_id` quedan con `NO ACTION`. No se agrega `CASCADE`.
**Justificación**: no hay endpoints para borrar mascotas ni prácticas, así que el caso no es alcanzable por la API (IN-02).

### DD-14 — `GET /health/ready`
**Decisión**: 200 con `{"estado": "listo", "base": "ok"}`; 503 con `{"estado": "no_disponible", "base": "error"}`.

### DD-15 — Paginación y organización de `test/`
**Decisión**: `page` y `size` son query params (`?page=&size=`). Orden por defecto de los listados: por `id` ascendente. Un archivo `.http` por caso (`test/caso_C-0X.http`) más `test/caso_C-08.sql`. `env.example` usa la base `veterinaria`. `cliente.py` se crea con el código exacto del enunciado.
