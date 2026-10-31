# 04_modelo_de_datos.md

> **Fuente normativa**: consigna, § "Modelo de dominio". Los **nombres de tablas y columnas son obligatorios** (la corrección los usa): se pueden agregar columnas, **no quitar ni renombrar** las indicadas.
> Lo marcado **[DECISIÓN]** no está en la consigna: es una decisión de implementación y debe justificarse en el `design.md` del change.

## ERD

```
duenio (1) ────── (0..1) ficha_duenio          uno a uno (FK + UNIQUE)
duenio (1) ────< (N) mascota                   agregación (FK, ON DELETE RESTRICT)
mascota (1) ───< (N) turno                     asociación (FK)
turno (1) ─────< (N) turno_practica            composición (FK, ON DELETE CASCADE)
practica (1) ──< (N) turno_practica            M:N con datos (precio_unitario)
```

`turno_practica` es la tabla intermedia entre `turno` y `practica`: guarda el **precio cobrado en ese turno** (el precio es de la relación, no de la práctica).

## Tablas

### `duenio`
Módulo: `duenios`. Clase: `Duenio`.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | entero, PK autoincremental **[DECISIÓN]** | PK |
| `nombre` | texto | |
| `email` | texto | **UNIQUE** (RN-01) |

### `ficha_duenio`
Módulo: `duenios`. Clase: `FichaDuenio`.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | entero, PK autoincremental | PK |
| `duenio_id` | entero | FK → `duenio.id`; **UNIQUE** (RN-03) |
| `telefono` | texto | |
| `direccion` | texto | |

- `Duenio.ficha` devuelve **un objeto** (o `None`), **no una lista** (`uselist=False`).
- Regla de borrado de la FK: **no especificada** → se deja el default de PostgreSQL (`NO ACTION`). Ver IN-03 en `10_preguntas_abiertas.md`. **No** agregar `CASCADE` sin autorización.

### `mascota`
Módulo: `mascotas`. Clase: `Mascota`.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | entero, PK autoincremental | PK |
| `nombre` | texto | |
| `especie` | texto | libre (ver pregunta abierta) |
| `duenio_id` | entero | FK → `duenio.id` **ON DELETE RESTRICT** (RN-08); **índice** en `duenio_id` |

### `practica`
Módulo: `practicas`. Clase: `Practica`.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | entero, PK autoincremental | PK |
| `nombre` | texto | **UNIQUE** (RN-02) |
| `precio` | `NUMERIC(10,2)` | **CHECK `precio > 0`** (RN-04) |

### `turno`
Módulo: `turnos`. Clase: `Turno`.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | entero, PK autoincremental | PK |
| `mascota_id` | entero | FK → `mascota.id`; **índice** en `mascota_id` |
| `fecha` | `TIMESTAMP WITH TIME ZONE` | `DateTime(timezone=True)` |
| `motivo` | texto | |
| `total` | `NUMERIC(12,2)` | **CHECK `total >= 0`**; lo calcula el servidor (RN-06) |

### `turno_practica`
Módulo: `turnos`. Clase: `TurnoPractica`.

| Columna | Tipo | Restricciones |
|---|---|---|
| `turno_id` | entero | FK → `turno.id` **ON DELETE CASCADE** (RN-09); parte de la **PK** |
| `practica_id` | entero | FK → `practica.id`; parte de la **PK**; **índice** en `practica_id` |
| `precio_unitario` | `NUMERIC(10,2)` | **CHECK `precio_unitario > 0`**; copia del precio del catálogo al reservar (RN-06) |

- **PK compuesta `(turno_id, practica_id)`**: garantiza que una práctica no aparezca dos veces en un turno (RN-07).
- Regla de borrado de `practica_id`: **no especificada** → default de PostgreSQL. Ver pregunta abierta en `10_preguntas_abiertas.md`.

## Justificación del lado de cada clave foránea

| Relación | Tipo | FK en | Por qué |
|---|---|---|---|
| Dueño ↔ ficha | Uno a uno | `ficha_duenio.duenio_id` + **UNIQUE** | La ficha no existe sin dueño: depende de él. El UNIQUE convierte el "muchos a uno" en "uno a uno" (máximo una ficha por dueño). |
| Dueño ↔ mascota | Agregación | `mascota.duenio_id` (N) | La mascota existe por sí misma y puede cambiar de dueño; la FK va del lado "muchos". `RESTRICT` impide borrar un dueño con mascotas. |
| Mascota ↔ turno | Asociación | `turno.mascota_id` (N) | El turno conoce a la mascota; ninguno es parte del otro. La FK va del lado "muchos" (turno). |
| Turno ↔ sus prácticas | Composición | `turno_practica.turno_id` | Una práctica reservada no existe sin su turno: nace y se borra con él → `CASCADE`. |
| Turno ↔ práctica | M:N con datos | tabla intermedia `turno_practica` | El precio cobrado es de la relación, no de la práctica. Las dos FK forman la PK compuesta. |

## Relaciones en el ORM (`Relationship`)

Cada relación se declara en **los dos extremos** con `back_populates`:

| Extremo A | Extremo B |
|---|---|
| `Duenio.ficha` (uno) | `FichaDuenio.duenio` |
| `Duenio.mascotas` (lista) | `Mascota.duenio` |
| `Mascota.turnos` (lista) | `Turno.mascota` |
| `Turno.practicas` (lista de `TurnoPractica`) | `TurnoPractica.turno` |
| `Practica.turnos` (lista de `TurnoPractica`) | `TurnoPractica.practica` |

- `Turno.practicas` se declara con **`passive_deletes=True`**: el borrado del turno lo decide la base (`ON DELETE CASCADE`), el ORM no intenta vaciar ni borrar esas filas.
- Ninguna relación se lee con carga perezosa: toda lectura declara `joinedload` (relaciones "a uno") o `selectinload` (colecciones) en la misma consulta (RN-14, RN-16).

## Reglas transversales del modelo

- El dinero es **`Decimal`**, nunca `float`; en JSON se serializa como string (`"27000.00"`).
- Los DTO de alta **no llevan `id`**; los modelos de tabla no se exponen directamente.
- PostgreSQL **no crea** el índice de una FK por su cuenta: por eso la consigna pide índice en `mascota.duenio_id`, `turno.mascota_id` y `turno_practica.practica_id`.
- El esquema se crea con `SQLModel.metadata.create_all` (y se borra con `drop_all`) desde `reiniciar.py`. **Sin Alembic.**

## Por qué `turno_practica.turno_id` no necesita índice propio

Es la única FK sin índice propio. La clave primaria compuesta `(turno_id, practica_id)` ya tiene un índice B-tree con **`turno_id` como primera columna**, así que PostgreSQL lo usa para buscar por `turno_id` (por ejemplo, las prácticas de un turno o el borrado en cascada). En cambio `practica_id` es la **segunda** columna de la PK: buscar por ella solo no aprovecha ese índice, por eso sí lleva uno propio.

> Esta explicación (en 1 o 2 líneas) es entregable obligatorio del `README.md`.

## Seed data inicial (`reiniciar.py`)

Mínimo exigido: **2 dueños (uno con ficha), 3 mascotas, 4 prácticas, 1 turno con 2 prácticas** (con `precio_unitario` copiado y `total` calculado).

El ejemplo de la consigna (alta de turno) devuelve `"id": 2` y usa la mascota `1` ("Toby", perro), la práctica `1` ("Consulta", `15000.00`) y la práctica `3` ("Vacuna antirrábica", `12000.00`). Para que ese ejemplo funcione tal cual, el seed debería respetar esos ids:

| Tabla | Datos sugeridos **[DECISIÓN]** |
|---|---|
| `duenio` | 1: nombre y email a elección, **con ficha**; 2: sin ficha |
| `mascota` | 1: Toby (perro), del dueño 1; dos mascotas más (una del dueño 1 o 2) |
| `practica` | 1: Consulta `15000.00`; 2: Desparasitación (precio a elección); 3: Vacuna antirrábica `12000.00`; 4: una práctica más |
| `turno` | 1: de una mascota existente, con 2 prácticas (el siguiente alta recibe `id = 2`) |

Datos ficticios: nada real.
