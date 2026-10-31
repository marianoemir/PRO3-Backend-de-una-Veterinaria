# Tareas: modelos-y-esquema

> Dueño: **Mariano**. Duración estimada total: **8–10 h**. Dependencias: `01` `fundacion-proyecto` (archivado).
> Alcance: **solo los cuatro `models.py`**. Sin DTO, sin endpoints, sin `reiniciar.py`, sin `.gitignore`.

## Notas previas (leer antes de empezar)

- **Sin `psql` y sin `\d`**: el equipo trabaja en Windows con **pgAdmin**. Toda inspección del esquema se hace con consultas al **catálogo del sistema** (`information_schema`, `pg_constraint`, `pg_indexes`) ejecutadas en **Query Tool**.
- **Este change no crea la base.** `create_all` vive en `reiniciar.py` ([09], DD-01), que todavía no existe. Por eso la verificación usa un script temporal `scratch_crear_esquema.py` que hace `drop_all` + `create_all`, y después el `scratch_verificacion.sql` **asume que las tablas ya existen**.
- **`scratch_*` no se versiona**: `scratch_crear_esquema.py`, `scratch_mapeo.py` y `scratch_verificacion.sql` son temporales, no se agregan al repo y se borran del disco al final (tarea 6.1).
- **TDD**: este change **no tiene lógica ejecutable** (solo declaraciones de esquema), así que no hay ciclo RED/GREEN de tests unitarios. La verificación es (a) el smoke de mapeo con `configure_mappers()` sin base y (b) las consultas y los casos de aceptación/rechazo por SQL en pgAdmin.
- **Importar los cuatro módulos** antes de `create_all` / `configure_mappers()`: si falta uno, las clases no se registran en `SQLModel.metadata` y el esquema queda incompleto (ver `design.md` §6).

## 1. Preparación

- [x] **1.1 — Crear `scratch_crear_esquema.py` (temporal, no versionado)** *(30 min)*
  - Script que importa **los cuatro** `models.py`, borra y crea el esquema:
    ```python
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlmodel import SQLModel
    from app.core.config import settings
    # Importar los CUATRO módulos: sin esto las clases no se registran en el metadata.
    from app.modules.duenios.models import Duenio, FichaDuenio      # noqa: F401
    from app.modules.mascotas.models import Mascota                 # noqa: F401
    from app.modules.practicas.models import Practica               # noqa: F401
    from app.modules.turnos.models import Turno, TurnoPractica      # noqa: F401

    async def main() -> None:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)
        await engine.dispose()
        print("esquema recreado:", sorted(SQLModel.metadata.tables))

    asyncio.run(main())
    ```
  - **Verificación**: `python scratch_crear_esquema.py` termina sin error e imprime `['duenio', 'ficha_duenio', 'mascota', 'practica', 'turno', 'turno_practica']`. En pgAdmin, `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY 1;` devuelve las **6** filas.
  - **Nota**: si `DATABASE_URL` no está en `.env`, el script falla con el mensaje FATAL de `config.py` — es el comportamiento esperado.

- [x] **1.2 — Crear `scratch_verificacion.sql` con las consultas de catálogo (temporal, no versionado)** *(45 min)*
  - Cabecera del archivo:
    ```sql
    -- scratch_verificacion.sql — NO versionado: se borra del disco al final (tarea 6.1)
    -- Ejecutar en pgAdmin > Query Tool, DESPUÉS de scratch_crear_esquema.py.
    -- Bloque A: inspección del esquema (solo SELECT, seguro de repetir).
    -- Bloque B: casos de aceptación/rechazo (envueltos en BEGIN ... ROLLBACK).
    ```
  - **Bloque A.1 — tablas existentes**:
    ```sql
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name IN ('duenio','ficha_duenio','mascota','practica','turno','turno_practica')
    ORDER BY table_name;
    ```
    Esperado: 6 filas.
  - **Bloque A.2 — columnas y tipos**:
    ```sql
    SELECT table_name, column_name, data_type, numeric_precision, numeric_scale, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name IN ('duenio','ficha_duenio','mascota','practica','turno','turno_practica')
    ORDER BY table_name, ordinal_position;
    ```
    Esperado: 3 + 4 + 4 + 3 + 5 + 3 = **22 filas**, con los nombres de `knowledge-base/04_modelo_de_datos.md`.
  - **Verificación**: el archivo existe, corre en Query Tool sin error y el Bloque A.1 devuelve 6 filas.

## 2. Modelos del dominio

> Cada tarea se verifica corriendo `python scratch_crear_esquema.py` y después la consulta indicada en pgAdmin.

- [x] **2.1 — `app/modules/duenios/models.py`: `Duenio` y `FichaDuenio`** *(1 h)*
  - `Duenio`: `__tablename__ = "duenio"`; `id: int | None = Field(default=None, primary_key=True)`; `nombre: str`; `email: str = Field(unique=True)`; relación `ficha: Optional["FichaDuenio"] = Relationship(back_populates="duenio", sa_relationship_kwargs={"uselist": False})`.
  - `FichaDuenio`: `__tablename__ = "ficha_duenio"`; `id` PK; `duenio_id: int = Field(foreign_key="duenio.id", unique=True)` (**sin** `ondelete`: default `NO ACTION`, DD-13); `telefono: str`; `direccion: str`; relación `duenio: "Duenio" = Relationship(back_populates="ficha")`.
  - Imports con `TYPE_CHECKING` (sin `from __future__ import annotations`), anotaciones en string (ver `design.md` §6).
  - **Desvíos de sintaxis forzados por SQLModel 0.0.48** (no cambian el esquema, la spec ni los criterios de aceptación):
    - `uselist=False` **no** es un kwarg de `Relationship()` en esta versión: `TypeError: Relationship() got an unexpected keyword argument 'uselist'`. Se pasa con `sa_relationship_kwargs={"uselist": False}`, que produce el mismo efecto (`Duenio.ficha.property.uselist is False`, verificado en 3.1).
    - La anotación es `Optional["FichaDuenio"]` (importando `Optional` de `typing`) y **no** `"FichaDuenio" | None`: la forma con `|` rompe el mapeo con `InvalidRequestError: expression 'B | None' failed to locate a name`. Sigue siendo forward reference en string, como exige `design.md` §6.
  - **Verificación**:
    ```sql
    SELECT c.conname, c.contype, pg_get_constraintdef(c.oid) AS definicion
    FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'public' AND t.relname IN ('duenio','ficha_duenio')
    ORDER BY t.relname, c.contype;
    ```
    Esperado: PK en `duenio.id`; `UNIQUE` en `duenio.email`; PK en `ficha_duenio.id`; **UNIQUE** en `ficha_duenio.duenio_id`; FK `ficha_duenio.duenio_id → duenio.id` con `confdeltype = 'a'` (NO ACTION).

- [x] **2.2 — `app/modules/mascotas/models.py`: `Mascota`** *(45 min)*
  - `__tablename__ = "mascota"`; `id` PK; `nombre: str`; `especie: str`; `duenio_id: int = Field(foreign_key="duenio.id", ondelete="RESTRICT", index=True)`; relación `duenio: "Duenio" = Relationship(back_populates="mascotas")`.
  - **Verificación**:
    ```sql
    SELECT c.conname, c.contype, c.confdeltype, pg_get_constraintdef(c.oid) AS definicion
    FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'public' AND t.relname = 'mascota';
    ```
    Esperado: PK en `id`; FK `mascota.duenio_id → duenio.id` con **`confdeltype = 'r'` (RESTRICT)**. Y en `pg_indexes`: existe un índice cuyo `indexdef` es `... ON public.mascota USING btree (duenio_id)`.

- [x] **2.3 — `app/modules/practicas/models.py`: `Practica`** *(30 min)*
  - `__tablename__ = "practica"`; `id` PK; `nombre: str = Field(unique=True)`; `precio: Decimal` mapeado a `NUMERIC(10,2)` con `CHECK (precio > 0)` vía `__table_args__ = (CheckConstraint("precio > 0", name="ck_practica_precio_positivo"),)` y `sa_column=Column(Numeric(10, 2), nullable=False)`; relación `turnos: list["TurnoPractica"] = Relationship(back_populates="practica")`.
  - **Verificación**:
    ```sql
    SELECT column_name, data_type, numeric_precision, numeric_scale
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'practica' AND column_name = 'precio';
    ```
    Esperado: `numeric`, precisión **10**, escala **2**. Y en `pg_constraint`: `UNIQUE` sobre `nombre` y `CHECK` cuyo `pg_get_constraintdef` contiene `CHECK ((precio > (0)::numeric))`.

- [x] **2.4 — `app/modules/turnos/models.py`: `Turno`** *(1 h)*
  - `__tablename__ = "turno"`; `id` PK; `mascota_id: int = Field(foreign_key="mascota.id", index=True)` (**sin** `ondelete`: default `NO ACTION`, DD-13); `fecha: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))`; `motivo: str`; `total: Decimal` → `NUMERIC(12,2)` con `CHECK (total >= 0)`; relaciones `mascota: "Mascota" = Relationship(back_populates="turnos")` y `practicas: list["TurnoPractica"] = Relationship(back_populates="turno", passive_deletes=True)`.
  - **Verificación**:
    ```sql
    SELECT column_name, data_type, numeric_precision, numeric_scale
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'turno'
    ORDER BY ordinal_position;
    ```
    Esperado: `fecha` con `data_type = 'timestamp with time zone'`; `total` `numeric` 12/2. En `pg_constraint`: FK `turno.mascota_id` con `confdeltype = 'a'` y `CHECK ((total >= (0)::numeric))`. En `pg_indexes`: índice btree sobre `turno (mascota_id)`.

- [x] **2.5 — `app/modules/turnos/models.py`: `TurnoPractica` con PK compuesta** *(1.5 h)*
  - `__tablename__ = "turno_practica"`; **`turno_id` primero**: `turno_id: int = Field(primary_key=True, foreign_key="turno.id", ondelete="CASCADE")`; `practica_id: int = Field(primary_key=True, foreign_key="practica.id", index=True)` (**sin** `ondelete`); `precio_unitario: Decimal` → `NUMERIC(10,2)` con `CHECK (precio_unitario > 0)`; relaciones `turno: "Turno" = Relationship(back_populates="practicas")` y `practica: "Practica" = Relationship(back_populates="turnos")`.
  - **Sin** columna `id`, **sin** índice propio en `turno_id` (la PK compuesta lo cubre).
  - **Verificación**:
    ```sql
    SELECT indexname, indexdef FROM pg_indexes
    WHERE schemaname = 'public' AND tablename = 'turno_practica' ORDER BY indexname;
    ```
    Esperado: (a) el índice de la PK lista **`(turno_id, practica_id)` en ese orden**; (b) existe un índice sobre `(practica_id)`; (c) **no** existe un índice cuyo `indexdef` termine en `(turno_id)`. Y en `pg_constraint`: PK compuesta de dos columnas, FK `turno_id → turno.id` con **`confdeltype = 'c'` (CASCADE)**, FK `practica_id → practica.id` con `confdeltype = 'a'`, `CHECK ((precio_unitario > (0)::numeric))`.

## 3. Mapeo ORM sin base de datos

- [x] **3.1 — Verificar el mapeo con `configure_mappers()` (sin PostgreSQL)** *(45 min)*
  - Crear `scratch_mapeo.py` (temporal, no versionado):
    ```python
    from sqlalchemy.orm import configure_mappers
    # Importar los CUATRO módulos antes de configurar los mapeos.
    from app.modules.duenios.models import Duenio, FichaDuenio      # noqa: F401
    from app.modules.mascotas.models import Mascota                 # noqa: F401
    from app.modules.practicas.models import Practica               # noqa: F401
    from app.modules.turnos.models import Turno, TurnoPractica      # noqa: F401

    configure_mappers()
    assert Duenio.ficha.property.uselist is False, "Duenio.ficha debe ser a uno"
    assert Turno.practicas.property.passive_deletes is True, "passive_deletes en Turno.practicas"
    for clase in (Duenio, FichaDuenio, Mascota, Practica, Turno, TurnoPractica):
        print(clase.__tablename__, sorted(c.name for c in clase.__table__.columns))
    print("mapeo OK")
    ```
  - **Verificación**: `python scratch_mapeo.py` imprime las 6 tablas con sus columnas y termina en `mapeo OK`, **sin** `InvalidRequestError` y **sin** conectarse a la base. Un `expression 'X' failed to locate a name` significa que falta importar un módulo o hay un `back_populates` mal escrito.

## 4. Verificación del esquema completo en pgAdmin (integración)

- [x] **4.1 — Tablas, columnas y tipos exactos** *(30 min)*
  - Ejecutar los bloques **A.1** y **A.2** de `scratch_verificacion.sql`.
  - **Verificación**: A.1 devuelve 6 tablas; A.2 devuelve 22 columnas con estos tipos: `precio` numeric(10,2), `total` numeric(12,2), `precio_unitario` numeric(10,2), `fecha` timestamp with time zone. **Ninguna** columna monetaria es `double precision` ni `real`. `turno_practica` **no** tiene columna `id`.

- [x] **4.2 — PK, UNIQUE, CHECK y FK con su acción de borrado** *(45 min)*
  - Ejecutar en Query Tool:
    ```sql
    SELECT t.relname AS tabla, c.conname, c.contype, c.confdeltype,
           pg_get_constraintdef(c.oid) AS definicion
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'public'
      AND t.relname IN ('duenio','ficha_duenio','mascota','practica','turno','turno_practica')
    ORDER BY t.relname, c.contype, c.conname;
    ```
  - **Verificación** (chequear fila por fila):

    | Restricción | Esperado |
    |---|---|
    | `duenio.email` | `contype = 'u'` |
    | `ficha_duenio.duenio_id` | `contype = 'u'` **y** FK con `confdeltype = 'a'` |
    | `mascota.duenio_id` | FK con `confdeltype = 'r'` (RESTRICT) |
    | `practica.nombre` | `contype = 'u'` |
    | `practica.precio` | `contype = 'c'`, definición `CHECK ((precio > (0)::numeric))` |
    | `turno.mascota_id` | FK con `confdeltype = 'a'` (NO ACTION) |
    | `turno.total` | `contype = 'c'`, definición `CHECK ((total >= (0)::numeric))` |
    | `turno_practica` | PK de **dos columnas** `(turno_id, practica_id)` |
    | `turno_practica.turno_id` | FK con `confdeltype = 'c'` (CASCADE) |
    | `turno_practica.practica_id` | FK con `confdeltype = 'a'` (NO ACTION) |
    | `turno_practica.precio_unitario` | `contype = 'c'`, definición `CHECK ((precio_unitario > (0)::numeric))` |

- [x] **4.3 — Índices de claves foráneas y orden de la PK compuesta** *(30 min)*
  - Ejecutar:
    ```sql
    SELECT tablename, indexname, indexdef FROM pg_indexes
    WHERE schemaname = 'public'
      AND tablename IN ('duenio','ficha_duenio','mascota','practica','turno','turno_practica')
    ORDER BY tablename, indexname;
    ```
  - **Verificación**: existen índices que cubren `mascota (duenio_id)`, `turno (mascota_id)` y `turno_practica (practica_id)`; **no** existe ninguno exclusivo sobre `turno_practica (turno_id)`; el índice de la PK de `turno_practica` muestra `(turno_id, practica_id)` **en ese orden**.

## 5. Verificación de comportamiento por SQL (aceptación / rechazo)

> Todo el bloque va en **una sola transacción** con `ROLLBACK` final: no ensucia la base y se puede repetir.
> **pgAdmin solo muestra el resultado del último `SELECT`** de la pestaña. Por eso ningún conteo se deja como `SELECT` suelto: todos se calculan con `SELECT ... INTO` dentro de un bloque `DO` y se imprimen con `RAISE NOTICE`, que aparecen en la pestaña **Messages**. Lo mismo vale para los casos de rechazo: el `INSERT`/`DELETE` que debe fallar va dentro de un bloque `DO $$ ... EXCEPTION ... $$`, así el error esperado **no aborta** la transacción y el script corre completo de una vez.
> Todos los `NOTICE` de rechazo imprimen **`SQLSTATE` y `SQLERRM`**, para que el código quede a la vista (`23514` CHECK, `23505` única/PK, `23503` clave foránea).
> Usar ids altos (9001+) para no chocar con datos existentes.

- [x] **5.1 — Caso 1: `precio = 0` rechazado por el CHECK** *(20 min)*
  ```sql
  BEGIN;
  DO $$ BEGIN
    INSERT INTO practica (nombre, precio) VALUES ('scratch_c1', 0);
    RAISE NOTICE 'FALLA caso 1: precio 0 fue ACEPTADO';
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'OK caso 1: rechazado por CHECK -> SQLSTATE=% SQLERRM=%', SQLSTATE, SQLERRM;
  END $$;
  ROLLBACK;
  ```
  - **Verificación**: Messages muestra `OK caso 1: rechazado por CHECK -> SQLSTATE=23514 SQLERRM=...`. Repetir con `precio = -1`: mismo resultado. Si aparece `FALLA caso 1`, el `CHECK` no se creó.

- [x] **5.2 — Caso 2: práctica repetida en el mismo turno rechazada por la PK compuesta** *(30 min)*
  ```sql
  BEGIN;
  INSERT INTO duenio (id, nombre, email) VALUES (9001, 'scratch', 'scratch@ejemplo.com');
  INSERT INTO mascota (id, nombre, especie, duenio_id) VALUES (9001, 'scratch', 'perro', 9001);
  INSERT INTO practica (id, nombre, precio) VALUES (9001, 'scratch_prac', 1000.00);
  INSERT INTO turno (id, mascota_id, fecha, motivo, total) VALUES (9001, 9001, now(), 'scratch', 1000.00);
  INSERT INTO turno_practica (turno_id, practica_id, precio_unitario) VALUES (9001, 9001, 1000.00);
  DO $$
  DECLARE v_filas integer;
  BEGIN
    BEGIN
      INSERT INTO turno_practica (turno_id, practica_id, precio_unitario) VALUES (9001, 9001, 1000.00);
      RAISE NOTICE 'FALLA caso 2: duplicado ACEPTADO';
    EXCEPTION WHEN unique_violation THEN
      RAISE NOTICE 'OK caso 2: rechazado por PK compuesta -> SQLSTATE=% SQLERRM=%', SQLSTATE, SQLERRM;
    END;
    SELECT count(*) INTO v_filas FROM turno_practica WHERE turno_id = 9001 AND practica_id = 9001;
    RAISE NOTICE 'caso 2: filas en turno_practica = % (esperado 1)', v_filas;
  END $$;
  ROLLBACK;
  ```
  - **Verificación**: Messages muestra `OK caso 2: rechazado por PK compuesta -> SQLSTATE=23505 ...` y `caso 2: filas en turno_practica = 1 (esperado 1)`.

- [x] **5.3 — Caso 3: borrar un dueño con mascotas rechazado por RESTRICT** *(20 min)*
  ```sql
  BEGIN;
  INSERT INTO duenio (id, nombre, email) VALUES (9002, 'scratch', 'scratch2@ejemplo.com');
  INSERT INTO mascota (id, nombre, especie, duenio_id) VALUES (9002, 'scratch', 'gato', 9002);
  DO $$
  DECLARE v_duenios integer;
  BEGIN
    BEGIN
      DELETE FROM duenio WHERE id = 9002;
      RAISE NOTICE 'FALLA caso 3: el dueño fue BORRADO';
    EXCEPTION WHEN foreign_key_violation THEN
      RAISE NOTICE 'OK caso 3: rechazado por FK RESTRICT -> SQLSTATE=% SQLERRM=%', SQLSTATE, SQLERRM;
    END;
    SELECT count(*) INTO v_duenios FROM duenio WHERE id = 9002;
    RAISE NOTICE 'caso 3: duenios con id 9002 = % (esperado 1)', v_duenios;
  END $$;
  ROLLBACK;
  ```
  - **Verificación**: Messages muestra `OK caso 3: rechazado por FK RESTRICT -> SQLSTATE=23503 ...` y `caso 3: duenios con id 9002 = 1 (esperado 1)`.

- [x] **5.4 — Caso 4 (borde): borrar un turno elimina sus `turno_practica` por CASCADE** *(30 min)*
  ```sql
  BEGIN;
  INSERT INTO duenio (id, nombre, email) VALUES (9003, 'scratch', 'scratch3@ejemplo.com');
  INSERT INTO mascota (id, nombre, especie, duenio_id) VALUES (9003, 'scratch', 'perro', 9003);
  INSERT INTO practica (id, nombre, precio) VALUES (9003, 'scratch_prac3', 1000.00), (9004, 'scratch_prac4', 2000.00);
  INSERT INTO turno (id, mascota_id, fecha, motivo, total) VALUES (9003, 9003, now(), 'scratch', 3000.00);
  INSERT INTO turno_practica (turno_id, practica_id, precio_unitario) VALUES (9003, 9003, 1000.00), (9003, 9004, 2000.00);
  DO $$
  DECLARE v_antes integer;
  BEGIN
    SELECT count(*) INTO v_antes FROM turno_practica WHERE turno_id = 9003;
    RAISE NOTICE 'caso 4: antes = % (esperado 2)', v_antes;
  END $$;
  DELETE FROM turno WHERE id = 9003;
  DO $$
  DECLARE v_despues integer;
          v_practicas integer;
  BEGIN
    SELECT count(*) INTO v_despues FROM turno_practica WHERE turno_id = 9003;
    SELECT count(*) INTO v_practicas FROM practica WHERE id IN (9003, 9004);
    RAISE NOTICE 'caso 4: despues = % (esperado 0)', v_despues;
    RAISE NOTICE 'caso 4: practicas en el catalogo = % (esperado 2)', v_practicas;
  END $$;
  ROLLBACK;
  ```
  - **Verificación**: el `DELETE` **no lanza error** y Messages muestra `antes = 2`, `despues = 0`, `practicas en el catalogo = 2`. Si el `DELETE` falla o `despues = 2`, el `ON DELETE CASCADE` no está en la base.

- [x] **5.5 — Caso 5 (borde): `total = 0` aceptado y `total` negativo rechazado** *(20 min)*
  ```sql
  BEGIN;
  INSERT INTO duenio (id, nombre, email) VALUES (9004, 'scratch', 'scratch4@ejemplo.com');
  INSERT INTO mascota (id, nombre, especie, duenio_id) VALUES (9004, 'scratch', 'perro', 9004);
  DO $$ BEGIN
    INSERT INTO turno (id, mascota_id, fecha, motivo, total) VALUES (9004, 9004, now(), 'scratch total cero', 0);
    RAISE NOTICE 'OK caso 5a: total 0 ACEPTADO';
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'FALLA caso 5a: total 0 fue RECHAZADO -> SQLSTATE=% SQLERRM=%', SQLSTATE, SQLERRM;
  END $$;
  DO $$ BEGIN
    INSERT INTO turno (id, mascota_id, fecha, motivo, total) VALUES (9005, 9004, now(), 'scratch negativo', -0.01);
    RAISE NOTICE 'FALLA caso 5b: total negativo ACEPTADO';
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'OK caso 5b: rechazado por CHECK -> SQLSTATE=% SQLERRM=%', SQLSTATE, SQLERRM;
  END $$;
  ROLLBACK;
  ```
  - **Verificación**: Messages muestra `OK caso 5a: total 0 ACEPTADO` y `OK caso 5b: rechazado por CHECK -> SQLSTATE=23514 ...`. Si sale `FALLA caso 5a`, el CHECK se escribió como `> 0` en lugar de `>= 0`.

## 6. Cierre

- [x] **6.1 — Limpiar los temporales y confirmar el diff** *(30 min)*
  - Borrar `scratch_crear_esquema.py`, `scratch_mapeo.py` y `scratch_verificacion.sql` del disco.
  - **Verificación**: `git status --short` muestra **solo** los cuatro `models.py` modificados; ningún `scratch_*`, ningún archivo fuera de alcance. `python -c "import app.main"` sigue funcionando (los `models.py` no rompen el arranque). `openspec validate "modelos-y-esquema" --type change --strict` responde `is valid`.

## Workflow follow-up

- Archivar el change con `/opsx:archive modelos-y-esquema` y marcar `[x]` en `CHANGES.md` (tarea del archive, no de este change).
- Al escribir el `README.md` ([11]): mencionar como decisión propia **DD-13** (`NO ACTION` donde la consigna no especifica regla de borrado, citando IN-03) y copiar la explicación de 1–2 líneas de por qué `turno_practica.turno_id` no lleva índice propio y `practica_id` sí.
- Avisar a los dueños de [03], [04] y [09] que ya pueden empezar: `reiniciar.py` ([09]) **debe importar los cuatro `models.py`** antes de `create_all`.
