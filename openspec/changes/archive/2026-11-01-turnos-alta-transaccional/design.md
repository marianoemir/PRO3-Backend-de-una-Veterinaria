# Diseño: turnos-alta-transaccional

## Contexto

Ver `proposal.md` §Why. El estado de partida que condiciona el diseño:

- **Modelos completos ([02] archivado)**: `app/modules/turnos/models.py` declara `Turno` (`id`, `mascota_id` FK con índice, `fecha` `DateTime(timezone=True)`, `motivo`, `total` `NUMERIC(12,2)` con `CHECK total >= 0`) y `TurnoPractica` (PK compuesta `(turno_id, practica_id)`, `turno_id` FK `ON DELETE CASCADE`, `practica_id` FK con índice, `precio_unitario` `NUMERIC(10,2)` con `CHECK > 0`, **sin** `id`). `Turno.practicas` tiene `passive_deletes=True`.
- **Nombres reales de las restricciones** (consultados en `pg_constraint`, solo lectura, sobre este entorno): `turno_practica_pkey` (PK compuesta), `turno_mascota_id_fkey`, `turno_practica_practica_id_fkey`, `turno_practica_turno_id_fkey`, `ck_turno_total_no_negativo`, `ck_turno_practica_precio_unitario_positivo`.
- **Estado del seed ([09] archivado, verificado)**: `turno` tiene 1 fila y `turno_id_seq` está en `last_value = 1`, `is_called = true`. Por lo tanto el próximo alta legítima recibe **`id = 2`**, que es el contrato que la spec verifica. No se ejecutó ni se ejecutará `nextval` para comprobarlo (ver Decisión 13).
- **Los tres archivos están vacíos**: `turnos/schemas.py` y `turnos/service.py` en blanco, `turnos/router.py` solo `router = APIRouter()`. `app/main.py` ya incluye ese router **sin prefijo**, así que el prefijo `/turnos` se declara dentro del módulo (mismo patrón que `health`).
- **Conexión y sesión ya resueltas ([01])**: `get_session()` entrega una `AsyncSession` por petición desde `app.state.session_local`, con `expire_on_commit=False` y `echo=True` en el motor (RN-21, y `echo` habilita la evidencia de C-07 para [07]).
- **Entorno del equipo**: Windows + PowerShell, sin `psql`; la inspección SQL se hace en **pgAdmin** (Query Tool). La sesión de PostgreSQL tiene `TimeZone = America/Buenos_Aires`.

## Objetivos / No objetivos

**Objetivos**

- Que el alta sea **realmente atómica**: ni un turno sin sus prácticas, ni prácticas huérfanas, ni datos a medio guardar en ningún camino de error (RN-23).
- Que el **servidor** sea el único dueño de los importes: el precio se copia del catálogo y el total se calcula con `Decimal` (RN-06, DD-06, DD-07).
- Que los tres rechazos —práctica inexistente, práctica repetida, mascota inexistente— se distingan en el mensaje y en el origen de la garantía, y que **ninguno** deje rastro en la base.
- Que la respuesta sea estable y verificable: mismo contrato que el ejemplo de la consigna, `fecha` en UTC y sin id de fila (DD-11, SU-02).

**No objetivos**

- `GET /turnos/{id}` y `DELETE /turnos/{id}` (change [07]); casos `.http`, `.sql` y evidencia (change [10]); README (change [11]).
- Tocar `models.py`, `app/core/**`, `app/main.py`, `reiniciar.py` o cualquier otro módulo, aunque una mejora sea evidente (Decisión 1).
- Validar `fecha` contra el pasado o contra turnos duplicados, ni normalizar datos: son reglas que la consigna no enuncia (DD-12).
- Locks explícitos, reintentos, idempotencia por clave de cliente o `FOR SHARE`: no hay requisito que los pida.

## Decisiones

### 1. Alcance literal: tres archivos, ninguno más — [KB] CHANGES.md §Archivos compartidos

`app/modules/turnos/*` es de Mariano y este change solo cubre `schemas.py`, `service.py` y `router.py`. `models.py` es de [02] y no se toca ni para renombrar restricciones: los nombres reales ya existen y el service los usa por `sqlstate`, no por nombre (Decisión 6). Tampoco se toca `app/main.py`, que ya incluye el router.

### 2. Una sola transacción sobre una sola sesión, con `commit()`/`rollback()` explícitos — [KB] RN-23, DD-02

El service recibe la `AsyncSession` de la petición y ejecuta todo el alta sobre ella. La sesión abre la transacción de forma implícita en la primera sentencia (la lectura del catálogo) y la cierra con `commit()` al final o con `rollback()` en cada camino de error:

```
leer catálogo (abre la transacción)  →  construir objetos  →  flush()  →  releer para la respuesta  →  commit()
                                     ↘ práctica faltante: rollback() → 409
                                     ↘ IntegrityError:    rollback() → 409
```

- **Por qué no `async with session.begin()`**: `begin()` revierte solo, pero el manejo de errores queda repartido entre el `except` de afuera y el `__aexit__` del contexto, y el caso "práctica inexistente" necesita un `rollback()` explícito **antes** de levantar el conflicto (así lo pide CHANGES.md §[06] y así queda legible en el código). Con `commit()`/`rollback()` manuales hay un único lugar donde termina la transacción por cada camino.
- **La relectura para la respuesta ocurre antes del `commit()`** y pertenece a la misma transacción: lo que se devuelve es exactamente lo que se está por confirmar. Se relee con `flush()` ya ejecutado, así el `INSERT` del turno y de sus filas ya pasó por la base y `turno.id` está asignado.
- **`flush()` dentro del `try`**: las violaciones de PK y de FK se producen en el `INSERT`, no en el `commit()`. Hacer `flush()` explícito deja el `except IntegrityError` pegado a la sentencia que puede fallar, y permite releer el turno con su `id` antes de confirmar.
- **Alternativa descartada**: dos transacciones (una para el turno, otra para las prácticas) o un `commit()` por fila. Deja estados intermedios observables: exactamente lo que RN-23 prohíbe y lo que el caso C-04 verifica contando filas.

### 3. Leer el catálogo **antes** de escribir es correcto acá: la regla "sin consulta previa" no aplica — [KB] DD-03, RN-06, RN-23

La regla del proyecto —"nada de consultas previas del tipo *¿ya existe?*"— existe porque **entre la pregunta y la escritura hay una ventana de carrera**: otra petición puede escribir lo mismo y la única defensa atómica es que la base rechace la segunda (DD-03, consigna §4.10). Esa regla habla de **garantías**: `UNIQUE`, `FK` y `CHECK`. Acá no se está garantizando nada con un `SELECT`:

- **La garantía sigue siendo de la base.** Si la práctica desapareciera entre la lectura y el `INSERT` (o si la lectura trajera una fila obsoleta), la FK `turno_practica_practica_id_fkey` rechaza y el camino es el mismo: `IntegrityError` → `rollback()` → 409. La lectura **no reemplaza** a la restricción; convive con ella como segunda línea.
- **Lo que se busca no es un booleano, es un dato.** Para copiar `precio` a `precio_unitario` hace falta el precio, y el único lugar donde está es el catálogo. No hay forma de "escribir y ver qué pasa" con un importe que el cliente no manda: sin leer el catálogo no hay nada que escribir. Copiar datos es justamente lo que RN-06 y DD-07 mandan hacer.
- **La alternativa sería peor.** Si se omitiera la lectura y se dejara que la FK falle, el 409 por práctica inexistente se confundiría con el 409 por mascota inexistente y con el 409 por práctica repetida: los tres son `IntegrityError`, y el mensaje propio que exige RN-12 se perdería. Peor: sin precios no se puede calcular `total` antes de insertar, y `turno.total` es `NOT NULL`.
- **La lectura es parte de la misma transacción** que la escritura, así que el precio copiado y el turno confirmado son consistentes entre sí: no se puede confirmar un turno con un precio leído en otra transacción ya cerrada.
- **Cómo se distingue de un "pre-check" prohibido**: no se consulta "¿existe la mascota?" (eso lo decide la FK, y el service **no** hace ese `SELECT`), y no se consulta "¿existe ya este turno?". Se consulta el catálogo para obtener los importes. La prueba está en el código: si se borra la lectura, la operación no puede completarse con datos válidos; si se borra cualquiera de las restricciones, la operación sí se completa mal.

El 409 por práctica inexistente se emite **después** de `rollback()`, aunque todavía no se haya escrito nada: la lectura ya abrió una transacción y hay que cerrarla antes de responder.

### 4. Una fila de `turno_practica` por cada práctica **pedida**, no por cada fila encontrada — [KB] RN-07, [DECISIÓN]

La lectura del catálogo devuelve filas únicas (`WHERE id IN (...)` deduplica), pero la construcción de las filas hijas itera la **lista del DTO**, no el resultado de la consulta. Si se iterara lo leído, dos `{"practica_id": 1}` en la petición producirían **una sola** fila y el turno se guardaría con la práctica repetida colapsada: RN-07 quedaría violada en silencio, sin ningún 409.

Con la iteración sobre lo pedido, la petición repetida llega a la base con dos filas iguales, la PK compuesta `turno_practica_pkey` rechaza la segunda y el `IntegrityError` se traduce a 409. **La garantía la da la base**; el service solo garantiza que el intento llegue.

### 5. `Decimal` de punta a punta, y por qué el `CHECK` del total no puede fallar — [KB] DD-06, DD-07, RN-06

- `precio_unitario` se asigna con el `Decimal` que devolvió la base (`NUMERIC(10,2)`), sin pasar por `float` en ningún punto. `total` se calcula con `sum(..., Decimal("0.00"))` y se normaliza con `.quantize(Decimal("0.01"))` antes de asignarlo, para no depender de la escala que traiga la suma.
- En JSON los importes salen como **string** (`"27000.00"`): es el comportamiento de Pydantic v2 con `Decimal` en modo JSON, verificado en este entorno. No hace falta un `field_serializer` y no se agrega.
- El `CHECK total >= 0` no puede dispararse con un alta válida: todos los `precio_unitario` son mayores que cero porque el catálogo tiene `CHECK precio > 0` (RN-04), y la lista tiene al menos un elemento (RN-05). El `total` de un alta válida es estrictamente positivo. Si algún día se permitieran importes negativos, el rechazo sería un `IntegrityError` más y caería en el 409 genérico (Decisión 6).
- **Nada de precios en la entrada**: `TurnoPracticaCreate` declara solo `practica_id` y `TurnoCreate` no declara `precio` ni `total`. Si el cliente los manda, Pydantic los ignora (configuración por defecto): no se rechaza el cuerpo por campos de más —sería una validación que la consigna no enuncia— y el valor enviado nunca se usa (Decisión 10).

### 6. De `IntegrityError` a 409: discriminación por `sqlstate`, con mensajes propios — [KB] RN-12, DD-03

Los tres rechazos posibles del `flush()` se distinguen así:

| `sqlstate` | Restricción que lo produce | Mensaje al cliente |
|---|---|---|
| `23505` (unique) | `turno_practica_pkey` | la práctica está repetida en el turno |
| `23503` (foreign key) | `turno_mascota_id_fkey` | la mascota no existe |
| otro | cualquiera | no se pudo registrar el turno |

- **Por qué `sqlstate` y no `constraint_name`**: verificado en este entorno, el error que expone SQLAlchemy con el driver `asyncpg` trae `sqlstate` (`'23505'`, `'23503'`) pero `constraint_name = None`. Elegir por nombre de restricción habría producido siempre el mensaje genérico.
- **Por qué `23503` es "la mascota no existe"**: en esta transacción las filas de `turno_practica` se construyen solo con prácticas encontradas en el catálogo, así que `turno_practica_practica_id_fkey` no debería poder violarse; y `turno_practica_turno_id_fkey` se satisface porque SQLAlchemy inserta el turno antes que sus hijos. Queda la FK de la mascota. Además, el catálogo y las mascotas **no tienen endpoints de baja** (IN-02), así que no hay forma de que una práctica o una mascota desaparezcan entre la lectura y el `INSERT` por la API.
- **Por qué `23505` es "la práctica repetida"**: `turno` y `turno_practica` no tienen otra columna única; la única restricción de unicidad alcanzable es la PK compuesta (RN-07).
- **Mensaje propio, código correcto**: los tres casos son **409**, porque en los tres la base rechaza la escritura (RN-12). El texto es en español, nombra el problema y no expone la sentencia SQL ni el nombre interno de la restricción.
- **Consecuencia obligatoria**: `rollback()` **antes** de levantar el conflicto. Sin eso la sesión queda en estado fallido y la petición siguiente del mismo cliente —o el cierre de la sesión— arrastra el error.

### 7. La respuesta se arma releyendo el turno con carga anticipada — [KB] RN-14

Después del `flush()` y dentro de la misma transacción, el service relee el turno recién creado:

```python
select(Turno)
.where(Turno.id == turno_id)
.options(
    joinedload(Turno.mascota),
    selectinload(Turno.practicas).joinedload(TurnoPractica.practica),
)
```

Son **2 consultas** (`turno` + mascota en una, prácticas + práctica en otra), fijas, sin importar cuántas prácticas tenga el turno. Sumadas a la lectura del catálogo, el alta ejecuta **3 `SELECT`** más los `INSERT`.

- **Por qué no armar el DTO con los objetos en memoria**: `Turno.practicas` no está cargado en el grafo (las filas se construyeron aparte y `expire_on_commit=False` no obliga a nada), y el nombre de la práctica vive en `Practica`, no en la fila hija. Armar la respuesta "a mano" obligaría a mantener en memoria un mapa de nombres y precios en paralelo al estado persistido: dos fuentes de verdad que se desincronizan el día que alguien agregue un campo a la respuesta.
- **Por qué no hace falta otro `SELECT` para la mascota**: la FK la valida el `INSERT`; la mascota se lee acá **para la respuesta**, no como verificación previa. Si no existiera, el alta ya habría fallado antes de llegar a esta consulta.
- **Sin carga perezosa**: si alguien borra el `options(...)`, la primera lectura de `turno.mascota` en el esquema de respuesta falla con `MissingGreenlet`. La prueba de que no hay carga perezosa es esa: el código no puede "funcionar de casualidad" (RN-16).

### 8. Orden de las prácticas en la respuesta: ascendente por `practica_id` — [DECISIÓN]

La respuesta lista las prácticas ordenadas por `practica_id` ascendente, tanto si se arman desde la relectura como si se ordena la lista del DTO al construirla.

- **Por qué**: el orden de filas que devuelve PostgreSQL sin `ORDER BY` no está garantizado, y el orden de la petición no tiene por qué ser el de la respuesta. Ordenar hace la respuesta **determinista** y comparable entre corridas, y coincide con el criterio de listados ya adoptado por el equipo (DD-15: "orden por `id` ascendente").
- **Compatibilidad**: el ejemplo de la consigna pide las prácticas 1 y 3 en ese orden, que es el mismo que produce este criterio, así que el caso C-06 compara igual.
- **Alternativa descartada**: respetar el orden de la petición. Obliga a arrastrar el orden del DTO hasta el armado final sin que ninguna regla lo pida, y dos peticiones equivalentes devolverían respuestas distintas.

### 9. `fecha`: se normaliza a UTC y una fecha sin offset se interpreta como UTC — [KB] SU-02, [DECISIÓN]

- **Salida**: la `fecha` se normaliza con `.astimezone(timezone.utc)` antes de armar el DTO. Verificado en este entorno: Pydantic serializa un `datetime` en UTC como `2026-11-12T13:30:00Z` y uno con offset `-03:00` como `2026-11-12T10:30:00-03:00`. Normalizar es lo que produce la `Z` que la consigna muestra (SU-02), sin depender del offset de entrada ni de la zona de la sesión de PostgreSQL (que acá es `America/Buenos_Aires`).
- **Entrada sin offset**: se interpreta como UTC. Es una decisión propia, no una regla de la cátedra, y se documenta en el README.
  - **Por qué no rechazarla con 422**: la consigna no dice que la fecha deba traer offset; rechazarla sería agregar una validación que no está enunciada (DD-12).
  - **Por qué no dejarla al driver**: verificado en este entorno, `asyncpg` toma un `datetime` sin zona como **hora local del proceso** y lo convierte a UTC. El mismo cuerpo produciría instantes distintos en dos máquinas con zonas distintas: la respuesta dejaría de ser reproducible, y `fecha` es un dato que la spec verifica.
  - **Por qué UTC y no la zona de la veterinaria**: UTC es el único criterio que no depende del entorno; la API no tiene configuración de zona horaria y no se le va a agregar una por este endpoint.
- **Lo que no se hace**: no se valida contra el pasado ni contra turnos duplicados de la misma mascota (DD-12), y no se trunca ni se redondea la fecha.

### 10. DTOs propios del módulo y validaciones mínimas — [KB] RN-05, RN-10, RN-12, DD-11, DD-12

`turnos/schemas.py` define todo lo que necesita y **no importa DTO de otro módulo** (regla de CHANGES.md):

| DTO | Campos | Notas |
|---|---|---|
| `TurnoPracticaCreate` | `practica_id: int` | solo eso: ni `precio` ni `id` |
| `TurnoCreate` | `mascota_id: int`, `fecha: datetime`, `motivo: str`, `practicas: list[TurnoPracticaCreate]` con `min_length=1` | sin `id`, sin `total` |
| `MascotaResumenRead` | `id`, `nombre`, `especie` | vista resumida **propia** de `turnos` |
| `TurnoPracticaRead` | `practica_id`, `nombre`, `precio_unitario` | **sin** id de fila (DD-11) |
| `TurnoRead` | `id`, `fecha`, `motivo`, `total`, `mascota`, `practicas` | el orden de campos sigue el ejemplo de la consigna |

- **Lista vacía → 422**: `min_length=1` en `practicas` es el garante de RN-05 y lo resuelve FastAPI antes de ejecutar el handler; no llega ninguna sentencia a la base.
- **`motivo` obligatorio, sin mínimo de longitud**: la KB solo dice "obligatorio" (DD-12). Agregar "no vacío" sería una regla nueva; no se agrega.
- **`mascota_id` y `practica_id` sin `gt=0`**: no hay regla que exija ids positivos. Un id inexistente —0, negativo o enorme— cae donde corresponde: la mascota en el 409 por FK y la práctica en el 409 por inexistente. Agregar `gt=0` convertiría esos casos en 422 sin que nadie lo haya pedido.
- **Campos de más**: se ignoran (configuración por defecto de Pydantic). Rechazarlos con 422 sería una validación no enunciada y rompería el escenario "un total enviado por el cliente no se respeta".

### 11. El service importa el grafo completo de modelos que participa del alta — [KB] [02] §6, [DECISIÓN]

`turnos/models.py` referencia `"Mascota"` y `"Practica"` como cadenas y solo las importa bajo `TYPE_CHECKING`. Verificado en este entorno: importar únicamente `app.modules.turnos.models` y llamar a `configure_mappers()` falla con `InvalidRequestError: expression 'Mascota' failed to locate a name`.

Por eso `service.py` importa el grafo completo que este endpoint recorre: `app.modules/duenios/models.py` (`Duenio`), `app.modules/mascotas/models.py` (`Mascota`), `app.modules/practicas/models.py` (`Practica`) y `app.modules/turnos/models.py` (`Turno`, `TurnoPractica`). Con **tres** módulos (sin `Duenio`) el `configure_mappers()` falla igualmente: `Mascota.duenio` también necesita registrarse.

No es un import cosmético: sin el grafo completo, la primera consulta del endpoint falla al configurar los mappers. Es el mismo cuidado que [09] documentó para `reiniciar.py`, pero acá el import vive donde se usa.

### 12. El router declara su prefijo, responde 201 y traduce los conflictos — [KB] RN-12, RN-17, SU-05

- `router = APIRouter(prefix="/turnos", tags=["turnos"])`, porque `app/main.py` incluye el router sin prefijo (igual que `health`). La ruta se declara como `"/"` para que el camino publicado sea **`/turnos/`** con barra final, como en la tabla de endpoints (SU-05).
- El handler es `async def`, recibe `Depends(get_session)` y delega; no contiene lógica de negocio (DD-02). `status_code=201` y `response_model=TurnoRead`.
- Los conflictos se modelan como excepciones propias del módulo (`PracticaInexistente`, `TurnoConflicto`) y el router las traduce a `HTTPException(409, detail="...")`. Una excepción de dominio no es un `HTTPException` en el service: el service no conoce HTTP.
- **Ningún `try/except` genérico**: un error inesperado debe seguir siendo un 500 con su traza, no un 409 mentiroso.

### 13. Cómo se verifica el `id = 2`, y por qué nunca con `nextval` — [KB] [09] §4.2

Ninguna task, ningún smoke y ningún caso de prueba ejecuta `nextval` sobre `turno_id_seq`. En PostgreSQL **los avances de secuencia no son transaccionales**: un `SELECT nextval(...)` seguido de `ROLLBACK` deja la secuencia adelantada y el próximo turno real recibiría `3` en lugar de `2`, rompiendo justamente el contrato que se quería comprobar.

Las dos comprobaciones legítimas son:

1. **De solo lectura**: `SELECT last_value, is_called FROM turno_id_seq;` → `1, true` implica que el próximo `nextval` entrega `2`, sin consumirlo.
2. **La real**: el `POST /turnos/` del smoke, corrido **después de `python reiniciar.py`**, devuelve `"id": 2`. Ese valor se consume porque el turno se crea de verdad; por eso el smoke se corre sobre la base recién reiniciada y no dos veces seguidas esperando siempre `2`.

### 14. Número de consultas del alta y qué se considera "sin carga perezosa" — [KB] RN-14, RN-16

Conteo esperado de sentencias por alta válida (visible en la consola, porque el motor tiene `echo=True`):

| # | Sentencia |
|---|---|
| 1 | `SELECT` del catálogo por los ids pedidos |
| 2 | `INSERT` de `turno` (con `RETURNING id`) |
| 3 | `INSERT` de cada fila de `turno_practica` (`n` sentencias) |
| 4 | `SELECT` del turno con `joinedload` de la mascota |
| 5 | `SELECT` de las prácticas con `selectinload` + `joinedload` de la práctica |

Las consultas de **lectura** son siempre **3**, sin importar `n`. Si aparece un cuarto `SELECT`, es una relación cargada tarde: el síntoma esperado, en async, es `MissingGreenlet` (RN-16) y no un N+1 silencioso.

### 15. Mensajes de error: qué dicen y qué no — [KB] RN-12

Los tres 409 llevan un mensaje en español que nombra el problema concreto; ninguno devuelve el SQL, el nombre de la restricción ni datos de otras filas:

- práctica inexistente → indica que las prácticas no existen en el catálogo (nombra los ids faltantes);
- práctica repetida → indica que una práctica está repetida en el turno;
- mascota inexistente → indica que la mascota no existe.

El 422 lo arma FastAPI con el detalle de validación de Pydantic: no se reescribe.

### 16. Decisiones que se anotan para el README como propias del equipo — [DECISIÓN]

Estas no están en la consigna ni en DD-08 a DD-15 y [11] debe listarlas como decisiones del equipo, no como reglas de la cátedra:

1. orden ascendente por `practica_id` en la respuesta (Decisión 8);
2. una `fecha` sin offset se interpreta como UTC (Decisión 9);
3. los campos de más en el cuerpo se ignoran en lugar de rechazarse (Decisión 10);
4. el 409 por FK de mascota se distingue del 409 por práctica repetida **por `sqlstate`**, con mensajes distintos (Decisión 6);
5. la respuesta se obtiene releyendo el turno con carga anticipada en lugar de armarla desde memoria (Decisión 7).

## Riesgos y cómo se atacan

| Riesgo | Síntoma | Mitigación |
|---|---|---|
| Turno guardado sin sus prácticas (o al revés) | `turno` crece y `turno_practica` no | Una transacción, `flush()` + `rollback()` por camino de error; verificación con conteos antes/después de cada 409 |
| El cliente logra fijar un precio | `total` distinto del catálogo | `precio`/`total` no existen en los DTO; escenario "un total enviado por el cliente no se respeta" |
| Duplicado colapsado en silencio | 201 con una sola fila hija | Construir una fila **por práctica pedida** (Decisión 4) |
| Respuesta con carga perezosa | `MissingGreenlet` en la primera petición | Relectura con `joinedload` + `selectinload` anidado (Decisión 7) y conteo de consultas (Decisión 14) |
| 409 mentiroso por un error inesperado | 409 con mensaje genérico ante un bug | Solo se traducen excepciones de dominio y `IntegrityError` con `sqlstate` conocido |
| Secuencia consumida por una comprobación | segundo alta devuelve `id = 3` | Prohibido `nextval`; solo lectura de `last_value`/`is_called` y el `id` real del smoke (Decisión 13) |
| Fecha dependiente de la máquina | misma entrada, instantes distintos | Normalización a UTC y naive = UTC (Decisión 9) |

## Preguntas abiertas que este change toca

- **IN-02** — no hay endpoints de baja de mascotas ni de prácticas: es lo que permite afirmar que `23503` solo puede venir de la FK de la mascota (Decisión 6). Si algún día se agregara un `DELETE /practicas/{id}`, ese mapping habría que revisarlo.
- **DD-11** — se aplica tal cual: la respuesta no trae id de fila.
- **DD-12** — se respeta: `motivo` obligatorio y `fecha` sin validaciones de pasado ni de duplicados.
- **SU-02** — se materializa acá: es el primer endpoint que devuelve una `fecha`, y la devuelve en UTC.

No se abre ninguna pregunta nueva: las cinco decisiones de la Decisión 16 son de implementación y se resuelven dentro del alcance del equipo, documentadas en el README por [11].
