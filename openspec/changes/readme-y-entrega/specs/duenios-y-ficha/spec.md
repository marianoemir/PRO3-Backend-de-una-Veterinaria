# Spec Delta: duenios-y-ficha

## MODIFIED Requirements

### Requirement: PATCH parcial de dueño

`PATCH /duenios/{id}` SHALL aplicar únicamente los campos presentes en el cuerpo, sin borrar los no enviados, y responder **200** con el dueño y su ficha. Un id inexistente SHALL responder **404**, un email que colisione **409** y un cuerpo inválido **422**, incluido un `null` explícito en `nombre` o `email` (RN-11, DD-08).

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

#### Scenario: Null explícito

- **WHEN** se envía `PATCH /duenios/{id}` con `{"nombre": null}`
- **THEN** responde **422**
- **AND** el dueño no se modifica
