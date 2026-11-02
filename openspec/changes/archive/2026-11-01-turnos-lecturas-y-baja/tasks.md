# Tasks — turnos-lecturas-y-baja ([07])

Todas en español; verificación por ejecución real (no por inspección visual de código).

- [x] **T1 — GET /turnos/{id} (especificación)**: implementar en `router.py`; reutilizar `_leer_turno` (envuelto en `obtener_turno` del service) → `TurnoRead`; 404 con mensaje propio (`TurnoNoEncontrado` → `HTTPException`). Verificación: `curl /turnos/1` → 200 con estructura del escenario 1; `/turnos/9999` → 404.

- [x] **T2 — DELETE /turnos/{id} (especificación)**: implementar en `router.py`; buscar turno con `session.get(Turno, id)` → si `None`, levantar `TurnoNoEncontrado`; `session.delete` + `commit`. Verificación: 
  - Consola: con `echo=True`, capturar salida; debe mostrar solo `DELETE FROM turno`, sin SELECT ni DELETE sobre turno_practica. 
  - SQL: `SELECT count(*) FROM turno_practica WHERE turno_id = 1` → 2 antes; tras `DELETE /turnos/1` → 0 filas; la consola muestra solo `DELETE FROM turno`, sin SELECT ni DELETE sobre turno_practica.
  - Error: `DELETE /turnos/9999` → 404 sin modificar la base.

- [x] **T3 — Reutilización de DTO / sin duplicar**: confirmar que `TurnoRead` en `schemas.py` cubre lectura; no agregar `TurnoResponse`. Justificar en `design.md` (DD-11, DD-02). Verificación: `grep -n "class TurnoRead" schemas.py` → existente; `grep -n "TurnoResponse"` → vacío.

- [x] **T4 — Evidencia C-07 (console con echo=True)**: con `echo=True` (DD-01), después de `python reiniciar.py`, crear con POST /turnos/ un turno con 1 práctica ([2]) y otro con 3 prácticas ([1, 2, 3]), luego capturar consola completa de la lectura de cada uno (GET /turnos/{id}). Contar SELECT de cada ejecución (esperado: exactamente 2 SELECT fijos por `_leer_turno`).
  - Guardar captura localmente (no en `test/` — eso es del change [10]).
  - No usar `nextval` ni consultar secuencias reales.

- [x] **T5 — No tocar archivos ajenos**: verificar que `app/main.py` no fue editado (prefijo `/turnos` ya puesto en 06); `schemas.py` sin modificaciones; solo `router.py` + `service.py` (si hace falta `obtener_turno` / `borrar_turno`). Verificación: `git diff --name-only` debe listar solo app/modules/turnos/router.py, app/modules/turnos/service.py, CHANGES.md y openspec/.

- [x] **T6 — Cierre**: `openspec validate --strict` y correr `python reiniciar.py` para asegurar que el seed todavía funciona (el change 06 depende de él).

## Cómo verificar cada escenario (de la spec)
| Escenario | Tarea | Comando / paso |
|---|---|---|
| GET existente | T1 | `curl /turnos/1` → 200 con TurnoRead |
| GET no encontrado | T1 | `curl /turnos/9999` → 404 |
| DELETE existente + cascada | T2 + T4 | `DELETE /turnos/1` → 204; `SELECT count(*) FROM turno_practica WHERE turno_id=1` = 0; consola solo DELETE FROM turno |
| DELETE no encontrado | T2 | `DELETE /turnos/9999` → 404 sin modificar la base |
| Constante SELECT | T4 | Contar SELECT en `echo` de 1 vs 3 prácticas → 2 en ambos |
