# practicas-catalogo Specification

## Purpose

Gestionar el catálogo de prácticas veterinarias expuesto por la API: alta de una práctica con su precio y consulta del catálogo completo, con garantías de unicidad de nombre y precio positivo delegadas a PostgreSQL, sin consultas previas de existencia.

## Requirements

### Requirement: Alta de práctica válida

El sistema SHALL aceptar `POST /practicas/` con un cuerpo `PracticaCreate` (`nombre` obligatorio, `precio` `Decimal` mayor que cero, sin `id`) y responder **201** con `PracticaRead` persistiendo la práctica en la base.

#### Scenario: Alta exitosa

- **WHEN** se envía `POST /practicas/` con `{"nombre": "Consulta", "precio": "15000.00"}`
- **THEN** responde **201** con `PracticaRead` que incluye `id`, `nombre` y `precio`
- **AND** la práctica queda persistida en la tabla `practica`

#### Scenario: Precio cero rechazado por el DTO

- **WHEN** se envía `POST /practicas/` con `precio = 0`
- **THEN** responde **422** y no se persiste ninguna práctica

#### Scenario: Precio negativo rechazado por el DTO

- **WHEN** se envía `POST /practicas/` con `precio = -1`
- **THEN** responde **422** y no se persiste ninguna práctica

#### Scenario: Cuerpo sin precio rechazado

- **WHEN** se envía `POST /practicas/` sin el campo `precio`
- **THEN** responde **422**

### Requirement: Nombre de práctica único

El sistema SHALL rechazar el alta de una práctica cuyo `nombre` ya exista en el catálogo respondiendo **409** con mensaje propio, capturando el `IntegrityError` de la restricción `UNIQUE` de la base y haciendo `rollback()`, sin realizar una consulta previa de existencia (RN-02, DD-03).

#### Scenario: Nombre repetido responde 409

- **WHEN** ya existe una práctica con `nombre = "Consulta"` y se envía `POST /practicas/` con el mismo `nombre`
- **THEN** responde **409** con mensaje propio
- **AND** no se crea una segunda fila en `practica`

#### Scenario: La base rechaza el duplicado aunque el DTO sea válido

- **WHEN** el DTO es válido pero el `INSERT` viola la restricción `UNIQUE` de `practica.nombre`
- **THEN** el service captura `IntegrityError`, hace `rollback()` y el router responde **409**

### Requirement: Listado del catálogo ordenado por id

El sistema SHALL responder **200** a `GET /practicas/` con el catálogo completo de prácticas ordenado por `id` ascendente (DD-15), sin envoltorio de paginación.

#### Scenario: Catálogo con prácticas

- **WHEN** existen prácticas en la base y se envía `GET /practicas/`
- **THEN** responde **200** con un arreglo de `PracticaRead` ordenado por `id` ascendente

#### Scenario: El orden no depende del orden de inserción

- **WHEN** las prácticas se insertaron en un orden distinto al de su `id`
- **THEN** `GET /practicas/` las devuelve ordenadas por `id` ascendente

### Requirement: Precio serializado como string decimal

`PracticaRead` SHALL serializar el campo `precio` como **string decimal** con dos decimales (por ejemplo `"15000.00"`), nunca como número JSON ni como `float` (DD-06, RN-04).

#### Scenario: Precio sale como string

- **WHEN** se crea o se lista una práctica con `precio = 15000.00`
- **THEN** el JSON de la respuesta contiene `"precio": "15000.00"` (string), no `15000.00` (número)

#### Scenario: Precisión decimal preservada

- **WHEN** una práctica tiene `precio = 12000.00`
- **THEN** la respuesta muestra `"12000.00"` sin pérdida de precisión ni notación científica 