# laboratorio Specification

## Purpose

Permite al personal de la veterinaria consultar el stock de una vacuna en el laboratorio externo sin bloquear el servicio: la consulta sincrónica de la biblioteca provista se ejecuta fuera del bucle de eventos y el endpoint responde el stock calculado para la vacuna solicitada.

## ADDED Requirements

### Requirement: Consulta de stock de una vacuna

El sistema SHALL exponer `GET /laboratorio/stock/{vacuna}` y responder `200` con un cuerpo JSON `{"vacuna": <vacuna solicitada>, "stock": <entero>}`, donde `stock` es el valor devuelto por la biblioteca sincrónica del laboratorio para esa vacuna. El handler SHALL ser asincrónico.

#### Scenario: Consulta exitosa de una vacuna

- **WHEN** se solicita `GET /laboratorio/stock/rabia`
- **THEN** la respuesta tiene código `200`
- **AND** el cuerpo es `{"vacuna": "rabia", "stock": 15}`

#### Scenario: Vacuna con nombre de un solo carácter

- **WHEN** se solicita `GET /laboratorio/stock/X`
- **THEN** la respuesta tiene código `200`
- **AND** el cuerpo es `{"vacuna": "X", "stock": 11}`

### Requirement: La consulta no bloquea el event loop

Mientras una o más consultas al laboratorio están en curso, el sistema SHALL seguir respondiendo `GET /health/live` de inmediato con `200` y `{"estado": "vivo"}`. La biblioteca sincrónica del laboratorio SHALL ejecutarse fuera del bucle de eventos.

#### Scenario: Tres consultas simultáneas y health en el medio

- **WHEN** se lanzan tres solicitudes simultáneas a `GET /laboratorio/stock/{vacuna}` y, mientras están en curso, se solicita `GET /health/live`
- **THEN** `GET /health/live` responde `200` con `{"estado": "vivo"}` sin esperar a que terminen las consultas al laboratorio
- **AND** las tres consultas al laboratorio terminan con `200` y su `stock` correspondiente

### Requirement: Vacuna con caracteres especiales se preserva en la respuesta

El sistema SHALL devolver en el campo `vacuna` de la respuesta el mismo valor recibido en el path, sin alterarlo, y calcular `stock` a partir de ese valor.

#### Scenario: Vacuna con espacios codificados

- **WHEN** se solicita `GET /laboratorio/stock/vacuna%20antirrabica`
- **THEN** la respuesta tiene código `200`
- **AND** el cuerpo es `{"vacuna": "vacuna antirrabica", "stock": 28}`