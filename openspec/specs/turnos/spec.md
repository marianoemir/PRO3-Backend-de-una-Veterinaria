# turnos Specification

## Purpose
Reserva un turno para una mascota junto con las prácticas que se le van a realizar, como una operación atómica: el servidor toma el precio vigente del catálogo en ese momento, calcula el total y garantiza que o queda el turno completo con todas sus prácticas, o no queda nada.

## Requirements

### Requirement: Reserva atómica de un turno con sus prácticas

`POST /turnos/` SHALL crear el turno y todas sus filas de práctica en una sola operación: o quedan todos los registros, o no queda ninguno. La respuesta SHALL ser **201** con `id`, `fecha`, `motivo`, `total`, la mascota resumida (`id`, `nombre`, `especie`) y las prácticas del turno (`practica_id`, `nombre`, `precio_unitario`).

#### Scenario: Alta válida con dos prácticas del catálogo

- **WHEN** se hace `POST /turnos/` con `{"mascota_id": 1, "fecha": "2026-11-12T10:30:00-03:00", "motivo": "Control anual", "practicas": [{"practica_id": 1}, {"practica_id": 3}]}` sobre la base recién reiniciada
- **THEN** responde **201**
- **AND** el cuerpo trae `"id": 2`, `"total": "27000.00"`, `"mascota": {"id": 1, "nombre": "Toby", "especie": "perro"}` y las prácticas 1 ("Consulta", `"15000.00"`) y 3 ("Vacuna antirrábica", `"12000.00"`)
- **AND** `turno` tiene una fila nueva con `total = 27000.00` y `turno_practica` tiene exactamente 2 filas nuevas para ese turno

#### Scenario: Las prácticas no llevan id de fila

- **WHEN** se inspecciona la lista `practicas` de la respuesta de un alta válida
- **THEN** cada elemento tiene exactamente `practica_id`, `nombre` y `precio_unitario`
- **AND** ningún elemento incluye un campo `id`, porque `turno_practica` no tiene esa columna

### Requirement: El servidor toma el precio del catálogo y calcula el total

El precio de cada práctica SHALL copiarse del catálogo a `turno_practica.precio_unitario`, y `turno.total` SHALL ser la suma de esos importes calculada por el servidor con aritmética decimal exacta. El cuerpo del alta MUST NOT aportar precios ni totales: si el cliente los envía, no se usan.

#### Scenario: Un total enviado por el cliente no se respeta

- **WHEN** se hace `POST /turnos/` con las prácticas 1 y 3 y se agrega `"total": "1.00"` y `"precio": "1.00"` dentro de cada práctica
- **THEN** responde **201** con `"total": "27000.00"`
- **AND** `turno_practica.precio_unitario` vale `15000.00` y `12000.00`, y `turno.total` vale `27000.00`
- **AND** los importes se serializan como string decimal, nunca como número de punto flotante

### Requirement: El precio queda congelado al reservar

Los importes de un turno SHALL quedar fijados en el momento del alta: modificar después el precio de una práctica en el catálogo MUST NOT alterar el `precio_unitario` ni el `total` de los turnos ya reservados.

#### Scenario: Cambio de precio posterior al alta

- **WHEN** se crea un turno con la práctica 1 y después se actualiza `practica.precio` de esa práctica por SQL
- **THEN** el `precio_unitario` de la fila de `turno_practica` del turno creado sigue siendo el precio anterior
- **AND** `turno.total` sigue siendo la suma de los importes del momento del alta

### Requirement: La fecha se devuelve en UTC

La `fecha` del turno SHALL interpretarse y devolverse en UTC, con independencia del offset con que se haya enviado. Una `fecha` sin offset SHALL interpretarse como UTC, nunca como la zona horaria de la máquina que ejecuta la API.

#### Scenario: Entrada con offset local y salida en UTC

- **WHEN** se hace `POST /turnos/` con `"fecha": "2026-11-12T10:30:00-03:00"`
- **THEN** la respuesta trae `"fecha": "2026-11-12T13:30:00Z"`
- **AND** la fila de `turno` guarda ese mismo instante

#### Scenario: Entrada sin offset

- **WHEN** se hace `POST /turnos/` con `"fecha": "2026-11-12T13:30:00"` (sin zona horaria) desde cualquier máquina
- **THEN** la respuesta trae `"fecha": "2026-11-12T13:30:00Z"`
- **AND** el instante guardado no depende de la zona horaria del sistema operativo ni de la sesión de PostgreSQL

### Requirement: Una práctica inexistente no guarda nada

Si alguna de las prácticas pedidas no existe en el catálogo, el alta SHALL responder **409** y MUST NOT persistir el turno ni ninguna de las filas de práctica pedidas: la base SHALL quedar exactamente como estaba.

#### Scenario: Alta con una práctica inexistente

- **WHEN** se hace `POST /turnos/` con `[{"practica_id": 1}, {"practica_id": 99999}]`
- **THEN** responde **409** con un mensaje propio que nombra las prácticas que no existen
- **AND** el conteo de `turno` y el de `turno_practica` son los mismos que antes de la petición
- **AND** la práctica válida 1 tampoco quedó guardada en ningún turno nuevo

### Requirement: Una práctica repetida en el turno es rechazada

Un turno MUST NOT contener la misma práctica dos veces. La garantía SHALL ser la clave primaria compuesta de `turno_practica`, y el rechazo SHALL traducirse a **409** sin dejar nada guardado.

#### Scenario: La misma práctica dos veces

- **WHEN** se hace `POST /turnos/` con `[{"practica_id": 1}, {"practica_id": 1}]`
- **THEN** responde **409** con un mensaje propio que indica que la práctica está repetida
- **AND** ni el turno ni ninguna fila de `turno_practica` quedan guardados

### Requirement: Una mascota inexistente es rechazada por la clave foránea

Si la mascota indicada no existe, el alta SHALL responder **409** sin crear el turno ni sus prácticas. La garantía SHALL ser la clave foránea de `turno.mascota_id`, no una consulta previa de existencia.

#### Scenario: Alta con mascota inexistente

- **WHEN** se hace `POST /turnos/` con `"mascota_id": 99999` y prácticas válidas
- **THEN** responde **409** con un mensaje propio que indica que la mascota no existe
- **AND** el conteo de `turno` y el de `turno_practica` no cambian

### Requirement: Contrato del cuerpo del alta

El cuerpo del alta SHALL exigir `mascota_id`, `fecha`, `motivo` y una lista `practicas` con al menos un elemento; cada elemento SHALL aportar solo `practica_id`. Cuando el cuerpo no cumple el contrato, la respuesta SHALL ser **422** y no se SHALL escribir nada en la base.

#### Scenario: Lista de prácticas vacía

- **WHEN** se hace `POST /turnos/` con `"practicas": []`
- **THEN** responde **422**
- **AND** el conteo de `turno` y el de `turno_practica` no cambian

#### Scenario: Falta el motivo o la mascota

- **WHEN** se hace `POST /turnos/` sin el campo `motivo`, o sin `mascota_id`, o con `practicas` ausente
- **THEN** responde **422**
- **AND** no se escribe ninguna fila

### Requirement: La respuesta no depende de carga perezosa

La respuesta del alta SHALL armarse con carga anticipada declarada, de modo que la cantidad de consultas de lectura no crezca con la cantidad de prácticas del turno y ninguna lectura falle por carga perezosa en contexto asincrónico.

#### Scenario: Misma cantidad de consultas con una y con tres prácticas

- **WHEN** se comparan las sentencias registradas por el motor al dar de alta un turno con 1 práctica y otro con 3
- **THEN** la cantidad de `SELECT` de lectura es la misma en ambos casos
- **AND** ninguna petición falla con un error de carga perezosa (`MissingGreenlet`)

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
