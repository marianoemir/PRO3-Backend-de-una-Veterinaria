# Diseño: modelos-y-esquema

## Contexto

Ver `proposal.md` §Why. El estado de partida que condiciona el diseño:

- `app/modules/{duenios,mascotas,practicas,turnos}/models.py` existen y están **vacíos** (stubs del change [01]).
- `app/core/database.py` solo expone `get_session`; **no** hay engine a nivel módulo y **no** existe `reiniciar.py` (llega en [09]). Por eso este change **no crea la base**: solo declara los modelos que `create_all` consumirá.
- `app/main.py` registra los seis routers pero **no importa ningún `models.py`**. Hoy nada importa los modelos: el primer import lo hará `reiniciar.py` ([09]) y el smoke de este change.
- `knowledge-base/04_modelo_de_datos.md` es normativo y fija **nombres de tabla y de columna obligatorios**: se pueden agregar columnas, no quitar ni renombrar.
- La corrección del TP revisa el esquema (30 % de la nota) y usa los nombres de la consigna.

## Objetivos / No objetivos

**Objetivos**

- Que `SQLModel.metadata.create_all` genere el esquema exacto de la KB: seis tablas, PK compuesta, UNIQUE, CHECK, FK con su acción de borrado e índices.
- Que las garantías de RN-01 a RN-09 queden **en la base**, de modo que los changes posteriores solo tengan que capturar `IntegrityError` → `rollback()` → 409 (DD-03).
- Que el mapeo ORM esté completo y consistente en los dos extremos, verificable sin base con `configure_mappers()`.

**No objetivos**

- Crear el esquema o el seed (`reiniciar.py`, change [09]); este change no ejecuta `create_all`.
- DTO, endpoints, services, códigos HTTP (changes [03]–[07]).
- Migraciones versionadas (Alembic está excluido: DD-01).
- Agregar validaciones o reglas que la consigna no enuncia (p. ej. normalizar el email, validar formato, longitudes máximas).

## Decisiones

### 1. Un archivo de modelos por módulo, con `__tablename__` explícito

Cada clase se declara en el `models.py` de su módulo, tal como fija la estructura (`FichaDuenio` en `duenios`, `TurnoPractica` en `turnos`). `__tablename__` se escribe **explícitamente** en las seis clases aunque SQLModel podría derivarlo del nombre de la clase: derivar `Duenio` → `duenio` funciona por casualidad, pero `FichaDuenio` → `ficha_duenio` y `TurnoPractica` → `turno_practica` dependen de una regla de pluralización que no queremos que decida la corrección. Explícito = verificable por lectura y por `information_schema.tables`.

**Alternativa descartada**: un único `models.py` central. Rompe la estructura modular de la consigna y concentra en un archivo lo que pertenece a cuatro módulos.

### 2. Justificación tabla por tabla: lado de la FK, tipo de relación y regla de borrado

Esta sección es el núcleo del change: cada FK tiene un lado y una acción de borrado que se derivan del **concepto de modelado**, no de la comodidad del ORM.

#### 2.1 `duenio`

Sin claves foráneas: es la raíz del grafo (nada depende de nada para existir como dueño).

| Columna | Tipo | Restricción | Origen |
|---|---|---|---|
| `id` | entero | PK autoincremental | **[DECISIÓN]** de la KB (los ids autoincrementales son decisión, no consigna) |
| `nombre` | texto | — | consigna |
| `email` | texto | **UNIQUE** | RN-01 |

`UNIQUE` en `email` y no una consulta previa: entre "¿existe este email?" y el `INSERT` hay una ventana de carrera; la única garantía atómica es la restricción de la base (DD-03).

#### 2.2 `ficha_duenio`

| FK | Va en | Por qué del lado | Regla de borrado | Por qué |
|---|---|---|---|---|
| `duenio_id → duenio.id` | `ficha_duenio` (lado "uno" con UNIQUE) | **Uno a uno de dependencia**: la ficha es un dato adicional del dueño y no existe sin él. La FK va en la tabla que depende. El `UNIQUE` sobre `duenio_id` es lo que convierte el "muchos a uno" natural de una FK en "uno a uno" (máximo una ficha por dueño, RN-03). | **Sin `ON DELETE` explícito → `NO ACTION`** | La consigna no especifica qué pasa al borrar un dueño con ficha (**IN-03**). `NO ACTION` es el default de PostgreSQL y **no inventa** una semántica: si alguien borra un dueño con ficha, la base rechaza el borrado. Agregar `CASCADE` sería decidir por la cátedra que la ficha es descartable, cosa que el enunciado no dice (DD-13). |

**Alternativa descartada**: poner la ficha como columnas de `duenio`. La consigna exige la tabla `ficha_duenio` separada y un endpoint propio (`POST /duenios/{id}/ficha`).

#### 2.3 `mascota`

| FK | Va en | Por qué del lado | Regla de borrado | Por qué |
|---|---|---|---|---|
| `duenio_id → duenio.id` | `mascota` (lado "muchos") | **Agregación**: la mascota existe por sí misma (tiene identidad y ciclo de vida propios, podría cambiar de dueño) pero pertenece a un dueño. La FK va del lado "muchos" porque un dueño tiene N mascotas y cada mascota tiene exactamente un dueño. | **`ON DELETE RESTRICT`** | **RN-08**: no se puede borrar un dueño que tenga mascotas. `RESTRICT` hace que la base rechace el `DELETE` del dueño en el mismo instante, sin consulta previa; el `service` de [03] lo traducirá a 409. Se elige `RESTRICT` y no `NO ACTION` porque la consigna **sí** enuncia la regla acá: `RESTRICT` la expresa literalmente y hace explícita la intención en el esquema. (Diferencia práctica: `NO ACTION` admite diferir la verificación al final de la transacción; `RESTRICT` no. Para este caso el efecto observable es el mismo, pero el esquema dice lo que la regla dice.) |

Índice propio en `duenio_id`: PostgreSQL **no** indexa las FK automáticamente. Sin índice, cada `DELETE` de un dueño obliga a un *sequential scan* de `mascota` para verificar `RESTRICT`, y `GET /duenios/{id}/mascotas` ([03]) también escanearía la tabla completa. La KB lo exige explícitamente.

#### 2.4 `practica`

Sin claves foráneas: es un catálogo independiente (no depende de ningún turno ni dueño).

| Columna | Tipo | Restricción | Origen |
|---|---|---|---|
| `id` | entero | PK autoincremental | KB |
| `nombre` | texto | **UNIQUE** | RN-02 |
| `precio` | `NUMERIC(10,2)` | **CHECK `precio > 0`** | RN-04, DD-06 |

`CHECK` y no validación solo en el DTO: la consigna pide el CHECK en la base (RN-04) *además* de la validación del DTO, que hará [04]. El CHECK es la última línea de defensa y la única que no se puede saltear.

#### 2.5 `turno`

| FK | Va en | Por qué del lado | Regla de borrado | Por qué |
|---|---|---|---|---|
| `mascota_id → mascota.id` | `turno` (lado "muchos") | **Asociación**: el turno *referencia* a la mascota; ninguno es parte del otro (la mascota sigue existiendo cuando el turno se atiende o se borra). La FK va del lado "muchos" porque una mascota tiene N turnos y cada turno es de una mascota. | **Sin `ON DELETE` explícito → `NO ACTION`** | La consigna no define qué pasa al borrar una mascota con turnos (**DD-13**) y **no hay endpoint `DELETE /mascotas/{id}`** (IN-02), así que el caso no es alcanzable por la API. El default rechaza el borrado, que es el comportamiento conservador y no destruye historia clínica por accidente. |

`fecha` es `DateTime(timezone=True)` → `TIMESTAMP WITH TIME ZONE`: el ejemplo de la consigna envía `-03:00` y devuelve `Z` (SU-02); sin zona horaria el dato sería ambiguo. `total` es `NUMERIC(12,2)` con `CHECK (total >= 0)`: 12 dígitos porque es una suma de precios (más rango que un precio individual) y `>= 0` porque un turno sin prácticas no puede quedar negativo; el cálculo es del `service` (RN-06, DD-07).

Índice propio en `mascota_id`: mismo razonamiento que en `mascota.duenio_id` — sin índice, el detalle de una mascota y cualquier verificación de la FK escanean `turno` completa.

#### 2.6 `turno_practica`

| FK | Va en | Por qué del lado | Regla de borrado | Por qué |
|---|---|---|---|---|
| `turno_id → turno.id` | `turno_practica` (tabla intermedia) | **Composición**: la práctica reservada es parte del turno; no existe sin él. La FK va en la tabla intermedia porque la fila **es** la relación. | **`ON DELETE CASCADE`** | **RN-09**: al borrar un turno se borran sus prácticas. `CASCADE` en la base (no en el ORM) da una única fuente de verdad: `DELETE /turnos/{id}` ([07]) emite un solo `DELETE` y PostgreSQL limpia las hijas en la misma transacción. Combinado con `passive_deletes=True` (DD-05), el ORM no emite `UPDATE turno_practica SET turno_id = NULL` ni `DELETE` fila por fila. |
| `practica_id → practica.id` | `turno_practica` (tabla intermedia) | **M:N con datos**: la relación entre turno y práctica no es un simple vínculo; lleva `precio_unitario` (el precio cobrado **en ese turno**, DD-07). Por eso no alcanza con una tabla de unión sin atributos. | **Sin `ON DELETE` explícito → `NO ACTION`** | La consigna no especifica qué pasa al borrar una práctica usada en turnos (**DD-13**), y no hay `DELETE /practicas/{id}` (IN-02). `CASCADE` acá sería catastrófico: borrar una práctica del catálogo destruiría el histórico de turnos ya cobrados. El default rechaza el borrado y protege el histórico (coherente con DD-07: el precio se congela en la relación). |

**PK compuesta `(turno_id, practica_id)`**: la clave de la fila **es** el par, no un `id` subrogado. Esto cumple RN-07 (una práctica no se repite en un turno) con una restricción de la base, sin `SELECT` previo, y evita una columna `id` que la KB no define (DD-11: el detalle de turno no expone id de fila). El orden `(turno_id, practica_id)` no es arbitrario: se elige `turno_id` primero porque la consulta dominante es "las prácticas de un turno".

`precio_unitario` con `NUMERIC(10,2)` y `CHECK (> 0)`: es una copia del precio del catálogo al reservar (RN-06, DD-07), así que comparte escala y regla con `practica.precio`. Que un turno tenga `total = 0` con prácticas cargadas es imposible por el CHECK `> 0` de cada línea; `total = 0` solo es alcanzable si se permite un turno sin líneas, y el CHECK `>= 0` lo acepta.

### 3. Por qué `turno_practica.turno_id` no lleva índice propio y `practica_id` sí

Es la única FK del esquema sin índice dedicado, y es deliberado:

- La PK compuesta `(turno_id, practica_id)` crea un índice B-tree con **`turno_id` como primera columna**. PostgreSQL puede usar ese índice para cualquier búsqueda por `turno_id` (las prácticas de un turno, y también el borrado en cascada cuando elimina las hijas). Un índice extra sobre `turno_id` sería un índice redundante: mismo prefijo, mismo orden, costo de escritura y espacio duplicados.
- `practica_id` es la **segunda** columna de esa PK. Un índice B-tree solo sirve para prefijos: buscar por `practica_id` sin `turno_id` no puede aprovechar el índice de la PK (no puede "saltar" la primera columna). Por eso `practica_id` **sí** necesita un índice propio — lo usa, por ejemplo, el chequeo de la FK al borrar o actualizar una práctica.
- Verificación: en `pg_indexes` deben existir índices que cubran `mascota (duenio_id)`, `turno (mascota_id)` y `turno_practica (practica_id)`, y **no** debe existir uno exclusivo sobre `turno_practica (turno_id)`.

> La explicación en 1–2 líneas es entregable obligatorio del `README.md` ([11]); este change la deja escrita acá para que [11] la copie.

### 4. Tipos: `Decimal` en Python, `NUMERIC` en la base (DD-06)

`precio` y `precio_unitario` → `NUMERIC(10,2)`; `total` → `NUMERIC(12,2)`. En Python se anotan como `Decimal` y se mapean con `Column(Numeric(10, 2))`, **nunca** `float`: `float` es binario y no representa exactamente `0.10`, con lo que las sumas de `total` derivarían. Los DTO ([04], [06]) serializarán el `Decimal` como string (`"27000.00"`), pero eso se decide en esos changes; acá solo se fija el tipo de columna y el de la anotación.

`turno.fecha`: `datetime` con `DateTime(timezone=True)` → `TIMESTAMP WITH TIME ZONE`. Se descarta `TIMESTAMP` sin zona: el ejemplo de la consigna cruza `-03:00` con `Z` (SU-02) y sin zona el instante se vuelve ambiguo.

Las tres columnas monetarias se declaran **`NOT NULL`**. Es necesario, no cosmético: un `CHECK` sobre `NULL` evalúa a *unknown* y PostgreSQL **acepta** la fila, así que un `precio` nulo esquivaría RN-04 y un `total` nulo esquivaría `total >= 0`. La KB no menciona `NULL` en ninguna columna; se toma el default de SQLModel (campo no `Optional` → `NOT NULL`) y se explicita en los importes para que el CHECK sea efectivo.

### 5. Relaciones: ambos extremos, `uselist=False`, `passive_deletes=True`

| Extremo A | Extremo B | Cardinalidad | Detalle |
|---|---|---|---|
| `Duenio.ficha` | `FichaDuenio.duenio` | 1 a 0..1 | `uselist=False` en el lado del dueño: devuelve **un objeto o `None`**, nunca una lista. Sin esto, SQLAlchemy lo trataría como colección y `GET /duenios/{id}` ([03]) devolvería `[]` en lugar de `null`/objeto. |
| `Duenio.mascotas` | `Mascota.duenio` | 1 a N | `list["Mascota"]` |
| `Mascota.turnos` | `Turno.mascota` | 1 a N | `list["Turno"]` |
| `Turno.practicas` | `TurnoPractica.turno` | 1 a N | `list["TurnoPractica"]` con **`passive_deletes=True`** |
| `Practica.turnos` | `TurnoPractica.practica` | 1 a N | `list["TurnoPractica"]` |

- `back_populates` en **los dos extremos** (no `backref`): el mapeo queda explícito en ambos archivos, y un error de nombre se detecta en `configure_mappers()` en lugar de aparecer como un atributo dinámico en tiempo de ejecución.
- **Ninguna relación declara `lazy=`**: se deja el default de SQLAlchemy y las lecturas resuelven la carga explícitamente con `joinedload`/`selectinload` (RN-14, RN-16, DD-04). Declarar `lazy="joined"` en el modelo acoplaría el esquema a una estrategia de lectura y haría que cualquier `SELECT` arrastre joins no pedidos.
- `passive_deletes=True` solo en `Turno.practicas`, que es la relación cuyo `ON DELETE CASCADE` existe en la base (DD-05). No se pone `cascade="all, delete-orphan"`: el ORM no debe borrar ni "vaciar" las filas hijas; la base ya lo hace. Ponerlo en las demás relaciones sería mentir sobre lo que la base garantiza.
- `Turno.practicas` **no** usa `secondary=`: `turno_practica` es una entidad con atributos (`precio_unitario`), no una tabla de unión pura. Se modela como association object.

**Desvíos de sintaxis forzados por SQLModel 0.0.48** (no afectan el esquema ni los criterios de aceptación):

| Lo que pedía el plan | Lo que se escribió | Por qué |
|---|---|---|
| `Relationship(back_populates="duenio", uselist=False)` | `Relationship(back_populates="duenio", sa_relationship_kwargs={"uselist": False})` | En 0.0.48 `uselist` **no** es un kwarg de `Relationship()`: lanza `TypeError: Relationship() got an unexpected keyword argument 'uselist'`. Con `sa_relationship_kwargs` el efecto es idéntico y verificable: `Duenio.ficha.property.uselist is False`. |
| `ficha: "FichaDuenio" \| None` | `ficha: Optional["FichaDuenio"]` | La forma con `\|` en la anotación rompe el mapeo: `InvalidRequestError: expression 'B \| None' failed to locate a name`. `Optional[...]` sobre un forward reference en string cumple lo que exige §6 y mapea a uno. |

### 6. Imports entre módulos sin ciclos

`Duenio.mascotas` necesita el nombre `Mascota`, que vive en otro módulo. Para no crear imports circulares (`duenios.models` ↔ `mascotas.models`), se usa el patrón:

```python
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.mascotas.models import Mascota
```

y la anotación **en forma de string** dentro de la colección: `mascotas: list["Mascota"] = Relationship(back_populates="duenio")`. En ejecución el nombre no se importa; SQLModel lo resuelve contra el registro de clases de `SQLModel.metadata` cuando se configuran los mapeos.

Consecuencias que hay que respetar en los changes siguientes:

- **No** usar `from __future__ import annotations` en estos archivos: convierte todas las anotaciones en strings y complica la resolución de las relaciones en SQLModel. La forma `list["Mascota"]` ya es un forward reference válida.
- Importar **un solo** `models.py` no alcanza para mapear: `configure_mappers()` falla con `expression 'Mascota' failed to locate a name` si la clase no fue importada. Por eso `reiniciar.py` ([09]) y el script de smoke **deben importar los cuatro módulos** antes de `create_all` / `configure_mappers()`. Si no, `create_all` crearía un subconjunto de tablas (las de las clases importadas) y el esquema quedaría incompleto.
- Las dependencias reales entre modelos son: `mascotas` → `duenios`, `turnos` → `mascotas` + `practicas`. `duenios` no importa a nadie en ejecución; los `TYPE_CHECKING` no generan ciclos.

### 7. Restricciones nombradas: solo los `CHECK`

Solo los `CHECK` se declaran con nombre explícito: `ck_<tabla>_<columna>_<condición abreviada>` (por ejemplo `ck_practica_precio_positivo`). Las PK, los `UNIQUE` y las FK quedan con el **nombre por defecto de PostgreSQL**, que se deriva de la tabla y sus columnas (`duenio_pkey`, `duenio_email_key`, `mascota_duenio_id_fkey`).

Motivos:

1. **El `CHECK` es la restricción que el `service` necesita distinguir**: `asyncpg` expone el nombre de la restricción en la excepción (`constraint_name`) y SQLAlchemy lo arrastra en el `IntegrityError`. Con `ck_practica_precio_positivo` / `ck_turno_total_no_negativo` / `ck_turno_practica_precio_unitario_positivo`, [04] y [06] pueden reconocer una violación de precio sin parsear el texto del motor.
2. **Verificación legible en pgAdmin**: `pg_get_constraintdef(oid)` y `conname` muestran exactamente qué condición se creó, sin tener que leer la expresión.
3. **PK, UNIQUE y FK no se nombran porque no aportan**: se declaran con `Field(primary_key=True)`, `Field(unique=True)` y `Field(foreign_key=...)`, que es la forma idiomática de SQLModel; nombrarlas obligaría a `sa_column` o `__table_args__` extra en cada columna. El nombre derivado por PostgreSQL es predecible, y la verificación de `tasks.md` no depende de él: compara `contype` y `pg_get_constraintdef(oid)`, no `conname`.

### 8. Verificación sin `psql` (pgAdmin) y sin base para el mapeo

El entorno del equipo es Windows con **pgAdmin**, no `psql`. La verificación se parte en dos, y ambas usan archivos `scratch_*` **no versionados**:

1. **Mapeo ORM, sin PostgreSQL**: un snippet Python temporal importa los cuatro `models.py` y llama a `sqlalchemy.orm.configure_mappers()`. Valida `back_populates`, `uselist=False`, la PK compuesta y las FK declaradas sin necesitar servidor. Es el chequeo más barato y el que atrapa los errores de tipeo en nombres de relación.
2. **Esquema y comportamiento, en pgAdmin**: un `scratch_verificacion.sql` que se abre en Query Tool y se ejecuta **después** de que un `create_all` temporal haya creado las tablas (este change no crea `reiniciar.py`). El script inspecciona el **catálogo del sistema**, no metacomandos:
   - tablas → `information_schema.tables` con `table_schema = 'public'`;
   - columnas y tipos → `information_schema.columns`;
   - PK, UNIQUE, CHECK y FK con su acción de borrado → `pg_constraint` (`contype` `'p'`/`'u'`/`'c'`/`'f'`, `confdeltype` `'a'` = NO ACTION, `'r'` = RESTRICT, `'c'` = CASCADE) + `pg_get_constraintdef(oid)`;
   - índices → `pg_indexes` (incluido el orden de columnas de la PK compuesta);
   - casos de aceptación/rechazo → `INSERT`/`DELETE` dentro de `BEGIN … ROLLBACK` para no ensuciar la base.

Se descarta `\d` porque es un metacomando de `psql` y no existe en pgAdmin. El script es **idempotente/repetible** por el `ROLLBACK`.

**TDD**: este change no tiene lógica ejecutable —solo declaraciones de esquema—, así que no hay ciclo RED/GREEN de tests unitarios. La verificación es el smoke de mapeo + SQL; queda escrito también en `tasks.md`.

## Decisiones propias registradas

> La consigna no define estos puntos. Son decisiones del equipo, no reglas de la cátedra: van al `design.md` y se mencionan en el `README.md` (ver `knowledge-base/09_decisiones_y_supuestos.md` §Decisiones del equipo).

| Punto abierto | Resolución en este change | Referencia |
|---|---|---|
| **IN-03** — regla de borrado de `ficha_duenio.duenio_id` no especificada | Se deja el default de PostgreSQL (`NO ACTION`). **No** se agrega `CASCADE`. Si se borra un dueño con ficha, la base rechaza el borrado (mismo 409 de RN-08, por otra restricción). | **DD-13** |
| `turno.mascota_id` y `turno_practica.practica_id` sin `ON DELETE` en la consigna | Mismo criterio: `NO ACTION` por default. No son alcanzables por la API (no hay `DELETE` de mascotas ni de prácticas, IN-02) y `CASCADE` destruiría histórico. | **DD-13**, IN-02 |
| Borrado en cascada: ¿ORM o base? | Base (`ON DELETE CASCADE` + `passive_deletes=True`). | **DD-05**, RN-09 |
| Tipo de los importes | `NUMERIC` / `Decimal`, nunca `float`; JSON como string (eso último en [04] y [06]). | **DD-06** |
| Precio congelado en la relación | Columna `precio_unitario` en `turno_practica`; `total` en `turno`. | **DD-07**, RN-06 |
| Ids autoincrementales | `Integer` PK con autoincremento (`SERIAL`/`IDENTITY` en PostgreSQL). | **[DECISIÓN]** de `04_modelo_de_datos.md` |

## Riesgos / Trade-offs

| Riesgo | Mitigación |
|---|---|
| `create_all` ejecutado sin importar los cuatro `models.py` crea un subconjunto de tablas y el esquema queda incompleto. | Nota explícita en §6 y tarea de smoke: importar los cuatro módulos antes de `create_all`/`configure_mappers()`. [09] debe hacer lo mismo en `reiniciar.py`. |
| El orden de las columnas de la PK compuesta se invierte (`(practica_id, turno_id)`) y se pierde la justificación del índice. | Se declara `turno_id` primero en la clase y se verifica el orden con `pg_indexes`; queda como criterio de aceptación en `tasks.md`. |
| Agregar un índice "por las dudas" en `turno_practica.turno_id` (redundante) o en otra columna. | La KB fija exactamente tres índices de FK; la verificación exige que **no** exista uno propio sobre `turno_id`. |
| `passive_deletes=True` deja objetos hijos en la sesión apuntando a filas ya borradas por la base. | El service de [07] debe tratar el turno como borrado tras el `commit` y no reutilizar la colección cargada (trade-off aceptado en DD-05). |
| `NO ACTION` en `ficha_duenio.duenio_id` hace que `DELETE /duenios/{id}` de un dueño **con ficha y sin mascotas** falle con 409 aunque la regla RN-08 hable de mascotas. | Es el comportamiento decidido en DD-13/IN-03 y se documentará en el README. No se agrega `CASCADE` sin autorización de la cátedra. |
| `Decimal` en el modelo y `float` colado en un cálculo futuro de `total` produciría un error de tipo en el `INSERT`. | El tipo `Decimal` en la anotación y `Numeric` en la columna hacen que el error salte en desarrollo, no en producción. |

## Plan de migración / rollback

No hay migraciones (DD-01). El esquema se materializa con `create_all` y se descarta con `drop_all` desde `reiniciar.py` ([09]).

- **Aplicación**: completar los cuatro `models.py`; verificar mapeo con `configure_mappers()`; crear el esquema con un `create_all` temporal; ejecutar `scratch_verificacion.sql` en pgAdmin; borrar los `scratch_*`.
- **Rollback**: vaciar los cuatro `models.py` a su estado de stub y ejecutar `drop_all` (o borrar la base y recrearla). Al no haber consumidores previos del modelo, no hay datos que preservar ni contrato que romper.
- **Orden respecto del roadmap**: [03], [04] y [09] dependen de este change; [09] es quien deja el esquema creado de forma reproducible. Hasta que [09] exista, el esquema solo se crea desde el script temporal.

## Preguntas abiertas

Ninguna que afecte este change. Las dos ambigüedades reales (regla de borrado de `ficha_duenio.duenio_id` y de `turno_practica.practica_id`) están resueltas por DD-13/IN-03 y registradas arriba. Queda pendiente para la cátedra, no para el código, la confirmación de esas dos reglas; si la cátedra pidiera `CASCADE`, el cambio se limita a la declaración de la FK.
