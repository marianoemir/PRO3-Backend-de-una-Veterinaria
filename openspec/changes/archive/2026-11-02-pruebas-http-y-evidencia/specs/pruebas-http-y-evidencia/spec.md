# Spec Delta: pruebas-http-y-evidencia

## Purpose

Proveer la suite de casos de prueba HTTP de la cátedra (C-01 a C-09) y la evidencia de consola del caso C-07, ejecutables tras reiniciar la base, que verifican el contrato de la API sin modificar código de la aplicación.

## ADDED Requirements

### Requirement: Suite .http por caso con respuesta esperada

La suite de pruebas SHALL contener un archivo `test/caso_C-0N.http` para N = 01..09, cada uno con la respuesta esperada en un comentario, ejecutable después de `python reiniciar.py`.

#### Scenario: C-01 parámetro de ruta no entero

- **WHEN** se envía `GET /duenios/abc`
- **THEN** responde **422** sin ejecutar el handler

#### Scenario: C-02 email o nombre repetido

- **WHEN** ya existe un dueño con un email o una práctica con un nombre y se intenta crear otro con el mismo valor
- **THEN** responde **409** con mensaje propio

#### Scenario: C-03 segunda ficha para el mismo dueño

- **WHEN** un dueño ya tiene ficha y se envía `POST /duenios/{id}/ficha` otra vez
- **THEN** responde **409**

#### Scenario: C-04 mascota con dueño inexistente

- **WHEN** se envía `POST /mascotas/` con un `duenio_id` que no existe
- **THEN** responde **409**

#### Scenario: C-04 turno con práctica inexistente

- **WHEN** se envía `POST /turnos/` con una práctica que no está en el catálogo
- **THEN** responde **409** y no queda guardado nada (ni turno ni filas de `turno_practica`)

#### Scenario: C-05 borrar dueño con mascotas

- **WHEN** se envía `DELETE /duenios/{id}` a un dueño con mascotas
- **THEN** responde **409**

#### Scenario: C-05 borrar turno

- **WHEN** se envía `DELETE /turnos/{id}` a un turno existente
- **THEN** responde **204** y sus prácticas ya no están en `turno_practica`

#### Scenario: C-06 turno válido con dos prácticas

- **WHEN** se envía `POST /turnos/` con dos prácticas del catálogo (1 y 3)
- **THEN** responde **201** con los precios copiados y el total calculado (`"27000.00"`)

#### Scenario: C-09 laboratorio y salud

- **WHEN** se envían tres consultas simultáneas a `GET /laboratorio/stock/{vacuna}` y un `GET /health/live` en el medio
- **THEN** el endpoint de salud responde de inmediato

### Requirement: Caso C-07 número fijo de consultas

La suite SHALL documentar que `GET /turnos/{id}` ejecuta la misma cantidad de `SELECT` para un turno con una práctica y para uno con tres, verificable con `echo=True` en la consola.

#### Scenario: Detalle con una práctica

- **WHEN** se lee el detalle de un turno con una práctica con `echo=True`
- **THEN** la consola muestra un número fijo de `SELECT` (2) y no aparece `MissingGreenlet`

#### Scenario: Detalle con tres prácticas

- **WHEN** se lee el detalle de un turno con tres prácticas con `echo=True`
- **THEN** la consola muestra la misma cantidad de `SELECT` que con una práctica

### Requirement: Caso C-08 rechazo por CHECK en la base

La suite SHALL incluir `test/caso_C-08.sql` que ejecute `UPDATE practica SET precio = 0` directo en la base, documentando que la base lo rechaza por el `CHECK`.

#### Scenario: UPDATE precio cero rechazado

- **WHEN** se ejecuta `UPDATE practica SET precio = 0` (o `precio = -1`) directo en PostgreSQL
- **THEN** la base rechaza la operación por violación del `CHECK (precio > 0)` y ninguna fila queda modificada

#### Scenario: Restauración del estado

- **WHEN** se vuelve a ejecutar `python reiniciar.py` tras el caso C-08
- **THEN** el catálogo queda en el estado original del seed

### Requirement: Archivo de evidencia C-07

La suite SHALL incluir `test/evidencia_C-07.txt` con el fragmento de consola (con `echo=True`) que muestra las consultas del detalle de un turno con una práctica y con tres.

#### Scenario: Evidencia presente y completa

- **WHEN** se abre `test/evidencia_C-07.txt`
- **THEN** contiene el fragmento de consola para un turno con una práctica y para uno con tres, con la misma cantidad de `SELECT` en ambos

### Requirement: Aislamiento de test/

El change SHALL modificar únicamente archivos bajo `test/`; si un caso falla, el fallo y el módulo al que pertenece se registran sin parchear código de la aplicación desde `test/`.

#### Scenario: Solo test/ tocado

- **WHEN** se revisa el diff del change
- **THEN** todos los archivos nuevos o modificados están bajo `test/`

#### Scenario: Fallo registrado, no parcheado

- **WHEN** un caso `.http` falla al ejecutarse
- **THEN** se registra el caso, el código de respuesta observado y el módulo dueño, sin editar archivos de `app/`