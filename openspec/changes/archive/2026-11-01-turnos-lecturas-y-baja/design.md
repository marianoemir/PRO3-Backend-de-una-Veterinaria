# Design — turnos-lecturas-y-baja ([07], Mariano)

## Dependencias verificadas
- `[06]` archivado; `app/modules/turnos/` completo (`router.py` con `prefix="/turnos"`, `schemas.py` con `TurnoRead`, `service.py` con `_leer_turno` y carga anticipada). No se edita `main.py` (regla de archivos compartidos, CHANGES.md 62-77).

## Decisiones de dominio (justificadas; no inventadas)

### DD-03 (consulta previa)
Buscar el turno por clave primaria para decidir 404 es la operación misma, no una consulta previa de garantía; la baja la resuelve la base por `ON DELETE CASCADE` (DD-05).

### DD-04 (carga anticipada)
`GET /turnos/{id}` usa `_leer_turno` que ya declara `joinedload(Turno.mascota)` + `selectinload(Turno.practicas).joinedload(TurnoPractica.practica)`. La cantidad fija (2 SELECT) satisface RN-15 y la evidencia C-07.

### DD-05 (cascada por base)
`DELETE /turnos/{id}` delega en `borrar_turno` que llama a `session.get(Turno, id)` → `session.delete(turno)` → `session.commit()`. `Turno.practicas` tiene `passive_deletes=True`; el ORM no emite `DELETE` extra sobre las filas hijas porque `ON DELETE CASCADE` en la base borra `turno_practica`. El CONSOLE debe mostrar solo `DELETE FROM turno`. La verificación de integridad se hace por SQL (`SELECT * FROM turno_practica WHERE turno_id = ?` → 0).

### DD-11 (sin id de fila)
`TurnoRead` ya cubre prácticas sin id de `turno_practica`. No necesitamos modificar `schemas.py`; duplicar DTO violaría la regla de DTO propios del change 06 (DD-11) y agregar un `TurnoResponse` extra no está pedido en la consigna.

### RN-09 / RN-12 (códigos y mensajes)
Los códigos HTTP (200, 204, 404, 409) y los mensajes propios se justifican con RN-09 (borrado de turno) y RN-12 (códigos de error) del `knowledge-base/05_reglas_de_negocio.md`. El router traduce `TurnoNoEncontrado` a `HTTPException(404)` con mensaje propio; el service no conoce HTTP, igual que `crear_turno` en [06].

## Qué no se decide (fuera de alcance / ya decidido)
- Paginación de turnos: fuera (no hay `GET /turnos/`).
- Formato de `fecha`: DD-02 / `_fecha_en_utc` (salida UTC).
- Precio Decimal: DD-06; `TurnoRead.total` y `precio_unitario` ya Decimal.

## Verificación de esquemas
- `schemas.py`: sin cambios (justificado: `TurnoRead` cubre lectura; duplicar violaría reg. propias del change 06).
- `service.py`: se agrega:
  - `obtener_turno` (envuelve `_leer_turno`; `_leer_turno` (líneas 62-91) usa `scalars().one()`, que levanta `NoResultFound`; `obtener_turno` captura eso y convierte a `TurnoNoEncontrado`, sin modificar `crear_turno` que usa `_leer_turno` con éxito garantizado tras flush).
  - `borrar_turno` (usa `session.get`, levanta `TurnoNoEncontrado` si el turno es `None`).
  - `TurnoNoEncontrado(Exception)` (misma familia que `PracticaInexistente` / `TurnoConflicto`).
- `router.py`: nuevo endpoint `DELETE /turnos/{id}`; mismo prefijo existente; ambos endpoints usan el mismo `session: AsyncSession` del DI (`get_session`).

## Evidencia C-07 (captura de consola)
- El seed (`reiniciar.py`) crea un turno con 2 prácticas. Para la evidencia C-07: con `echo=True`, crear con POST /turnos/ un turno con 1 práctica (práctica [2]) y otro con 3 prácticas ([1, 2, 3]) después de `python reiniciar.py`. Capturar consola completa de la lectura de ambos. Guardar captura en variable local (no en `test/` — eso es del change [10]). No usar `nextval` ni consultar secuencias reales; contar SELECT mostrados por el echo (esperado: 2 SELECT fijos para ambas).
- No usar `nextval` ni consultar secuencias reales; contar SELECT mostrados por el echo (esperado: 2 SELECT fijos para ambas).
