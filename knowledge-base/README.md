# Veterinaria — Base de Conocimiento

Base de conocimiento generada a partir de `docs/MiniTP_Cap1a4_Consigna.pdf` (consigna del TP de Programación III, unidades 1 a 4).

**Modo de generación**: ingest (documento fuente en `docs/`).

## Índice de Archivos

| Archivo | Contenido |
|---|---|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance, fuera de alcance, métricas de éxito |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack con versiones mínimas, arquitectura general, integraciones, tabla de endpoints |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, ausencia de RBAC (fuera de alcance), rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | ERD, las 6 tablas con columnas y restricciones, índices, justificación de cada FK, seed |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-01 a RN-24 con su garante esperado y el principio de "no preguntar antes de escribir" |
| [06_funcionalidades.md](06_funcionalidades.md) | 19 historias de usuario en 7 épicas con criterios de aceptación |
| [07_flujos_principales.md](07_flujos_principales.md) | Arranque, altas con conflicto, reserva de turno, lectura sin N+1, bajas, laboratorio, reinicio |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, estructura de directorios, capas, seguridad, variables de entorno |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-01 a DD-07 y SU-01 a SU-05 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias IN-01 a IN-05 y preguntas priorizadas |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md) **(leer antes de tocar cualquier modelo)**
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

API asincrónica en FastAPI + SQLModel + PostgreSQL 16 para registrar dueños, mascotas, prácticas y turnos de una veterinaria de barrio. El corazón del TP son las cinco relaciones del capítulo 4 (uno a uno, agregación, asociación, composición y muchos a muchos con datos) y la disciplina de delegar en la base las garantías de integridad, leer con carga anticipada y no bloquear el event loop. Entrega: esta semana, 3 personas en paralelo.
