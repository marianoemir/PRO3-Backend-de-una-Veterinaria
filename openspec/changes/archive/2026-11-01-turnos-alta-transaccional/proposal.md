# Propuesta: turnos-alta-transaccional

## Why

Los changes [01] `fundacion-proyecto`, [02] `modelos-y-esquema` y [09] `reiniciar-y-seed` ya están archivados: la API levanta, las seis tablas existen y `python reiniciar.py` deja datos reproducibles (mascota 1 = Toby, práctica 1 = Consulta `15000.00`, práctica 3 = Vacuna antirrábica `12000.00`, próximo turno con `id = 2`). Pero **no hay forma de reservar un turno**: `app/modules/turnos/{schemas,service,router}.py` siguen vacíos y `POST /turnos/` no existe.

Es el endpoint más delicado del trabajo práctico (Ej. 4, 15 % de la nota) porque en una sola petición combina cuatro cosas que ningún otro endpoint combina: **dos tablas escritas de forma atómica** (RN-23), **un dato que se copia de otra tabla** (RN-06, DD-07), **una PK compuesta que rechaza duplicados** (RN-07) y **una FK que rechaza una mascota inexistente**. Si el alta guarda el turno y falla al guardar sus prácticas, la base queda inconsistente; si el precio lo manda el cliente, el turno queda con un importe inventado.

Es además la dependencia directa de [07] `turnos-lecturas-y-baja` y uno de los casos que [10] ejecuta (C-04 y C-06).

## What Changes

- **`app/modules/turnos/schemas.py` (nuevo contenido)**: DTO de entrada `TurnoCreate` (`mascota_id`, `fecha`, `motivo`, `practicas` con **al menos una**), DTO anidado `TurnoPracticaCreate` (solo `practica_id`) y DTO de salida `TurnoRead` con **vistas resumidas propias de este módulo** (`MascotaResumenRead`, `TurnoPracticaRead`: `practica_id`, `nombre`, `precio_unitario`; **sin** id de fila, DD-11). Ni `precio` ni `total` en la entrada (RN-06); `total` y los importes salen como string decimal (DD-06); `fecha` de salida normalizada a UTC (SU-02). Ningún DTO se importa de otro módulo.
- **`app/modules/turnos/service.py` (nuevo contenido)**: `crear_turno(session, datos)` en **una sola transacción**: lee del catálogo las prácticas pedidas, copia `precio` → `precio_unitario`, calcula `total` con `Decimal`, persiste `Turno` + `TurnoPractica` y devuelve el turno con su mascota y sus prácticas **con carga anticipada declarada**. Si alguna práctica no existe → `rollback()` → conflicto de negocio; si la base rechaza (`IntegrityError`) → `rollback()` → conflicto. En ningún caso queda guardado el turno ni ninguna fila hija (RN-23).
- **`app/modules/turnos/router.py` (nuevo contenido)**: `POST /turnos/` (`async def`, `Depends(get_session)`) que delega en el service y traduce el resultado al contrato HTTP: **201** con `TurnoRead`, **409** ante conflicto de negocio o rechazo de la base, **422** cuando el cuerpo no cumple el contrato (lista vacía incluida).
- **Sin** cambios en `models.py`, `app/core/**`, `app/main.py`, `reiniciar.py`, `requirements.txt`, `env.example` ni en ningún otro módulo. El `APIRouter` de `turnos` ya está incluido en `app.main` sin prefijo, así que el prefijo `/turnos` se declara en el propio router (SU-05).

**BREAKING**: ninguno. Los tres archivos están vacíos (o contienen solo `router = APIRouter()`), no hay contrato previo que romper y ningún otro módulo los importa.

## Alcance

| ¿Qué incluye? | ¿Qué queda fuera? |
|---|---|
| `POST /turnos/` con su DTO de entrada, su DTO de salida y sus vistas resumidas propias | `GET /turnos/{id}` y `DELETE /turnos/{id}`: son del change [07] |
| Transacción única turno + `turno_practica`, copia de precio, cálculo de `total` con `Decimal`, `rollback()` y 409 en los tres rechazos | Casos de prueba `.http`/`.sql`, evidencia de C-04 y C-06 y `test/**`: son del change [10] |
| Respuesta armada con carga anticipada declarada, `fecha` en UTC y sin id de fila en las prácticas | `run`/`run_sync` de cualquier tipo, migraciones, auth, repositorios, colas, Docker y CI (fuera de alcance global) |
| Mensajes de error propios en español para cada 409 | Cambiar precios, prácticas, mascotas o el seed: cualquier ajuste de datos va por [09] o por [04]/[05] |

El alcance de archivos es **literal**: `app/modules/turnos/schemas.py`, `app/modules/turnos/service.py` y `app/modules/turnos/router.py`. Si durante el apply aparece la tentación de tocar `app/modules/turnos/models.py` (por ejemplo para renombrar una restricción), eso es del change [02] y va por otro change.

## Capabilities

### New Capabilities

- `turnos`: reserva de un turno con sus prácticas como una operación atómica — el servidor copia el precio vigente del catálogo, calcula el total, rechaza prácticas inexistentes o repetidas y mascotas inexistentes sin dejar nada guardado, y devuelve el turno con su mascota y sus prácticas en un contrato estable (importes decimales como string, fecha en UTC, sin id de fila en las prácticas).

### Modified Capabilities

Ninguna. `modelo-de-datos` describe el esquema y `reinicio-de-base-datos` el estado de partida; este change **no cambia el comportamiento especificado** por ninguna de las dos: agrega el endpoint que las consume. No se tocan sus requisitos ni sus escenarios.

## Reglas de negocio cubiertas

- **RN-05** — el turno se reserva con sus prácticas y tiene **al menos una**: viajan en el cuerpo del alta y la lista vacía responde **422**.
- **RN-06** — el precio se **copia** del catálogo al reservar y el `total` lo calcula el servidor: ni el precio ni el total viajan en el DTO de entrada.
- **RN-07** — una misma práctica no aparece dos veces en un turno: lo garantiza la PK compuesta `(turno_id, practica_id)`; el service traduce el rechazo a **409**.
- **RN-12** — códigos del contrato: **201** al crear, **409** si la base o una regla de negocio rechazan la escritura, **422** si el cuerpo no cumple el contrato.
- **RN-14** — la respuesta incluye relaciones solo con **carga anticipada declarada** en la misma consulta (`joinedload` para la mascota, `selectinload` + `joinedload` anidado para las prácticas).
- **RN-17** — handler `async def`; el service recibe la `AsyncSession` por parámetro (DD-02) y no hay ninguna llamada bloqueante.
- **RN-23** — *todo o nada*: una práctica inexistente no guarda **nada**, ni el turno ni ninguna de sus prácticas, en una sola transacción.
- **DD-06** — dinero con `Decimal`, `NUMERIC` en la base y string decimal en JSON (`"27000.00"`).
- **DD-07** — el precio se congela en `turno_practica`: un cambio posterior del catálogo no altera los turnos ya reservados.
- **DD-11** — el turno devuelve `practica_id`, `nombre` y `precio_unitario`, **sin** id de fila.
- **DD-12** — validaciones mínimas: `motivo` obligatorio, `fecha` sin validación contra el pasado ni contra duplicados, sin reglas nuevas.
- **SU-02** — la `fecha` se devuelve en UTC (`...Z`) aunque la entrada venga con offset `-03:00`.
- **DD-13** — las FK sin `ON DELETE` especificado siguen en `NO ACTION`; este change no toca el esquema.

## Impact

- **Código afectado**: `app/modules/turnos/schemas.py`, `app/modules/turnos/service.py` y `app/modules/turnos/router.py`. Ningún otro archivo se modifica. Estos tres archivos tienen dueño único (Mariano, `CHANGES.md` §Archivos compartidos), igual que el resto de `app/modules/turnos/*`.
- **APIs**: se publica **`POST /turnos/`** con cuerpo `{"mascota_id", "fecha", "motivo", "practicas": [{"practica_id"}]}` y respuesta `{"id", "fecha", "motivo", "total", "mascota": {id, nombre, especie}, "practicas": [{practica_id, nombre, precio_unitario}]}`; códigos 201, 409 y 422. No se agregan ni se modifican otras rutas.
- **Base de datos**: sin cambios de esquema. Cada alta escribe 1 fila en `turno` y *n* filas en `turno_practica`, o ninguna de las dos cosas.
- **Dependencias**: ninguna nueva. `fastapi`, `sqlmodel`, `sqlalchemy[asyncio]` y `asyncpg` ya están en `requirements.txt`; la discriminación de los rechazos usa el `sqlstate` que expone el driver, sin importar `asyncpg` en el service.
- **Changes que desbloquea**: [07] `turnos-lecturas-y-baja` (depende de este) y, a través de él, [10] `pruebas-http-y-evidencia` (casos C-04 y C-06) y [11] `readme-y-entrega`.
- **Riesgo principal — atomicidad**: que el turno se guarde y las prácticas no (o al revés). Se ataca con una única transacción sobre una única sesión y `rollback()` explícito en los tres caminos de fallo; se verifica contando filas antes y después de cada 409.
- **Riesgo secundario — fidelidad del contrato**: que la respuesta dependa de estado en memoria o de carga perezosa y falle con `MissingGreenlet`, o que la `fecha` salga con offset local en lugar de `Z`. Se ataca releyendo el turno recién creado con carga anticipada y normalizando la fecha a UTC; se verifica contra el ejemplo textual de la consigna.
- **Riesgo operativo — secuencia del turno**: el `"id": 2` esperado depende de que la base esté en el estado del seed. El smoke se corre **después** de `python reiniciar.py`, y **nunca** se comprueba nada con `nextval` (no es transaccional y consume ids).
