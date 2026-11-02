## ADDED Requirements

### Requirement: Detalle de un turno con carga anticipada
El sistema SHALL responder GET /turnos/{id} con el turno, su mascota y sus prácticas (TurnoRead), usando una consulta base con joinedload de la mascota y selectinload de las prácticas con joinedload de la práctica, de modo que el número de consultas no dependa de la cantidad de prácticas.

#### Scenario: Turno existente
- **WHEN** se envía GET /turnos/{id} con el id de un turno existente
- **THEN** responde 200 con TurnoRead (id, fecha en UTC, motivo, total como string, mascota resumida y prácticas ordenadas por practica_id sin id de fila)

#### Scenario: Turno inexistente
- **WHEN** se envía GET /turnos/9999 y no existe ese turno
- **THEN** responde 404 con mensaje propio y la base no se modifica

#### Scenario: Número fijo de consultas
- **WHEN** se lee el detalle de un turno con 1 práctica y el de un turno con 3 prácticas, con echo=True
- **THEN** ambas lecturas ejecutan exactamente 2 SELECT y ninguna falla con MissingGreenlet

### Requirement: Baja de un turno con borrado en cascada por la base
El sistema SHALL responder DELETE /turnos/{id} buscando el turno por clave primaria sin cargar sus prácticas, borrándolo y confirmando la transacción; las filas de turno_practica las elimina la base por ON DELETE CASCADE y el ORM no las toca.

#### Scenario: Turno existente
- **WHEN** se envía DELETE /turnos/{id} con el id de un turno existente
- **THEN** responde 204, no quedan filas en turno_practica con ese turno_id y la consola solo muestra DELETE FROM turno, sin SELECT ni DELETE sobre turno_practica

#### Scenario: Turno inexistente
- **WHEN** se envía DELETE /turnos/9999 y no existe ese turno
- **THEN** responde 404 con mensaje propio y la base no se modifica
