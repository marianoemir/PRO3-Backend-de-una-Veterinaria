# Spec Delta: readme-y-entrega

## Purpose

Garantizar que el proyecto se pueda levantar desde cero siguiendo solo el `README.md` y que la entrega cumpla el formato pedido por la consigna.

## ADDED Requirements

### Requirement: Puesta en marcha desde cero

El `README.md` SHALL describir, en orden, entorno virtual, instalación de dependencias, creación de `.env` a partir de `env.example`, creación de la base, `python reiniciar.py` y arranque del servidor, de modo que un entorno limpio llegue a una API funcionando sin pasos implícitos.

#### Scenario: Entorno limpio

- **WHEN** se siguen los pasos del README en un entorno virtual nuevo con una base vacía
- **THEN** `python reiniciar.py` termina con los conteos 2, 1, 3, 4, 1 y 2
- **AND** `GET /health/ready` responde **200**

#### Scenario: Falta el `.env`

- **WHEN** se arranca sin `DATABASE_URL` definida
- **THEN** el proceso termina con código 1 y un mensaje que remite a `env.example`

#### Scenario: Base inexistente

- **WHEN** `python reiniciar.py` apunta a una base que no existe
- **THEN** termina con código 2 sin modificar nada y sin imprimir la clave

### Requirement: Justificación del índice de la clave primaria compuesta

El `README.md` SHALL explicar en una o dos líneas por qué `turno_practica.turno_id` no lleva índice propio: la clave primaria `(turno_id, practica_id)` ya crea un índice con `turno_id` como primera columna.

#### Scenario: Explicación presente

- **WHEN** se lee la sección "Modelo de datos e índices"
- **THEN** aparece la explicación y se aclara que `practica_id` sí lleva índice propio

### Requirement: Decisiones propias del equipo

El `README.md` SHALL presentar DD-08 a DD-15 como decisiones del equipo y no como reglas de la cátedra.

#### Scenario: Decisión no definida por la consigna

- **WHEN** se consulta la sección de decisiones
- **THEN** cada decisión indica su efecto observable y la advertencia de que no es una regla de la cátedra

### Requirement: Entrega sin secretos

El repositorio SHALL incluir `requirements.txt`, `env.example`, `reiniciar.py` y `test/`, y SHALL NOT versionar `.env` ni credenciales reales.

#### Scenario: Revisión de credenciales

- **WHEN** se ejecuta `git ls-files .env`
- **THEN** no devuelve nada
- **AND** `env.example` contiene solo valores de ejemplo
