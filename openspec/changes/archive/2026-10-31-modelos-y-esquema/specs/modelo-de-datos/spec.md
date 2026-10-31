# Delta Spec: modelo-de-datos

## Purpose

Declara y garantiza en la base el esquema del dominio veterinario —seis tablas con sus columnas, tipos, restricciones, acciones de borrado, índices y relaciones— de modo que la corrección de las reglas RN-01 a RN-09 dependa de PostgreSQL y no de validaciones previas en el código.

## ADDED Requirements

### Requirement: Tablas y columnas obligatorias

El esquema SHALL contener seis tablas en el esquema `public` —`duenio`, `ficha_duenio`, `mascota`, `practica`, `turno` y `turno_practica`— con los nombres de tabla y de columna de `knowledge-base/04_modelo_de_datos.md`. Esos nombres MUST NOT renombrarse ni omitirse. Los importes SHALL ser `NUMERIC` y `turno.fecha` SHALL ser `timestamp with time zone`.

#### Scenario: Esquema completo generado por create_all

| Dato | Valor |
|---|---|
| **Dado** | La base `veterinaria` vacía y los cuatro `models.py` importados por `SQLModel.metadata` |
| **Cuando** | Se ejecuta `create_all` desde un script temporal no versionado |
| **Entonces** | `information_schema.tables` con `table_schema = 'public'` devuelve las seis filas `duenio`, `ficha_duenio`, `mascota`, `practica`, `turno` y `turno_practica` |
| **Y** | `information_schema.columns` devuelve, por tabla: `duenio` (`id`, `nombre`, `email`), `ficha_duenio` (`id`, `duenio_id`, `telefono`, `direccion`), `mascota` (`id`, `nombre`, `especie`, `duenio_id`), `practica` (`id`, `nombre`, `precio`), `turno` (`id`, `mascota_id`, `fecha`, `motivo`, `total`), `turno_practica` (`turno_id`, `practica_id`, `precio_unitario`) |

#### Scenario: Importes y fecha con los tipos exactos

| Dato | Valor |
|---|---|
| **Dado** | El esquema ya creado |
| **Cuando** | Se consulta `information_schema.columns` para `practica.precio`, `turno.total`, `turno_practica.precio_unitario` y `turno.fecha` |
| **Entonces** | `data_type` es `numeric` con `numeric_precision` 10 y `numeric_scale` 2 para `precio` y `precio_unitario`; 12 y 2 para `total` |
| **Y** | `turno.fecha` tiene `data_type = 'timestamp with time zone'` |
| **Y** | Ninguna columna monetaria es de tipo `double precision` ni `real` |

### Requirement: Unicidad de email, ficha y nombre de práctica

La base SHALL rechazar un `duenio.email` repetido (RN-01), una segunda `ficha_duenio` para el mismo `duenio_id` (RN-03) y un `practica.nombre` repetido (RN-02) mediante restricciones `UNIQUE`.

#### Scenario: Email de dueño repetido rechazado

| Dato | Valor |
|---|---|
| **Dado** | Un `duenio` con `email = 'ana@ejemplo.com'` |
| **Cuando** | Se intenta `INSERT INTO duenio (nombre, email) VALUES ('Otra', 'ana@ejemplo.com')` |
| **Entonces** | PostgreSQL responde **ERROR** con `SQLSTATE 23505` (violación de restricción única) |
| **Y** | La tabla `duenio` sigue teniendo una sola fila con ese email |

#### Scenario: Segunda ficha para el mismo dueño rechazada

| Dato | Valor |
|---|---|
| **Dado** | Un `duenio` con id 1 que ya tiene una fila en `ficha_duenio` |
| **Cuando** | Se intenta insertar otra `ficha_duenio` con `duenio_id = 1` |
| **Entonces** | PostgreSQL responde **ERROR** con `SQLSTATE 23505` |

#### Scenario: Nombre de práctica repetido rechazado

| Dato | Valor |
|---|---|
| **Dado** | Una `practica` con `nombre = 'Consulta'` |
| **Cuando** | Se intenta insertar otra `practica` con `nombre = 'Consulta'` |
| **Entonces** | PostgreSQL responde **ERROR** con `SQLSTATE 23505` |

### Requirement: Importes válidos según CHECK

La base SHALL rechazar `practica.precio <= 0` (RN-04) y `turno_practica.precio_unitario <= 0`, y SHALL rechazar `turno.total < 0` aceptando `turno.total = 0`, mediante restricciones `CHECK` nombradas.

#### Scenario: Práctica con precio cero rechazada

| Dato | Valor |
|---|---|
| **Dado** | El esquema ya creado |
| **Cuando** | Se ejecuta `INSERT INTO practica (nombre, precio) VALUES ('Prueba', 0)` |
| **Entonces** | PostgreSQL responde **ERROR** con `SQLSTATE 23514` (violación de `CHECK`) |
| **Y** | El mismo `INSERT` con `precio = -1` también responde **ERROR** `23514` |
| **Y** | Ninguna fila queda insertada |

#### Scenario: Total cero aceptado y total negativo rechazado

| Dato | Valor |
|---|---|
| **Dado** | Una `mascota` existente |
| **Cuando** | Se inserta un `turno` con `total = 0` |
| **Entonces** | El `INSERT` **se completa sin error** (el CHECK es `total >= 0`) |
| **Cuando** | Se intenta insertar otro `turno` con `total = -0.01` |
| **Entonces** | PostgreSQL responde **ERROR** con `SQLSTATE 23514` |

### Requirement: Una práctica no se repite en el mismo turno

`turno_practica` SHALL tener clave primaria compuesta `(turno_id, practica_id)` en ese orden, de modo que la base rechace dos filas con el mismo par (RN-07).

#### Scenario: Práctica repetida en el mismo turno rechazada

| Dato | Valor |
|---|---|
| **Dado** | Un `turno` con id 1 y una `practica` con id 1 ya asociados en `turno_practica` |
| **Cuando** | Se intenta `INSERT INTO turno_practica (turno_id, practica_id, precio_unitario) VALUES (1, 1, 15000.00)` |
| **Entonces** | PostgreSQL responde **ERROR** con `SQLSTATE 23505` |
| **Y** | `SELECT count(*) FROM turno_practica WHERE turno_id = 1 AND practica_id = 1` devuelve `1` |

### Requirement: Acción de borrado de cada clave foránea

Las claves foráneas SHALL declarar la acción de borrado de la consigna: `mascota.duenio_id` **ON DELETE RESTRICT** (RN-08) y `turno_practica.turno_id` **ON DELETE CASCADE** (RN-09). `ficha_duenio.duenio_id`, `turno.mascota_id` y `turno_practica.practica_id` MUST quedar sin `ON DELETE` explícito, es decir en el default de PostgreSQL `NO ACTION` (DD-13, IN-03).

#### Scenario: Borrar un dueño con mascotas es rechazado

| Dato | Valor |
|---|---|
| **Dado** | Un `duenio` con al menos una `mascota` a su nombre |
| **Cuando** | Se ejecuta `DELETE FROM duenio WHERE id = <ese dueño>` |
| **Entonces** | PostgreSQL responde **ERROR** con `SQLSTATE 23503` (violación de clave foránea) |
| **Y** | El dueño y su mascota siguen existiendo |

#### Scenario: Borrar un turno elimina sus turno_practica

| Dato | Valor |
|---|---|
| **Dado** | Un `turno` con dos filas en `turno_practica` |
| **Cuando** | Se ejecuta `DELETE FROM turno WHERE id = <ese turno>` |
| **Entonces** | El `DELETE` **se completa sin error** |
| **Y** | `SELECT count(*) FROM turno_practica WHERE turno_id = <ese turno>` devuelve `0` |
| **Y** | Las filas de `practica` referenciadas siguen existiendo (no se borra el catálogo) |

#### Scenario: Las FK sin regla explícita quedan en NO ACTION

| Dato | Valor |
|---|---|
| **Dado** | El esquema ya creado |
| **Cuando** | Se consulta `pg_constraint` con `contype = 'f'` para `ficha_duenio.duenio_id`, `turno.mascota_id` y `turno_practica.practica_id` |
| **Entonces** | `confdeltype = 'a'` (NO ACTION) en las tres |
| **Y** | `mascota.duenio_id` devuelve `confdeltype = 'r'` (RESTRICT) y `turno_practica.turno_id` devuelve `confdeltype = 'c'` (CASCADE) |

### Requirement: Índices de claves foráneas

El esquema SHALL tener un índice propio en `mascota.duenio_id`, `turno.mascota_id` y `turno_practica.practica_id`, y MUST NOT tener un índice propio en `turno_practica.turno_id` (la PK compuesta ya lo cubre por ser su primera columna).

#### Scenario: Índices presentes y ausente el de turno_id

| Dato | Valor |
|---|---|
| **Dado** | El esquema ya creado |
| **Cuando** | Se consulta `pg_indexes` filtrando `schemaname = 'public'` |
| **Entonces** | Existen índices que cubren `mascota (duenio_id)`, `turno (mascota_id)` y `turno_practica (practica_id)` |
| **Y** | No existe ningún índice cuyo `indexdef` sea exclusivamente sobre `turno_practica (turno_id)` |
| **Y** | El índice de la PK de `turno_practica` lista las columnas en el orden `(turno_id, practica_id)` |

### Requirement: Relaciones del ORM declaradas en ambos extremos

Cada relación SHALL declararse en los dos extremos con `back_populates`: `Duenio.ficha` ↔ `FichaDuenio.duenio`, `Duenio.mascotas` ↔ `Mascota.duenio`, `Mascota.turnos` ↔ `Turno.mascota`, `Turno.practicas` ↔ `TurnoPractica.turno` y `Practica.turnos` ↔ `TurnoPractica.practica`. `Duenio.ficha` SHALL ser a uno (`uselist=False`) y `Turno.practicas` SHALL usar `passive_deletes=True`.

#### Scenario: configure_mappers resuelve todas las relaciones

| Dato | Valor |
|---|---|
| **Dado** | Un intérprete Python con las dependencias instaladas y **sin conexión a PostgreSQL** |
| **Cuando** | Un script temporal no versionado importa los cuatro `models.py` y ejecuta `sqlalchemy.orm.configure_mappers()` |
| **Entonces** | La ejecución termina **sin error** (sin `InvalidRequestError` ni referencias sin resolver) |

#### Scenario: Duenio.ficha es una relación a uno

| Dato | Valor |
|---|---|
| **Dado** | Los mapeos configurados |
| **Cuando** | Se inspecciona `Duenio.ficha.property` |
| **Entonces** | `uselist` es `False` (devuelve un objeto o `None`, nunca una lista) |
| **Y** | `Turno.practicas.property.passive_deletes` es `True` |
