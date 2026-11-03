# mascotas-y-paginacion Specification

## Purpose
Registrar mascotas a nombre de un dueño existente y consultarlas por id o por páginas acotadas, dejando que la base garantice la pertenencia al dueño y manteniendo un número fijo de consultas en todas las lecturas.

## Requirements

### Requirement: Alta de mascota

`POST /mascotas/` SHALL aceptar `nombre`, `especie` y `duenio_id` (sin `id`) y responder **201** con la mascota creada y su dueño resumido. Un `duenio_id` inexistente SHALL responder **409** porque la clave foránea rechaza la escritura, sin consultar antes si el dueño existe. Un cuerpo que no cumple el contrato SHALL responder **422** (RN-10, RN-12, DD-03, DD-12).

#### Scenario: Alta exitosa

- **WHEN** se envía `POST /mascotas/` con `{"nombre": "Luna", "especie": "gato", "duenio_id": 1}` sobre la base recién reiniciada
- **THEN** responde **201** con `id`, `nombre`, `especie` y `"duenio": {"id": 1, "nombre": "Ana Gómez"}`
- **AND** queda exactamente una fila nueva en la tabla `mascota` con esos valores

#### Scenario: Dueño inexistente rechazado por la clave foránea

- **WHEN** se envía `POST /mascotas/` con `{"nombre": "Luna", "especie": "gato", "duenio_id": 99999}`
- **THEN** responde **409** con un mensaje propio
- **AND** el conteo de filas de `mascota` no cambia

#### Scenario: Sin consulta previa de existencia del dueño

- **WHEN** se envía `POST /mascotas/` con un `duenio_id` inexistente y el registro de sentencias del motor activado
- **THEN** el registro muestra el `INSERT` rechazado y su `ROLLBACK`
- **AND** no aparece ningún `SELECT` sobre `duenio` para verificar si el dueño existe (DD-03)

#### Scenario: Cuerpo inválido

- **WHEN** se envía `POST /mascotas/` sin `duenio_id`, o con `especie` vacía, o con `duenio_id` que no es un entero
- **THEN** responde **422**
- **AND** el conteo de filas de `mascota` no cambia

#### Scenario: El id enviado por el cliente se ignora

- **WHEN** se envía `POST /mascotas/` con `{"id": 999, "nombre": "Luna", "especie": "gato", "duenio_id": 1}`
- **THEN** responde **201** con un `id` generado por la base, distinto de `999`
- **AND** no existe ninguna fila con `id = 999` en `mascota`

### Requirement: Detalle de mascota con su dueño

`GET /mascotas/{id}` SHALL responder **200** con la mascota y su dueño resumido, obtenidos con carga anticipada en la misma consulta, y **404** con mensaje propio si la mascota no existe (RN-12, RN-14, RN-15).

#### Scenario: Mascota existente

- **WHEN** se consulta `GET /mascotas/1` sobre la base recién reiniciada
- **THEN** responde **200** con `id`, `nombre`, `especie` y el dueño resumido de esa mascota
- **AND** el `duenio.id` corresponde al dueño real de la mascota en la tabla `mascota`

#### Scenario: Mascota inexistente

- **WHEN** se consulta `GET /mascotas/99999`
- **THEN** responde **404** con un mensaje propio
- **AND** no se modifica ninguna fila de la base

#### Scenario: Una sola consulta y sin carga perezosa

- **WHEN** se consulta el detalle de una mascota con el registro de sentencias del motor activado
- **THEN** se ejecuta un único `SELECT` con `JOIN` a `duenio`
- **AND** la respuesta no falla con `MissingGreenlet` (RN-16)

### Requirement: Listado paginado con envoltorio fijo

`GET /mascotas/?page=&size=` SHALL responder **200** con el envoltorio `{ items, total, page, size, pages }`, `size` por defecto **20** y acotado a **1..100**, con `items` ordenados por `id` ascendente. `total` SHALL salir de un `count(*)` y la página de un `offset`/`limit`: **dos consultas fijas** (RN-13, RN-15, DD-15).

#### Scenario: Primera página con valores por defecto

- **WHEN** se consulta `GET /mascotas/` sin parámetros sobre la base recién reiniciada, que tiene 3 mascotas
- **THEN** responde **200** con `page: 1`, `size: 20`, `total: 3`, `pages: 1` y 3 elementos en `items`
- **AND** los elementos vienen ordenados por `id` ascendente y cada uno incluye su dueño resumido

#### Scenario: Size fuera del rango permitido

- **WHEN** se consulta `GET /mascotas/?size=0` y luego `GET /mascotas/?size=101`
- **THEN** ambas peticiones responden **422**
- **AND** ninguna de las dos ejecuta una consulta sobre `mascota`

#### Scenario: Página más allá de pages

- **WHEN** se consulta `GET /mascotas/?page=99&size=20` sobre una base con 3 mascotas, donde `pages` es 1
- **THEN** responde **422**
- **AND** el cuerpo no devuelve `items` vacío, porque el código de error es el que informa el problema

#### Scenario: Page fuera del contrato 1-based

- **WHEN** se consulta `GET /mascotas/?page=0` o `GET /mascotas/?page=-1`
- **THEN** responde **422**
- **AND** no se ejecuta ninguna consulta con un `offset` negativo

#### Scenario: Base vacía responde 200 en la primera página

- **WHEN** se consulta `GET /mascotas/` sobre una base sin ninguna fila en `mascota`
- **THEN** responde **200** con `"items": []`, `"total": 0`, `"page": 1`, `"size": 20` y `"pages": 0`
- **AND** no responde 422, porque la primera página siempre responde aunque no haya resultados

#### Scenario: Dos consultas fijas

- **WHEN** se consulta `GET /mascotas/` con el registro de sentencias del motor activado, primero con 3 mascotas y después con 10
- **THEN** en ambos casos se ejecutan exactamente dos `SELECT`: uno de `count(*)` y uno de la página con `JOIN` a `duenio`
- **AND** la cantidad de consultas no crece con la cantidad de mascotas ni con la cantidad de elementos de la página (RN-15)

### Requirement: Contrato de endpoints acotado a la consigna

El módulo SHALL exponer únicamente `POST /mascotas/`, `GET /mascotas/` y `GET /mascotas/{id}`. La baja y la edición de mascotas MUST NOT existir, porque no están en la tabla de endpoints (IN-02, RN-12).

#### Scenario: No hay baja de mascotas

- **WHEN** se envía `DELETE /mascotas/1`
- **THEN** responde **405**
- **AND** la fila de `mascota` con `id = 1` sigue existiendo

#### Scenario: Rutas publicadas

- **WHEN** se inspecciona `GET /openapi.json`
- **THEN** aparecen exactamente `POST /mascotas/`, `GET /mascotas/` y `GET /mascotas/{mascota_id}`
- **AND** no aparece ninguna operación `DELETE`, `PATCH` ni `PUT` sobre `/mascotas`
