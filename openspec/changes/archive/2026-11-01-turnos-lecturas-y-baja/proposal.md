# Proposal — turnos-lecturas-y-baja ([07], Mariano)

## Why
El change 06 (`turnos-alta-transaccional`) dejó el módulo `turnos` con alta transaccional y DTO `TurnoRead`, pero falta la lectura y la baja, que cubre los casos C-05 (borrado), C-07 (detalle) y RN-14, RN-15, RN-16.

## What Changes
- `GET /turnos/{id}`: leer con carga anticipada (`joinedload` + `selectinload`) reutilizando el servicio existente `_leer_turno` (con una nueva excepción `TurnoNoEncontrado`).
- `DELETE /turnos/{id}`: borrar usando `session.get` para 404, con `passive_deletes` y la base haciendo `ON DELETE CASCADE`. El router traduce `TurnoNoEncontrado` → `HTTPException(404)`.
- No se modifica `schemas.py` (el DTO `TurnoRead` ya cubre lectura); no se agrega prefijo `/turnos` en `main.py` (ya presente en 06).
- Tareas de evidencia C-07 (captura consola con `echo=True` para 1 práctica y 3 prácticas, contar SELECT).

## Capabilities
- `turnos` (capability existente) — modificado: se agregan los requisitos de lectura y baja.

## Impact
- `app/modules/turnos/router.py`: nuevos endpoints.
- `app/modules/turnos/service.py`: `obtener_turno`, `borrar_turno`, y `TurnoNoEncontrado`.
- No se toca `app/main.py`, ni `schemas.py`.
- `CHANGES.md`: marcar línea del change.
- `openspec/changes/turnos-lecturas-y-baja/` con proposal, design, spec, tasks.
