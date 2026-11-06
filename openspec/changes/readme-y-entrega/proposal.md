# Propuesta: readme-y-entrega

> Dueño: **Facundo**. Dependencia: change 10 archivado. Artefactos creados **retroactivamente** el 2026-11-05: el README se escribió y mergeó (PR #15) antes de abrir el change en OpenSpec; acá se deja el registro y la verificación de cierre.

## Why

La consigna exige un `README.md` con los pasos para levantar el proyecto desde cero y la explicación del índice de `turno_practica.turno_id`, además de `requirements.txt`, `env.example`, `reiniciar.py` y `test/`. Un proyecto que no levanta o no crea su esquema con `python reiniciar.py` sobre una base vacía no se corrige hasta que se subsane, así que la entrega depende de que esos pasos funcionen tal cual están escritos.

## What Changes

- `README.md` con requisitos, entorno virtual por shell, instalación, `.env`, creación de la base (pgAdmin), `python reiniciar.py` y arranque del servidor.
- Tabla de endpoints y códigos, cómo correr los `.http` y el `.sql` del caso C-08, y enlace a `test/evidencia_C-07.txt`.
- Explicación del índice de `turno_practica.turno_id` (la PK compuesta ya lo cubre).
- Sección de decisiones propias del equipo (DD-08 a DD-15) y checklist de entrega.
- **Ajustes de cierre** detectados en la revisión final: `PATCH /duenios/{id}` con `null` explícito pasa de 409 a **422**; los textos obligatorios no aceptan cadena vacía; `caso_C-05.http` verifica el 404 posterior al borrado; `requirements.txt` queda descrito como "versiones fijadas".

## Capabilities

### New Capabilities

- `readme-y-entrega`: documentación de puesta en marcha y checklist de entrega verificable desde cero.

### Modified Capabilities

- `duenios-y-ficha`: el `PATCH` rechaza `null` explícito en `nombre` y `email` con 422 (antes: 409 por `NOT NULL`).

## Impact

- **Código afectado**: `app/modules/*/schemas.py` (validaciones de DTO), `app/modules/turnos/{router,service}.py` (limpieza sin cambio de contrato), `README.md`, `test/caso_C-05.http`.
- **Base de datos**: sin cambios de esquema ni de datos.
- **Riesgo principal**: instrucciones que no funcionen en una máquina limpia. Mitigación: tarea 3 (venv nuevo con Python 3.12 y README al pie de la letra).
