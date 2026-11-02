# Spec Delta: duenios-y-ficha

## Purpose

Gestionar el padrón de dueños de la veterinaria y su ficha de contacto uno a uno: alta con email único, consulta con la ficha precargada, corrección parcial, baja bloqueada por las mascotas o la ficha existentes, carga de una única ficha por dueño y consulta de las mascotas del dueño como lista simple.

## ADDED Requirements

### Requirement: Alta de dueño

`POST /duenios/` SHALL aceptar un cuerpo con `nombre` y `email` (sin `id`) y responder **201** con el dueño creado. Un cuerpo que no cumple el contrato SHALL responder **422** y MUST NOT escribir nada. El `id` que el cliente envíe MUST ignorarse (RN-10).

#### Scenario: Alta exitosa

- **WHEN** se envía `POST /duenios/` con `{"nombre": "Ana Pérez", "email": "ana@ejemplo.com"}`
- **THEN** responde **201** con `id`, `nombre`, `email` y `"ficha": null`
- **AND** la fila queda persistida en la tabla `duenio`

#### Scenario: El id enviado por el cliente se ignora

- **WHEN** se envía `POST /duenios/` con `{"id": 999, "nombre": "Ana", "email": "ana@ejemplo.com"}`
- **THEN** responde **201** con un `id` generado por la base, distinto de `999`
- **AND** no existe ninguna fila con `id = 999` en `duenio`

#### Scenario: Cuerpo inválido

- **WHEN** se envía `POST /duenios/` sin el campo `email`, o con `email` de un tipo que no es texto
- **THEN** responde **422**
- **AND** el conteo de filas de `duenio` no cambia

### Requirement: Email de dueño único garantizado por la base

El sistema SHALL rechazar el alta de un dueño cuyo `email` ya exista respondiendo **409** con mensaje propio, capturando el `IntegrityError` de la restricción `UNIQUE` y deshaciendo la transacción. El alta MUST NOT consultar antes si el email existe (RN-01, DD-03).

#### Scenario: Email repetido responde 409

- **WHEN** ya existe un dueño con `email = "ana@ejemplo.com"` y se envía `POST /duenios/` con ese mismo email
- **THEN** responde **409** con un mensaje propio
- **AND** el conteo de filas de `duenio` no cambia

#### Scenario: La sesión sigue usable después del conflicto

- **WHEN** después de un 409 por email repetido se envía `POST /duenios/` con un email distinto y válido
- **THEN** responde **201** y el dueño queda persistido
- **AND** la petición no falla por una transacción en estado inválido

#### Scenario: Sin consulta previa de existencia

- **WHEN** se repite un email con el registro de sentencias del motor activado
- **THEN** el registro muestra el `INSERT` rechazado y su `ROLLBACK`
- **AND** no aparece ningún `SELECT` sobre `duenio` filtrado por `email`

#### Scenario: El email distingue mayúsculas de minúsculas

- **WHEN** existe un dueño con `email = "A@ejemplo.com"` y se da de alta otro con `email = "a@ejemplo.com"`
- **THEN** responde **201**, porque el `UNIQUE` de PostgreSQL es sensible a mayúsculas (DD-09)
- **AND** la tabla `duenio` tiene dos filas con esos dos emails

### Requirement: Detalle de dueño con su ficha

`GET /duenios/{id}` SHALL responder **200** con el dueño y su ficha anidada, o `"ficha": null` si no tiene, obtenida con carga anticipada en la misma consulta. Un id inexistente SHALL responder **404** y un id que no es entero SHALL responder **422** (RN-12, RN-14, RN-15).

#### Scenario: Dueño con ficha

- **WHEN** se consulta `GET /duenios/{id}` de un dueño que tiene ficha
- **THEN** responde **200** con `id`, `nombre`, `email` y `ficha` con `id`, `duenio_id`, `telefono` y `direccion`
- **AND** la ficha corresponde a ese dueño

#### Scenario: Dueño sin ficha

- **WHEN** se consulta `GET /duenios/{id}` de un dueño que no cargó ficha
- **THEN** responde **200** con `"ficha": null`
- **AND** no se produce ningún error de carga perezosa

#### Scenario: Id inexistente

- **WHEN** se consulta `GET /duenios/99999`
- **THEN** responde **404** con un mensaje propio

#### Scenario: Id no entero

- **WHEN** se consulta `GET /duenios/abc`
- **THEN** responde **422**
- **AND** la petición no llega a consultar la base

#### Scenario: Número fijo de consultas

- **WHEN** se consulta el detalle de un dueño con ficha y el de uno sin ficha con el registro de sentencias activado
- **THEN** en ambos casos se ejecuta un único `SELECT` de lectura del dueño con su ficha
- **AND** la cantidad de consultas no depende de si la ficha existe (RN-15)

### Requirement: PATCH parcial de dueño

`PATCH /duenios/{id}` SHALL aplicar únicamente los campos presentes en el cuerpo, sin borrar los no enviados, y responder **200** con el dueño y su ficha. Un id inexistente SHALL responder **404**, un email que colisione **409** y un cuerpo inválido **422** (RN-11, DD-08).

#### Scenario: Cambio de un solo campo

- **WHEN** se envía `PATCH /duenios/{id}` con `{"nombre": "Ana Gómez"}` sobre un dueño que tenía otro nombre y un email
- **THEN** responde **200** con el nombre nuevo y el **email sin cambios**
- **AND** la fila de `duenio` conserva el email anterior

#### Scenario: Cuerpo vacío no modifica nada

- **WHEN** se envía `PATCH /duenios/{id}` con `{}`
- **THEN** responde **200** con el dueño sin cambios
- **AND** ni el `nombre` ni el `email` se vacían

#### Scenario: Email que colisiona

- **WHEN** se envía `PATCH /duenios/{id}` con el email de otro dueño existente
- **THEN** responde **409** con un mensaje propio
- **AND** el email original del dueño editado queda intacto

#### Scenario: Id inexistente

- **WHEN** se envía `PATCH /duenios/99999` con un cuerpo válido
- **THEN** responde **404**
- **AND** no se modifica ninguna fila

#### Scenario: Cuerpo inválido

- **WHEN** se envía `PATCH /duenios/{id}` con `{"email": 123}`
- **THEN** responde **422**
- **AND** el dueño no se modifica

### Requirement: Baja de dueño

`DELETE /duenios/{id}` SHALL responder **204** sin cuerpo cuando el dueño se puede borrar, **404** si no existe y **409** cuando la base rechaza el borrado, deshaciendo la transacción. El rechazo MUST decidirlo la base y el servicio MUST NOT borrar las filas hijas por su cuenta (RN-08, DD-13).

#### Scenario: Baja exitosa

- **WHEN** se envía `DELETE /duenios/{id}` sobre un dueño sin mascotas y sin ficha
- **THEN** responde **204** sin cuerpo
- **AND** la fila ya no existe en `duenio`

#### Scenario: Dueño con mascotas

- **WHEN** se envía `DELETE /duenios/{id}` sobre un dueño que tiene al menos una mascota
- **THEN** responde **409** con un mensaje propio
- **AND** el dueño y todas sus mascotas siguen existiendo, porque la base lo impide con `ON DELETE RESTRICT` (RN-08)

#### Scenario: Dueño con ficha y sin mascotas

- **WHEN** se envía `DELETE /duenios/{id}` sobre un dueño que tiene ficha pero ninguna mascota
- **THEN** responde **409** con un mensaje propio
- **AND** el dueño y su ficha siguen existiendo, porque la FK de `ficha_duenio` no declara `ON DELETE` y queda en `NO ACTION` (DD-13, IN-03)

#### Scenario: Id inexistente

- **WHEN** se envía `DELETE /duenios/99999`
- **THEN** responde **404**
- **AND** no se borra ninguna fila

### Requirement: Alta de ficha del dueño

`POST /duenios/{id}/ficha` SHALL crear la ficha del dueño con `telefono` y `direccion` obligatorios y responder **201** con la ficha creada. Un dueño inexistente SHALL responder **404**, un dueño que ya tiene ficha **409** por el `UNIQUE` de `duenio_id`, y un cuerpo sin `telefono` o sin `direccion` **422** (RN-03, DD-12).

#### Scenario: Alta exitosa

- **WHEN** se envía `POST /duenios/{id}/ficha` con `{"telefono": "1144556677", "direccion": "Calle Falsa 123"}` sobre un dueño sin ficha
- **THEN** responde **201** con `id`, `duenio_id`, `telefono` y `direccion`
- **AND** queda exactamente una fila nueva en `ficha_duenio` para ese dueño

#### Scenario: Segunda ficha rechazada

- **WHEN** se envía `POST /duenios/{id}/ficha` sobre un dueño que ya tiene ficha
- **THEN** responde **409** con un mensaje propio
- **AND** `ficha_duenio` sigue teniendo una sola fila para ese dueño, con los datos originales

#### Scenario: Dueño inexistente

- **WHEN** se envía `POST /duenios/99999/ficha` con un cuerpo válido
- **THEN** responde **404**
- **AND** no se escribe ninguna fila en `ficha_duenio`

#### Scenario: Falta un campo obligatorio

- **WHEN** se envía `POST /duenios/{id}/ficha` sin `telefono` o sin `direccion`
- **THEN** responde **422**
- **AND** no se escribe ninguna fila en `ficha_duenio`

### Requirement: Mascotas de un dueño como lista simple

`GET /duenios/{id}/mascotas` SHALL responder **200** con un arreglo JSON simple de las mascotas del dueño —`id`, `nombre` y `especie`— ordenado por `id` ascendente, sin envoltorio de paginación. Un dueño sin mascotas SHALL responder **200** con `[]` y un dueño inexistente **404** (DD-10, DD-15).

#### Scenario: Dueño con mascotas

- **WHEN** se consulta `GET /duenios/{id}/mascotas` de un dueño con dos mascotas
- **THEN** responde **200** con un arreglo de dos elementos con `id`, `nombre` y `especie`
- **AND** cada elemento corresponde a ese dueño y el arreglo está ordenado por `id` ascendente

#### Scenario: Dueño sin mascotas

- **WHEN** se consulta `GET /duenios/{id}/mascotas` de un dueño que no tiene mascotas
- **THEN** responde **200** con `[]`
- **AND** no responde 404, porque el dueño existe

#### Scenario: Dueño inexistente

- **WHEN** se consulta `GET /duenios/99999/mascotas`
- **THEN** responde **404**
- **AND** no responde `[]`, para no confundir "dueño inexistente" con "dueño sin mascotas"

#### Scenario: Sin envoltorio de paginación

- **WHEN** se inspecciona el cuerpo de una respuesta 200 de `GET /duenios/{id}/mascotas`
- **THEN** el cuerpo es un arreglo JSON
- **AND** no incluye las claves `items`, `total`, `page`, `size` ni `pages`
