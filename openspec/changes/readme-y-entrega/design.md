# Design — readme-y-entrega ([11], Facundo)

## Context

Todos los módulos y la evidencia (changes 01 a 10) están archivados. Este change cierra la entrega: documentación reproducible y un último repaso de coherencia entre código, README y consigna.

## Goals / Non-Goals

**Goals:**

- Que alguien con Python 3.12+ y PostgreSQL 16+ levante el proyecto siguiendo solo el README.
- Que el README presente DD-08 a DD-15 como decisiones del equipo, no como reglas de la cátedra.

**Non-Goals:**

- No agregar endpoints, Docker, CI, Alembic ni autenticación.

## Decisions

### README por shell

Se documentan PowerShell, CMD, Git Bash y Linux/macOS por separado, incluida la alternativa cuando PowerShell bloquea la activación del entorno virtual. La base se crea desde pgAdmin para no depender de `psql` en el `PATH`.

### `requirements.txt` con versiones fijadas

Se fijan versiones exactas (`==`) para que la instalación sea reproducible. La consigna pide versiones *mínimas*; las fijadas son todas iguales o superiores. Si la instalación falla en un entorno limpio, se aflojan a `>=` con los mínimos de la consigna.

### Ajuste de cierre: `PATCH` con `null` explícito → 422

**Reemplaza** la decisión registrada en `openspec/changes/archive/2026-11-01-duenios-y-ficha/design.md` (caso borde: `null` explícito → 409 por `NOT NULL`). Motivo: la consigna pide 422 "si el cuerpo o los parámetros no cumplen el contrato", y `nombre`/`email` son NOT NULL, por lo que un `null` es un cuerpo inválido y no un rechazo de la base. Se resuelve con un `field_validator` en `DuenioUpdate`: omitir el campo sigue siendo válido (`exclude_unset`), enviarlo como `null` no.

### Ajuste de cierre: textos obligatorios no vacíos

`nombre`, `email`, `especie`, `motivo`, `telefono` y `direccion` llevan `min_length=1`. No se valida el formato del email ni fechas pasadas (DD-12).

## Risks / Trade-offs

- [Riesgo] Pins exactos que no resuelvan en Python 3.12. → Mitigación: `pip install -r requirements.txt` y `pip check` en un venv nuevo (tarea 3.1).
- [Riesgo] Evidencia C-07 grabada con una versión anterior del código. → Mitigación: regenerarla con la versión final (tarea 3.3).
