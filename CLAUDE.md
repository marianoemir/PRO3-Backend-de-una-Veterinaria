# PRO3 — Backend de una Veterinaria — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

| Capa | Tecnología | Versión Mínima |
|------|------------|---------------|
| Backend | Python | 3.12+ |
| Framework Web | FastAPI | 0.111+ |
| ORM | SQLModel + SQLAlchemy | 0.0.24+ / 2.0+ |
| Driver BD | asyncpg | 0.30+ |
| Base de Datos | PostgreSQL | 16 |
| Entorno | .env + python-dotenv | 1.0+ |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack, arquitectura, tabla de endpoints |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Actores (sin auth — fuera de alcance) |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | ⚠️ ERD, las 6 tablas, restricciones, índices, seed |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | ⚠️ RN-01 a RN-24 — leer antes de codear cualquier módulo |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | 19 historias de usuario con criterios de aceptación |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E: altas con conflicto, turnos, N+1, laboratorio |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Estructura de directorios, capas, variables de entorno |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | DD-01 a DD-07, SU-01 a SU-05 |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias a resolver ANTES de codear |

> Las preguntas abiertas de prioridad Alta y Media ya fueron **resueltas por el equipo** (DD-08 a DD-15 en `09_decisiones_y_supuestos.md`). Son decisiones propias, no reglas de la cátedra: justificarlas en el `design.md` del change y mencionarlas en el README.

---

## Skills Disponibles

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Mariano — Núcleo, modelos y turnos** | FastAPI / SQLModel / ciclo de vida / transacciones | — |
| **Facundo — Dueños, mascotas y README** | CRUD / paginación / DTO | — |
| **Andrés — Prácticas, laboratorio y pruebas** | async / asyncio / tests HTTP | — |
| **Orquestación** | OPSX / fundación / documentación | `kb-creator`, `roadmap-generator`, `agents-md-generator`, `skill-registry` |

Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan completo está en [CHANGES.md](CHANGES.md) y el reparto, orden y comandos en [docs/DIVISION-DEL-EQUIPO.md](docs/DIVISION-DEL-EQUIPO.md). Resumen (revisión 2, 31/10/2026):

- **Total**: 11 changes, un solo dueño cada uno. Equipo: Mariano, Facundo y Andrés.
- **Camino crítico**: `fundacion-proyecto → modelos-y-esquema → reiniciar-y-seed → turnos-alta-transaccional → turnos-lecturas-y-baja → pruebas-http-y-evidencia → readme-y-entrega`.
- **Primer change**: `fundacion-proyecto`.

| # | Change | Dueño | Depende de |
|---|---|---|---|
| 01 | `fundacion-proyecto` | Mariano | — |
| 02 | `modelos-y-esquema` | Mariano | 01 |
| 03 | `duenios-y-ficha` | Facundo | 02 |
| 04 | `practicas-catalogo` | Andrés | 02 |
| 05 | `mascotas-y-paginacion` | Facundo | 03 |
| 06 | `turnos-alta-transaccional` | Mariano | 02, 09 |
| 07 | `turnos-lecturas-y-baja` | Mariano | 06 |
| 08 | `laboratorio-sin-bloqueo` | Andrés | 01 |
| 09 | `reiniciar-y-seed` | Mariano | 02 |
| 10 | `pruebas-http-y-evidencia` | Andrés | 03 a 09 |
| 11 | `readme-y-entrega` | Facundo | 10 |

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), verificá que las dependencias del change estén archivadas y mergeadas, y leé los archivos de "Leer antes". Tocá **solo** los archivos del change. Los DTO viven en el `schemas.py` de cada módulo y ningún módulo importa DTO de otro.

---

## Reglas Duras

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram, diseño visual): el proyecto las **hereda**, no se repiten acá. Acá viven solo las reglas **específicas de este proyecto** + las universales que el global no cubra.

### Reglas universales que el global NO cubre (aplica siempre)

- **NUNCA commitees ni pushees sin pedido explícito del usuario.** Esperá a que diga "commit" o "push". No asumas que querés que lo haga.
- **NUNCA corras `git commit` o `git push` autónomamente.** Preguntá primero. El usuario commitea una fase por vez.

### Reglas específicas del proyecto (contrato — romperlas es un defecto)

1. **NUNCA cambiar el stack ni las versiones mínimas** → Stack fijo: Python 3.12, FastAPI 0.111+, SQLModel 0.0.24+, asyncpg 0.30+, PostgreSQL 16. Sin migrar a otra base, ORM o framework.

2. **NUNCA usar `float` para dinero** → Todo monto monetario con `Decimal` de Python, serializado como string en JSON. Aplica a `precio` en prácticas, `total` en turnos, `precio_unitario` en turno_práctica.

3. **NUNCA preguntar "¿ya existe?" antes de escribir** → Las garantías van en la base (FK, UNIQUE, CHECK). Escribir, capturar `IntegrityError`, hacer `rollback()`, responder 409 con mensaje propio. Sin consultas `SELECT` previas para "ver si existe".

4. **NUNCA handlers con llamadas bloqueantes** → Todos los handlers `async def`. Para la biblioteca del laboratorio (`consultar_stock` con `time.sleep`), usar `await asyncio.to_thread()`. **NUNCA modificar `app/modules/laboratorio/cliente.py`** — es código exacto de la cátedra.

5. **NUNCA carga perezosa (lazy loading)** → Siempre precarga explícita en la misma consulta: `joinedload` para relaciones `to-one`, `selectinload` + `joinedload` anidado para colecciones. Una consulta base, número fijo de queries, sin N+1.

6. **NUNCA Alembic, auth, repositorios ni colas** → El esquema se crea con `SQLModel.metadata.create_all`/`drop_all` desde `reiniciar.py`. Sin migraciones, sin JWT, sin capa de repositorio, sin RabbitMQ/SQS.

7. **NUNCA versionar `.env` ni credenciales reales** → `.env` en `.gitignore`. Solo `env.example` con valores de ejemplo va al repo.

8. **snake_case en todo** → Archivos, funciones, variables, endpoints. `PascalCase` solo para modelos SQLModel/SQLAlchemy y DTOs Pydantic. Type hints obligatorios en todas las funciones.

9. **`async def` en todos los handlers** → Todos los endpoints, services y dependencias son `async def`. Sin excepciones.

10. **NUNCA crear endpoints no listados en la consigna** → No implementar `GET /duenios/`, `DELETE /mascotas/{id}`, `DELETE /practicas/{id}` ni ningún otro que no esté en la tabla de endpoints de `02_descripcion_general.md`.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)               → entender el dominio
2. Identificar el change en CHANGES.md                   → respetar dependencias
3. /opsx:propose <nombre-del-change>                             → proposal + design + specs + tasks
4. Implementar las tasks cargando skills                  → respetando las reglas duras
5. /opsx:archive <nombre-del-change> + marcar [x] en CHANGES.md  → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.