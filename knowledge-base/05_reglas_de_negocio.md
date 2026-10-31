# Reglas de Negocio

**Fuente normativa**: consigna, § "Reglas de negocio". Los códigos `RN-01` a `RN-09` son los de la cátedra y **no deben renumerarse**. Solo se documentan reglas presentes en el enunciado; cualquier vacío está en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

## Principio transversal: garantizar en la base, no preguntar antes

> Ninguna de estas reglas se verifica con una consulta previa del tipo "¿ya existe?". Se escribe, y si la base rechaza la escritura, el `service` atrapa el `IntegrityError`, **deshace la transacción** y responde **409 con un mensaje propio**.

Razón (consigna, sección 4.10): entre la pregunta y la escritura hay una ventana en la que otra petición puede escribir lo mismo; la única defensa real es que la base rechace la segunda.

## Dominio: Dueños (RN-DU)

| Código | Regla | Garante esperado |
|---|---|---|
| RN-01 | El email de un dueño es único. | `UNIQUE` en la base; 409 |
| RN-03 | Un dueño tiene como máximo una ficha. | `UNIQUE` en `ficha_duenio.duenio_id`; 409 |
| RN-08 | No se puede borrar un dueño que tenga mascotas a su nombre. | `ON DELETE RESTRICT`; 409 |

## Dominio: Prácticas (RN-PR)

| Código | Regla | Garante esperado |
|---|---|---|
| RN-02 | El nombre de una práctica es único. | `UNIQUE` en la base; 409 |
| RN-04 | El precio de una práctica es mayor que cero. | `CHECK` en la base **y** validación del DTO |

## Dominio: Turnos (RN-TU)

| Código | Regla | Garante esperado |
|---|---|---|
| RN-05 | Un turno se reserva con sus prácticas: viajan dentro del cuerpo del alta del turno, y tiene **al menos una**. | DTO anidado; **422** si la lista está vacía |
| RN-06 | El precio de cada práctica se copia del catálogo al reservar el turno, y el total lo calcula el servidor. Ni el precio ni el total viajan en el DTO. | Cálculo en el `service` |
| RN-07 | Una misma práctica no aparece dos veces en un turno. | Clave primaria compuesta de `turno_practica`; 409 |
| RN-09 | Al borrar un turno se borran sus prácticas. | `ON DELETE CASCADE` en la base |

## Dominio: Contratos y HTTP (RN-HT)

| Código | Regla | Garante esperado |
|---|---|---|
| RN-10 | Los DTO están separados de los modelos de tabla y los de alta **no llevan `id`**. | `schemas.py` por módulo |
| RN-11 | El PATCH del dueño aplica **sólo** los campos enviados, con `exclude_unset`. | `service` / router |
| RN-12 | Códigos de respuesta: **201** al crear, **204** al borrar, **404** si el recurso no existe, **409** si la base rechaza la escritura, **422** si el cuerpo o los parámetros no cumplen el contrato. | Routers + manejo de `IntegrityError` |
| RN-13 | `GET /mascotas/` devuelve el envoltorio `{ items, total, page, size, pages }`; `size` vale 20 por defecto y va de 1 a 100; una página más allá de `pages` responde 422; la primera página siempre responde aunque no haya resultados. | Router + service |

## Dominio: Lecturas (RN-LE)

| Código | Regla | Garante esperado |
|---|---|---|
| RN-14 | Toda respuesta que incluya datos de una relación los obtiene con **carga anticipada declarada en la misma consulta**: `joinedload` para relaciones «a uno» y `selectinload` para colecciones. | Consultas del `service` |
| RN-15 | El detalle de un turno (mascota + prácticas) y el de un dueño (con su ficha) se resuelven con un **número fijo de consultas**, que no crece con la cantidad de hijos. | Consultas del `service` |
| RN-16 | Ninguna lectura puede depender de la carga perezosa: en contexto asincrónico falla con `MissingGreenlet`. | Prohibido `lazy="select"` implícito en lecturas |

## Dominio: Asincronía (RN-AS)

| Código | Regla | Garante esperado |
|---|---|---|
| RN-17 | Todos los handlers son `async def`. | `router.py` de cada módulo |
| RN-18 | Ningún handler ejecuta una llamada bloqueante; la biblioteca sincrónica del laboratorio se invoca **fuera** del bucle de eventos. | `GET /laboratorio/stock/{vacuna}` |
| RN-19 | Mientras hay consultas al laboratorio en curso, `GET /health/live` responde de inmediato. | Verificación C-09 |

## Dominio: Ciclo de vida (RN-CV)

| Código | Regla | Garante esperado |
|---|---|---|
| RN-20 | El motor asincrónico y la fábrica de sesiones se crean en el `lifespan`, se guardan en `app.state` y el motor se cierra al apagar. | `app/main.py` |
| RN-21 | Cada petición recibe su propia sesión vía `Depends(get_session)`, creada con `expire_on_commit=False`. | `app/core/database.py` |
| RN-22 | `GET /health/live` **no** toca la base; `GET /health/ready` ejecuta `SELECT 1` y responde **503** si la base no contesta. | módulo `health` |
| RN-23 | El alta de un turno con una práctica inexistente no guarda **nada**: ni el turno ni ninguna de sus prácticas (todo o nada, una sola transacción). | `service` de turnos |
| RN-24 | `DATABASE_URL` se lee del entorno (`.env` no versionado); el repo incluye `env.example` sin secretos. | `app/core/config.py` |
