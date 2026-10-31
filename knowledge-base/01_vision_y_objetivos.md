# 01_vision_y_objetivos.md

## Propósito

Una veterinaria de barrio necesita una **API** para registrar a sus clientes (dueños), sus mascotas y los turnos de atención. El trabajo es un **trabajo práctico breve** de Programación III (Unidades 1 a 4) que integra FastAPI, SQLModel y PostgreSQL en un solo servicio.

## Objetivos (los que evalúa la consigna)

1. **API asincrónica** con parámetros tipados, `Depends()` y el motor creado en el ciclo de vida.
2. **Contratos y CRUD**: modelos de tabla separados de los DTO de entrada/salida, con los códigos HTTP correctos.
3. **Modelo relacional**: traducir al esquema un uno a uno, una agregación, una asociación, una composición y un muchos a muchos con datos propios, **justificando de qué lado va cada clave foránea**.
4. **Lecturas sin N+1**: carga anticipada, número fijo de consultas, sin carga perezosa.
5. **Garantías en la base**: FK, unicidad y CHECK; el servicio traduce el rechazo a 409.
6. **Asincronía sin bloqueos**: la biblioteca sincrónica del laboratorio se usa sin frenar el servidor.

## Negocio

- Cada dueño puede cargar **una ficha** (teléfono y dirección).
- Cada mascota figura a nombre de un dueño.
- Cada turno es de una mascota y se reserva con **prácticas** (consulta, vacuna, desparasitación...).
- Hay un **catálogo de prácticas con precio**. Al reservar, el **precio se congela en el turno**: si el catálogo cambia, los turnos ya reservados no cambian.

## Alcance

- **Incluye**: dueños y ficha, mascotas con listado paginado, catálogo de prácticas, turnos con sus prácticas (alta transaccional, detalle, baja), consulta de stock al laboratorio, health, `reiniciar.py`, casos `.http`, README.
- **No se evalúa ni se implementa**: autenticación/autorización, repositorios ni Unit of Work, colas de tareas, migraciones con Alembic, frontend, Docker, CI, pagos, facturación, historial médico, notificaciones.

## Criterio de éxito

Puntaje de la consigna (100 %): Proyecto y ciclo de vida 10 · Contratos y CRUD 20 · **Modelos, restricciones y relaciones 30** · Altas con relaciones 15 · Lecturas sin N+1 15 · Asincronía sin bloqueos 10.

No se corrige hasta subsanar un proyecto que: no levanta, no crea su esquema con `python reiniciar.py` sobre una base vacía, o tiene credenciales reales en el repositorio.
