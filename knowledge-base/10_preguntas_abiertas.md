# Preguntas Abiertas

> **Actualización 31/10/2026**: las preguntas de prioridad Alta y Media quedaron **resueltas por el equipo** (decisiones propias DD-08 a DD-15 en `09_decisiones_y_supuestos.md`). Ya no bloquean el primer change. Siguen siendo decisiones del equipo, no confirmadas por la cátedra.

> **Criterio de este archivo**: la consigna es la única fuente de verdad. Todo lo que no está escrito en ella **no se inventa**: queda acá. Cada pregunta indica si bloquea la entrega o solo una decisión de implementación.

## Inconsistencias detectadas

### IN-01 — `duenios` está en la tabla de endpoints pero sin listado
**Documento dice**: existen `POST`, `GET /{id}`, `PATCH`, `DELETE` para dueños, y `GET /duenios/{id}/mascotas`.
**Qué falta**: no hay `GET /duenios/` (listado).
**Impacto**: ninguno sobre la corrección si no se implementa; sí si el equipo asume que "CRUD" implica listado.
**Resolución propuesta**: no implementar endpoints no listados.

### IN-02 — No hay endpoints de baja para mascotas, prácticas ni fichas
**Documento dice**: solo `DELETE /duenios/{id}` y `DELETE /turnos/{id}`.
**Qué falta**: `DELETE /mascotas/{id}`, `DELETE /practicas/{id}`, `DELETE` de ficha.
**Impacto**: el catálogo y las mascotas no se pueden limpiar por API; solo vía `reiniciar.py` o SQL.
**Resolución propuesta**: no implementarlos; `reiniciar.py` cubre el reseteo.

### IN-03 — Regla de borrado de `ficha_duenio.duenio_id` no está especificada
**Documento dice**: la tabla lista `duenio_id UNIQUE` para `ficha_duenio`, sin `ON DELETE`.
**Qué falta**: qué pasa al borrar un dueño que tiene ficha.
**Impacto**: con el comportamiento por defecto (`NO ACTION`) el borrado también falla; el 409 de RN-08 se dispararía igual pero por otra restricción.
**Resolución**: DD-13 — se deja el default de PostgreSQL. **No** agregar `CASCADE` sin autorización.

### IN-04 — Formato del cuerpo de `GET /health/ready`
**Documento dice**: "Estado de la base", códigos 200 y 503.
**Qué falta**: el JSON exacto de la respuesta.
**Impacto**: un `.http` con una aserción de forma podría no coincidir con la corrección.
**Resolución**: DD-14 — `{"estado": "listo", "base": "ok"}`; documentarlo en el README como decisión propia.

### IN-05 — `POST /mascotas/` declara 409 en la tabla de endpoints
**Documento dice**: códigos `201, 409, 422` para el alta de mascota.
**Qué falta**: qué conflicto produce 409 además del dueño inexistente (que C-04 confirma).
**Impacto**: bajo; el único caso identificable es la FK a un dueño que no existe.
**Resolución propuesta**: 409 únicamente por violación de FK.

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|---|---|---|---|
| Resuelta (DD-08) | ¿Qué campos acepta exactamente `DuenioUpdate`? La consigna solo dice "aplica sólo los campos enviados, con `exclude_unset`". ¿Incluye `email`? ¿Es un PATCH con todos los campos opcionales? | Implementación de `duenios` | Cátedra |
| Resuelta (DD-09) | ¿El email distingue mayúsculas/minúsculas? PostgreSQL `UNIQUE` es case-sensitive por defecto; `A@x.com` y `a@x.com` serían distintos. ¿Se normaliza a minúsculas? | RN-01 y casos C-02 | Cátedra |
| Resuelta (DD-10) | `GET /duenios/{id}/mascotas`: ¿devuelve una lista simple o el envoltorio paginado de RN-13? La consigna solo lo exige para `GET /mascotas/`. | Implementación de `duenios` | Cátedra |
| Resuelta (DD-11) | ¿La respuesta del detalle de turno incluye el `id` de cada fila `turno_practica` o solo `practica_id`, `nombre` y `precio_unitario` como en el ejemplo? | Contrato de `turnos` | Cátedra |
| Resuelta (DD-08) | ¿`DuenioUpdate` con email repetido responde 409? La tabla de códigos del PATCH lo incluye, pero no está enunciado como regla. | Precisa el `service` | Cátedra |
| Resuelta (DD-12) | ¿`mascota.especie` es texto libre o un conjunto cerrado de valores (perro, gato, …)? | Validación del DTO | Cátedra |
| Resuelta (DD-12) | ¿`fecha` de turno se valida contra el pasado o contra duplicados (misma mascota, mismo horario)? No hay regla que lo diga. | Implementación de `turnos` | Cátedra |
| Resuelta (DD-12) | ¿`FichaCreate` exige `telefono` y `direccion`, o alguno es opcional? La tabla no marca nulabilidad. | Validación del DTO | Cátedra |
| Resuelta (DD-12) | ¿`motivo` es obligatorio? La tabla no lo dice y el ejemplo siempre lo trae. | Validación del DTO | Cátedra |
| Resuelta (DD-13) | ¿Qué `ON DELETE` corresponde a `turno_practica.practica_id`? La tabla no lo especifica. Si se borrara una práctica usada, ¿debería fallar? | Integridad del catálogo | Cátedra |
| Resuelta (DD-15) | ¿`page`/`size` viajan como query params (`?page=&size=`) o como path params? La tabla los muestra en la columna "Cuerpo". | Contrato de `mascotas` | Cátedra |
| Resuelta (DD-15) | ¿Orden por defecto de `GET /practicas/` y de los listados? No está especificado. | Presentación | Equipo |
| Resuelta (DD-15) | ¿La biblioteca `app/modules/laboratorio/cliente.py` debe crearse con el código exacto del enunciado, o la cátedra la provee en el repo de entrega? | Puesta en marcha | Cátedra |
| Resuelta (DD-15) | ¿Se espera un archivo `.http` por caso (C-01…C-09) o un único archivo con todos? "Archivos `.http`" está en plural. | Organización de `test/` | Equipo |
| Resuelta (DD-15) | Nombre de la base y usuario por defecto para `env.example`. No está especificado. | Puesta en marcha | Equipo |

## Campos de discovery inferidos con baja confianza

- `[DISCOVERY]` `scale`: no está explícito en el enunciado. Se infirió `single_user` (proyecto académico de una veterinaria de barrio, sin auth, sin multi-tenant). Confirmar si la cátedra espera otra cosa.
- `[DISCOVERY]` `needs_infra`: se infirió `true` porque requiere PostgreSQL 16 y un archivo `.env`. No hay contenedores ni colas en el alcance.
