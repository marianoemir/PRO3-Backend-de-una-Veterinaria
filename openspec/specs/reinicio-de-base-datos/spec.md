# reinicio-de-base-datos Specification

## Purpose
Deja la base de la veterinaria en un estado conocido y reproducible —esquema reconstruido desde los modelos y poblado con un seed mínimo— para que la evaluación y los changes posteriores partan siempre del mismo punto, con los identificadores que el enunciado usa en sus ejemplos.

## Requirements

### Requirement: Reinicio del esquema y carga de datos iniciales en una sola ejecución

Ejecutar el script de reinicio SHALL dejar la base en el estado conocido del proyecto: descartar las tablas existentes, recrearlas con el esquema declarado por los modelos y cargar el seed mínimo, sobre la base indicada por `DATABASE_URL`. Una sola ejecución MUST alcanzar para pasar de una base vacía a ese estado, sin pasos manuales intermedios.

#### Scenario: Base vacía poblada con los conteos exactos

- **WHEN** se ejecuta `python reiniciar.py` con `DATABASE_URL` configurada en el `.env` y la base sin ninguna tabla
- **THEN** el proceso termina con código de salida `0`
- **AND** `duenio` tiene 2 filas, `ficha_duenio` 1, `mascota` 3, `practica` 4, `turno` 1 y `turno_practica` 2
- **AND** las seis tablas existen en el esquema `public` con las columnas de `knowledge-base/04_modelo_de_datos.md`

### Requirement: Datos iniciales con los identificadores del enunciado

El seed SHALL cargar 2 dueños (el `1` con ficha y el `2` sin ficha), 3 mascotas, 4 prácticas y 1 turno con 2 prácticas, respetando que `mascota` 1 sea "Toby" (especie perro) del dueño 1, `practica` 1 sea "Consulta" a `15000.00` y `practica` 3 sea "Vacuna antirrábica" a `12000.00`. Todos los datos SHALL ser ficticios.

#### Scenario: Contenido del seed y relaciones entre las filas

- **WHEN** tras el reinicio se consultan los dueños, sus fichas y las mascotas por id
- **THEN** el `duenio` 1 tiene exactamente 1 fila en `ficha_duenio` y el `duenio` 2 ninguna
- **AND** `mascota` 1 se llama "Toby", tiene `especie = 'perro'` y `duenio_id = 1`
- **AND** `practica` 1 se llama "Consulta" con precio `15000.00` y `practica` 3 se llama "Vacuna antirrábica" con precio `12000.00`
- **AND** `turno` 1 pertenece a una mascota existente y tiene exactamente 2 filas en `turno_practica`, con prácticas distintas

### Requirement: Importes copiados y total calculado con precisión decimal

Cada fila de `turno_practica` del seed SHALL copiar el `precio` vigente del catálogo a `precio_unitario`, y `turno.total` SHALL ser la suma de esos `precio_unitario`. Los importes SHALL ser decimales exactos, calculados con `Decimal` y nunca con punto flotante.

#### Scenario: Precios congelados y total del turno 1

- **WHEN** se inspecciona el `turno` 1 y sus filas de `turno_practica` después del reinicio
- **THEN** la fila de la práctica 1 tiene `precio_unitario = 15000.00` y la de la práctica 3 tiene `precio_unitario = 12000.00`
- **AND** `turno.total = 27000.00`
- **AND** `practica.precio`, `turno_practica.precio_unitario` y `turno.total` son de tipo `numeric` con escala 2, ninguna de ellas `double precision` ni `real`

### Requirement: El próximo turno recibe id 2

Después del reinicio, la secuencia de `turno.id` SHALL quedar posicionada de modo que el primer turno creado después del seed —por la API o por SQL— reciba `id = 2`, tal como muestra el ejemplo de alta de turno del enunciado.

#### Scenario: Alta posterior al seed obtiene el id 2

- **WHEN** tras el reinicio se consultan `last_value` e `is_called` de la secuencia de `turno.id` mediante una consulta de solo lectura (sin ejecutar `nextval`, porque los avances de secuencia no son transaccionales y el valor consumido no se recupera con un `ROLLBACK`)
- **THEN** la secuencia reporta `last_value = 1` e `is_called = true`, de modo que el próximo valor que entregue es `2`
- **AND** el turno existente en la base es el `1`, de modo que el alta siguiente ocupa el `2` sin colisión de clave primaria

### Requirement: Reconstrucción idempotente

Ejecutar el reinicio SHALL ser idempotente por reconstrucción: una segunda ejecución inmediata SHALL dejar el mismo estado que la primera, con los mismos identificadores, sin filas duplicadas y sin errores de clave primaria ni de unicidad, cualquiera sea el contenido previo de la base.

#### Scenario: Dos ejecuciones seguidas dejan el mismo estado

- **WHEN** se ejecuta `python reiniciar.py` dos veces seguidas sobre la misma base
- **THEN** ambas ejecuciones terminan con código de salida `0`
- **AND** los conteos de las seis tablas son idénticos a los de la primera corrida
- **AND** `mascota` 1 sigue siendo "Toby" del dueño 1 y el siguiente `turno.id` sigue siendo `2`

### Requirement: Fallo explícito, atómico y sin dejar la base a medio poblar

Si `DATABASE_URL` no está definida o la base no responde, el reinicio SHALL abortar sin dejar el esquema ni los datos a medio poblar: el resultado SHALL ser el estado previo, intacto. SHALL informar la causa con un mensaje legible en español, sin exponer credenciales, y terminar con un código de salida distinto de `0`.

#### Scenario: DATABASE_URL ausente

- **WHEN** se ejecuta `python reiniciar.py` sin `DATABASE_URL` en el entorno ni en el `.env`
- **THEN** el proceso termina con código de salida `1`
- **AND** imprime un mensaje que nombra `DATABASE_URL` y la acción de copiar `env.example` a `.env`
- **AND** la base no se toca: los conteos de las tablas previas siguen iguales

#### Scenario: Base de datos inalcanzable

- **WHEN** `DATABASE_URL` está definida pero apunta a una base que no acepta la conexión
- **THEN** el proceso termina con código de salida distinto de `0` (`2` para errores de conexión o de ejecución)
- **AND** el mensaje indica que no se pudo conectar o ejecutar, con el tipo de error y sin la contraseña de la URL
- **AND** no se muestra un traceback crudo como única salida, ni queda el esquema borrado o el seed incompleto: ante cualquier fallo se revierte todo

### Requirement: Funciona sobre una base recién creada

El reinicio SHALL funcionar sobre una base recién creada (`DROP DATABASE` + `CREATE DATABASE`) sin pasos manuales previos: no requiere que nadie cree las tablas ni cargue datos antes de ejecutarlo.

#### Scenario: Base nueva creada desde cero

- **WHEN** se crea una base vacía con `DROP DATABASE` + `CREATE DATABASE`, se apunta `DATABASE_URL` a ella y se ejecuta `python reiniciar.py`
- **THEN** el proceso termina con código de salida `0`
- **AND** las seis tablas quedan creadas y los conteos coinciden con los del escenario de base vacía
