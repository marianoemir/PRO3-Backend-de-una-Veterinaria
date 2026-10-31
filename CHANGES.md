# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **PRO3 — Backend de una Veterinaria**.
> Cada change es atómico: una persona puede implementarlo en media jornada o una jornada (~2-5 h).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

**Fuente de verdad**: `docs/MiniTP_Cap1a4_Consigna.pdf` + `knowledge-base/`.
**Equipo**: 3 personas en paralelo, entrega en ~4-5 días efectivos.
**Alcance**: solo backend. Sin frontend, sin CI/CD, sin Docker, sin devops.

> **Nomenclatura**: `C-NN` en este archivo identifica un **change del roadmap**.
> Los **casos de prueba de la cátedra** también se numeran C-01…C-09. Cuando se hable de
> ellos se dirá **"caso C-0X (cátedra)"** y los archivos serán `test/caso_C-0X.http`
> (más `test/caso_C-08.sql`).

---

## Cómo usar este documento

1. Elegir un change cuyo **dueño** sea tu persona (ver "Reparto por persona") y verificar que
   todas sus **Dependencias** estén archivadas en `openspec/changes/archive/`.
2. Leer los archivos de la knowledge-base indicados en **Leer antes** (con la sección exacta).
3. Ejecutar `/opsx:propose <nombre-del-change>` y completar proposal, specs, design y tasks
   **en español**, sin agregar alcance que no esté en la consigna.
4. Implementar, correr el smoke test del change (y los `.http` que existan) y archivarlo con
   `/opsx:archive <nombre-del-change>`.
5. Marcar el checkbox `[x]` de este archivo y avisar en el canal del equipo qué change quedó
   libre, para que la siguiente ola arranque sin esperar.

### Reglas de trabajo del equipo

- **Nada de dominio antes de C-01**: el esqueleto, `config.py`, `database.py`, el `lifespan` y
  `health` son prerequisito de todo lo demás.
- **Modelos antes que CRUD**: ningún service/router de un módulo se propone antes de que su
  change de modelos esté archivado.
- **Un change, un dueño, un archivo**: los archivos compartidos (`app/main.py`,
  `requirements.txt`, `env.example`, `reiniciar.py`, `README.md`, `test/`) tienen dueño único.
  Si necesitás un cambio ahí, lo pedís; no lo editás en paralelo.
- **No inventar reglas de negocio**: lo que la consigna no dice vive en
  `knowledge-base/10_preguntas_abiertas.md`. El change puede tomar una decisión de
  implementación y documentarla, pero **no** se presenta como regla de la cátedra ni se
  agregan validaciones no enunciadas.
- **No crear endpoints no listados** (por ejemplo `GET /duenios/` o `DELETE /mascotas/{id}`):
  ver IN-01 e IN-02.
- **Si un change crece más de una jornada, se parte** antes de empezar, no a mitad de camino.
- **Los tests no parchean código**: si un caso falla, se reporta al dueño del módulo y se
  corrige en el change de ese módulo.

### Definición de terminado (por change)

- Dependencias archivadas y `openspec/changes/<change>/` completo en español.
- La app levanta con `uvicorn app.main:app` y el contrato del change responde lo esperado.
- Smoke test propio ejecutado (y `.http` de `test/` si el change toca endpoints ya cubiertos).
- Sin credenciales reales ni `.env` versionado.
- Change archivado, checkbox marcado y aviso al equipo.

### Supuestos de esfuerzo

- **1 jornada ≈ 6 h netas** de trabajo efectivo; los changes se dimensionaron en **2-5 h**.
- Total estimado: **67 h** → **~22 h por persona**, con **5-10 h de colchón** por persona para
  integración, depuración y ensayo de la entrega.
- La estimación incluye leer la KB y escribir los artefactos de OpenSpec, no solo el código.
- No incluye el tiempo de instalar PostgreSQL ni de crear el entorno virtual la primera vez.

---

## Árbol de dependencias

```
C-01 esqueleto-y-configuracion                          [A]  ← raíz
│
├── C-02 motor-sesion-y-lifespan                        [A]  ← CRÍTICO
│   ├── C-03 health-live-ready                          [A]
│   └── C-15 laboratorio-stock-asincrono                [C]
│
├── C-04 modelos-duenios-y-ficha                       [B]  ← CRÍTICO
│   ├── C-05 modelos-mascotas                           [B]  ← CRÍTICO
│   │   ├── C-07 modelos-turnos-y-turno-practica        [A]  ← CRÍTICO (además ← C-06)
│   │   └── C-10 crud-mascotas → C-11 listado-paginado  [B]
│   └── C-08 crud-duenios → C-09 ficha-y-mascotas       [B]
│
└── C-06 modelos-practicas                             [C]  ← CRÍTICO
    ├── C-07 modelos-turnos-y-turno-practica            [A]
    └── C-12 crud-practicas                             [C]

C-07 + C-10 + C-12 ──▶ C-13 alta-turnos-con-practicas   [A]  ← CRÍTICO
C-13 ───────────────▶ C-14 detalle-y-baja-turno         [A]  ← CRÍTICO
C-02 + C-04 + C-05 + C-06 + C-07 ──▶ C-16 script-reiniciar-seed          [C]
C-08 + C-09 + C-10 + C-12 + C-13 + C-14 + C-16 ──▶ C-17 tests 01-05      [C]  ← CRÍTICO
C-13 + C-14 + C-15 + C-16 + C-17 ──▶ C-18 tests 06-09 + evidencia        [C]  ← CRÍTICO
C-17 + C-18 ────────▶ C-19 readme-y-checklist-entrega                    [B]  ← CRÍTICO
```

### Dependencias que no son obvias

- **C-08, C-10, C-11, C-12, C-13, C-14 y C-16 dependen además de C-02** (motor, fábrica de
  sesiones y `get_session`). En el árbol se omiten esas aristas para no tapar la cadena de
  modelos; están repetidas en el campo **Dependencias** de cada change.
- **C-04 y C-06 solo necesitan C-01**, no C-02: son declaraciones de modelos y DTO. La
  verificación contra PostgreSQL (`create_all`, `\d`, inserts) se hace en cuanto C-02 esté
  disponible, el mismo día.
- **C-07 toca dos archivos ajenos**: agrega las relaciones inversas `Mascota.turnos`
  (archivo de B) y `Practica.turnos` (archivo de C). Persona A entrega el fragmento exacto y
  B/C lo aplican al inicio del Paso 4, antes de que A cierre C-07. Son dos líneas por archivo.
- **C-13 no puede empezar hasta que C-10 y C-12 estén cerrados**: necesita una mascota y un
  catálogo de prácticas creados por API para probar el alta.
- **C-16 (reiniciar.py) espera a los cuatro changes de modelos** (C-04 a C-07). Es el único
  change que importa los seis módulos para `create_all`.

---

## Paralelismo por fase (GATES)

> Cada GATE es un punto de sincronización. Lo que está debajo de un gate puede ejecutarse en
> paralelo. `[Persona]` marca al dueño sugerido.

```
GATE 0: nada todavía
  → C-01 esqueleto-y-configuracion                  [A]
     (B y C: /opsx:propose de C-04 y C-06 + lectura de KB, sin tocar código)

GATE 1: C-01 ✓                                     ← PRIMER FORK (3 ramas)
  → C-02 motor-sesion-y-lifespan                    [A]
  → C-04 modelos-duenios-y-ficha                    [B]
  → C-06 modelos-practicas                          [C]

GATE 2: C-02 ✓
  → C-03 health-live-ready                          [A]
  → C-05 modelos-mascotas                           [B — si C-04 ✓]
  → C-12 crud-practicas                             [C — si C-06 ✓]
  → C-15 laboratorio-stock-asincrono                [C — después de C-12, no a la vez]

GATE 3: C-05 ✓ + C-06 ✓                            ← FORK (3 ramas + cola)
  → C-07 modelos-turnos-y-turno-practica            [A]
  → C-08 crud-duenios                               [B — si C-02 ✓]
  → C-10 crud-mascotas                              [B — después de C-08, no a la vez]
  → C-15 (si quedó pendiente)                       [C]

GATE 4: C-07 ✓                                     ← FORK (cierre de modelos)
  → C-13 alta-turnos-con-practicas                  [A — si C-10 ✓ y C-12 ✓]
  → C-16 script-reiniciar-seed                      [C — todos los modelos ✓]
  → C-09 ficha-y-mascotas-por-duenio                [B — si C-08 ✓]
  → C-11 listado-paginado-mascotas                  [B — después de C-10, no a la vez]

GATE 5: C-13 ✓
  → C-14 detalle-y-baja-turno                       [A]
  → C-17 redacción de casos 01-05                   [C]

GATE 6: C-14 ✓ + C-16 ✓
  → C-17 ejecución y cierre de casos 01-05          [C]
  → C-18 redacción de casos 06-09 + SQL             [C — después de C-17]

GATE 7: C-17 ✓                                     ← FORK de cierre
  → C-18 cierre + evidencia C-07                    [C]
  → C-19 borrador del README                        [B]

GATE 8: C-18 ✓
  → C-19 README final + checklist de entrega        [B]

GATE 9: C-19 ✓  →  ENTREGA
```

### Olas de paralelismo (qué puede arrancar a la vez)

| Ola | Entra cuando | Pueden correr en paralelo | Personas |
|---|---|---|---|
| 0 | — | `C-01` (solo) | A; B y C hacen propose + lectura |
| 1 | `C-01` ✓ | `C-02`, `C-04`, `C-06` | A, B, C |
| 2 | `C-02` ✓ | `C-03`, `C-05`, `C-12`; `C-15` después de `C-12` | A, B, C |
| 3 | `C-05` + `C-06` ✓ | `C-07`, `C-08`; `C-10` después de `C-08` | A, B, C |
| 4 | `C-07` ✓ (y `C-10`/`C-12` ✓) | `C-13`, `C-09`, `C-11`, `C-16` | A, B, C |
| 5 | `C-13` ✓ | `C-14`, `C-17` (redacción) | A, C |
| 6 | `C-14` + `C-16` ✓ | `C-17` (ejecución); `C-18` (redacción) al cerrar `C-17` | C |
| 7 | `C-17` ✓ | `C-18` (cierre), `C-19` (borrador) | C, B |
| 8 | `C-18` ✓ | `C-19` (final) + revisión integral | B, A, C |

### Camino crítico (9 changes — mínimo irreducible)

```
C-01 → C-04 → C-05 → C-07 → C-13 → C-14 → C-17 → C-18 → C-19
```

- **~37 h de trabajo encadenado.** Es la cadena que decide si se llega: cualquier demora en
  `C-04`, `C-05`, `C-07`, `C-13` o `C-14` corre la entrega.
- **Laterales que no alargan la cadena pero son obligatorios**: `C-02` (prerequisito de los
  CRUD), `C-06` (prerequisito de C-07), `C-10` y `C-12` (prerequisitos de C-13), `C-16`
  (prerequisito de C-17). Todos se cierran antes del nodo que los necesita.
- `C-03`, `C-08`, `C-09`, `C-11`, `C-15` son obligatorios para el puntaje, pero tienen holgura
  respecto de la cadena principal.

### Plan óptimo con 3 personas

> Pasos de media jornada (~3-4 h). Las flechas de dependencia se respetan; el colchón queda al
> final para integración y correcciones.

| Paso | A — Núcleo + turnos | B — Dueños + mascotas + README | C — Prácticas + laboratorio + test |
|---|---|---|---|
| 1 · día 1 AM | `C-01` esqueleto | — (propose `C-04` + KB) | — (propose `C-06` + KB) |
| 2 · día 1 PM | `C-02` motor y lifespan | `C-04` modelos dueños/ficha | `C-06` modelos prácticas |
| 3 · día 2 AM | `C-03` health | `C-05` modelos mascotas | `C-12` CRUD prácticas |
| 4 · día 2 PM | `C-07` modelos turnos | `C-10` CRUD mascotas | `C-15` laboratorio async |
| 5 · día 3 AM | `C-13` alta de turnos | `C-08` CRUD dueños | `C-16` reiniciar + seed |
| 6 · día 3 PM | `C-14` detalle y baja | `C-09` ficha y mascotas por dueño | `C-17` redacción casos 01-05 |
| 7 · día 4 AM | Revisión N+1 + buffer | `C-11` listado paginado | `C-17` ejecución + arranque `C-18` |
| 8 · día 4 PM | Revisión integral | Borrador del README | `C-18` cierre + evidencia C-07 |
| 9 · día 5 AM | Checklist técnico | `C-19` README final | Revisión de evidencias |
| 10 · día 5 PM | Colchón / correcciones | Colchón / correcciones | Colchón / correcciones |

### Reparto por persona y archivos compartidos

| Persona | Rol | Changes | Horas | Archivos que posee |
|---|---|---|---|---|
| **A** | Núcleo, ciclo de vida y turnos | `C-01`, `C-02`, `C-03`, `C-07`, `C-13`, `C-14` | 22 h | `app/main.py`, `app/core/*`, `app/modules/health/*`, `app/modules/turnos/*`, `requirements.txt`, `env.example`, `.gitignore` |
| **B** | Dueños, mascotas y README | `C-04`, `C-05`, `C-08`, `C-09`, `C-10`, `C-11`, `C-19` | 25 h | `app/modules/duenios/*`, `app/modules/mascotas/*`, `README.md` |
| **C** | Prácticas, laboratorio y entregables | `C-06`, `C-12`, `C-15`, `C-16`, `C-17`, `C-18` | 20 h | `app/modules/practicas/*`, `app/modules/laboratorio/*`, `reiniciar.py`, `test/*` |

**Archivos compartidos — dueño único:**

> Regla de reparto: **cada persona trabaja un change a la vez**. La simultaneidad es entre
> personas, no dentro de una misma persona. Cuando alguien termina antes de lo previsto, toma
> el siguiente change de su lista o ayuda con revisión/evidencia, nunca abre un archivo ajeno.

| Archivo | Dueño | Regla |
|---|---|---|
| `app/main.py` | A | Solo A. `C-01` lo deja con los seis routers ya incluidos (vacíos), así nadie más lo edita. |
| `app/core/config.py` y `app/core/database.py` | A | Solo A. Cambios de `echo`, pool o sesión se piden a A. |
| `requirements.txt` | A | Si un change necesita una dependencia, se la pide a A. No se edita en paralelo. |
| `env.example` / `.gitignore` | A | Solo A. |
| `reiniciar.py` | C | Solo C. |
| `README.md` | B | Solo B. Recibe de C la evidencia del caso C-07. |
| `test/**` | C | Solo C. Casos, `.sql` y evidencias. |
| `app/modules/duenios/models.py` | B | A no lo toca. B agrega `Duenio.mascotas` en `C-05`. |
| `app/modules/mascotas/models.py` | B | A entrega el fragmento de `Mascota.turnos`; B lo aplica al inicio del Paso 4 (`C-07`). |
| `app/modules/practicas/models.py` | C | A entrega el fragmento de `Practica.turnos`; C lo aplica al inicio del Paso 4 (`C-07`). |

> `C-01` crea los stubs vacíos de los seis módulos. Es la única vez que A escribe dentro de
> directorios de B y C; a partir de ese momento cada módulo tiene un solo dueño.

### Tabla resumen de changes

| ID | Change | Fase | Dueño | Effort | Depende de | Governance |
|---|---|---|---|---|---|---|
| C-01 | `esqueleto-y-configuracion` | 0 | A | 3 h | — | BAJO |
| C-02 | `motor-sesion-y-lifespan` | 0 | A | 3 h | C-01 | CRITICO |
| C-03 | `health-live-ready` | 0 | A | 2 h | C-02 | MEDIO |
| C-04 | `modelos-duenios-y-ficha` | 1 | B | 4 h | C-01 | CRITICO |
| C-05 | `modelos-mascotas` | 1 | B | 3 h | C-04 | CRITICO |
| C-06 | `modelos-practicas` | 1 | C | 3 h | C-01 | CRITICO |
| C-07 | `modelos-turnos-y-turno-practica` | 1 | A | 5 h | C-05, C-06 | CRITICO |
| C-08 | `crud-duenios` | 2 | B | 5 h | C-04, C-02 | ALTO |
| C-09 | `ficha-y-mascotas-por-duenio` | 2 | B | 3 h | C-08 | MEDIO |
| C-10 | `crud-mascotas` | 2 | B | 3 h | C-05, C-02 | ALTO |
| C-11 | `listado-paginado-mascotas` | 2 | B | 3 h | C-10 | ALTO |
| C-12 | `crud-practicas` | 2 | C | 2 h | C-06, C-02 | MEDIO |
| C-13 | `alta-turnos-con-practicas` | 3 | A | 5 h | C-07, C-10, C-12, C-02 | CRITICO |
| C-14 | `detalle-y-baja-turno` | 3 | A | 4 h | C-13 | ALTO |
| C-15 | `laboratorio-stock-asincrono` | 3 | C | 3 h | C-02 | ALTO |
| C-16 | `script-reiniciar-seed` | 4 | C | 3 h | C-02, C-04, C-05, C-06, C-07 | MEDIO |
| C-17 | `tests-http-casos-01-05` | 4 | C | 4 h | C-08, C-09, C-10, C-12, C-13, C-14, C-16 | MEDIO |
| C-18 | `tests-http-casos-06-09-y-evidencias` | 4 | C | 5 h | C-13, C-14, C-15, C-16, C-17 | MEDIO |
| C-19 | `readme-y-checklist-entrega` | 4 | B | 4 h | C-17, C-18 | BAJO |

**Total: 19 changes · 67 h · ~22 h por persona.**

---

## FASE 0 — Cimientos y ciclo de vida

> Todo lo demás depende de esta fase. `C-01` es serial; a partir de `C-02` se abre el primer
> fork real con los modelos, que no necesitan la sesión para escribirse.
> Cubre el **10 %** del puntaje ("Proyecto, conexión y ciclo de vida").

### [C-01] `esqueleto-y-configuracion`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona A).
  - Crear `app/__init__.py`, `app/core/{__init__,config}.py`, `app/main.py` y
    `app/modules/<módulo>/{__init__,models,schemas,service,router}.py` para `health`,
    `duenios`, `mascotas`, `practicas`, `turnos` y `laboratorio`. En este change los
    `router.py` son `APIRouter()` vacíos y `models/schemas/service` son stubs.
  - `app/main.py`: instancia `FastAPI` e incluye **los seis routers vacíos** con
    `include_router`. Es la única vez que se edita este archivo para registrar routers.
  - `requirements.txt`: `fastapi[standard]>=0.111`, `sqlmodel>=0.0.24`,
    `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.30`, `python-dotenv>=1.0`.
  - `env.example` con la forma de `DATABASE_URL`
    (`postgresql+asyncpg://usuario:clave@localhost:5432/veterinaria`), sin secretos.
  - `.gitignore` con `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`.
  - `app/core/config.py`: carga el `.env` con `python-dotenv` y expone `DATABASE_URL`; si
    falta, falla con un mensaje explícito al arrancar (no arranca en silencio).
  - Smoke: `uvicorn app.main:app` levanta y `GET /openapi.json` responde 200. Todavía no se
    crea esquema ni se conecta a la base.
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico, §Arquitectura general
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Dependencias
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-01, DD-02
  - `knowledge-base/05_reglas_de_negocio.md` RN-24

---

### [C-02] `motor-sesion-y-lifespan`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona A).
  - `app/core/database.py`: `create_async_engine(DATABASE_URL, echo=True)`,
    `async_sessionmaker(expire_on_commit=False)` y `get_session()` como generador asincrónico
    que toma la fábrica desde `app.state`, entrega una sesión por petición y la cierra.
  - `app/main.py`: `lifespan` que crea el motor y la fábrica al arrancar, los guarda en
    `app.state` y **cierra el motor** al apagar. Sin `create_all` en el arranque: el esquema
    lo crea `reiniciar.py` (DD-01).
  - `echo=True` en el motor para habilitar la evidencia de consultas del caso C-07 (cátedra).
  - Smoke: ciclo arranque/apagado sin errores; una sesión de prueba ejecuta `SELECT 1`;
    `/openapi.json` sigue respondiendo.
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-001
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/05_reglas_de_negocio.md` RN-20, RN-21
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados
  - `knowledge-base/02_descripcion_general.md` §Arquitectura general

---

### [C-03] `health-live-ready`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~2 h (Persona A).
  - `app/modules/health/service.py`: `ping_base(session)` con `SELECT 1`.
  - `app/modules/health/router.py`:
    - `GET /health/live` → `{"estado": "vivo"}` con 200 y **sin** tocar la base.
    - `GET /health/ready` → 200 si `SELECT 1` responde; **503** si la base no contesta.
    - Handlers `async def`.
  - La forma exacta del cuerpo de `/health/ready` es una incógnita abierta (IN-04): se decide
    dentro del change y se documenta; no se fija en este roadmap.
  - Smoke: con PostgreSQL detenido, `/health/ready` da 503 y `/health/live` sigue en 200.
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-002
  - `knowledge-base/05_reglas_de_negocio.md` RN-22
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/10_preguntas_abiertas.md` IN-04
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados

---

## FASE 1 — Modelos, restricciones y DTO

> Es la fase del **30 %** del puntaje y el prerequisito de todos los CRUD. Los cuatro changes
> se pueden escribir en paralelo según el grafo (C-04 y C-06 desde C-01; C-05 desde C-04;
> C-07 desde C-05 y C-06). Cada change incluye los DTO de su módulo.
> **No agregar validaciones que la consigna no pide** (ver `10_preguntas_abiertas.md`).

### [C-04] `modelos-duenios-y-ficha`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~4 h (Persona B).
  - `app/modules/duenios/models.py`:
    - `Duenio`: `id`, `nombre`, `email` con **UNIQUE**.
    - `FichaDuenio`: `id`, `duenio_id` FK → `duenio.id` con **UNIQUE**, `telefono`,
      `direccion`.
    - `Relationship(back_populates=...)` en **ambos extremos**; `Duenio.ficha` devuelve un
      objeto único, no una lista.
  - `app/modules/duenios/schemas.py`: `DuenioCreate` (sin `id`), `DuenioUpdate` (campos
    opcionales), `DuenioRead` (incluye ficha), `FichaCreate`, `FichaRead`.
  - `DuenioUpdate`: el conjunto exacto de campos es ambiguo (preguntas abiertas); se decide
    en el change y se documenta. No ampliar el contrato por iniciativa propia.
  - Verificación: `SQLModel.metadata.create_all` sobre base vacía crea `duenio` y
    `ficha_duenio`; `\d duenio` y `\d ficha_duenio` muestran el UNIQUE.
  - No crear endpoints en este change.
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §`duenio`, §`ficha_duenio`, §Justificación del lado de cada clave foránea
  - `knowledge-base/05_reglas_de_negocio.md` RN-01, RN-03, RN-10, RN-11
  - `knowledge-base/06_funcionalidades.md` §US-003 a §US-007
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-03, DD-06

---

### [C-05] `modelos-mascotas`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona B).
  - `app/modules/mascotas/models.py`: `Mascota` con `id`, `nombre`, `especie`,
    `duenio_id` FK → `duenio.id` **ON DELETE RESTRICT** e **índice** en `duenio_id`.
  - Agregar `Duenio.mascotas` (colección) en `app/modules/duenios/models.py`, con
    `Relationship(back_populates=...)` en ambos extremos. Archivo de B, sin conflicto.
  - `app/modules/mascotas/schemas.py`: `MascotaCreate` (recibe `duenio_id`, sin `id`),
    `MascotaRead` (con dueño resumido para el detalle).
  - Verificación: `\d mascota` muestra FK con RESTRICT e índice; insertar una mascota con
    `duenio_id` inexistente falla en la base.
  - No crear endpoints en este change.
- **Dependencias**: `C-04`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §ERD, §`mascota`, §Justificación del lado de cada clave foránea
  - `knowledge-base/05_reglas_de_negocio.md` RN-08, RN-10
  - `knowledge-base/06_funcionalidades.md` §US-008 a §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 7

---

### [C-06] `modelos-practicas`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona C).
  - `app/modules/practicas/models.py`: `Practica` con `id`, `nombre` **UNIQUE**, `precio`
    `NUMERIC(10,2)` con **CHECK `precio > 0`**.
  - `app/modules/practicas/schemas.py`: `PracticaCreate` con validación de precio mayor que
    cero en el DTO, `PracticaRead`.
  - Dinero con `Decimal`, nunca `float`; serialización como string decimal (DD-06).
  - Verificación: `INSERT` con precio 0 rechazado por el CHECK de la base; el DTO rechaza
    precio ≤ 0 con 422.
  - No crear endpoints en este change.
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §`practica`
  - `knowledge-base/05_reglas_de_negocio.md` RN-02, RN-04, RN-10
  - `knowledge-base/06_funcionalidades.md` §US-012, §US-013
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-06

---

### [C-07] `modelos-turnos-y-turno-practica`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~5 h (Persona A).
  - `app/modules/turnos/models.py`:
    - `Turno`: `id`, `mascota_id` FK con **índice**, `fecha` con zona horaria, `motivo`,
      `total` `NUMERIC(12,2)` con **CHECK `total >= 0`**.
    - `TurnoPractica`: `turno_id` FK → `turno.id` **ON DELETE CASCADE**, `practica_id` FK,
      `precio_unitario` `NUMERIC(10,2)` con **CHECK `precio_unitario > 0`**;
      **PK compuesta (`turno_id`, `practica_id`)**, **índice en `practica_id`** y **sin**
      índice propio en `turno_id`.
    - `Relationship(back_populates=...)` en ambos extremos de cada relación.
    - `Turno.practicas` con `passive_deletes=True` para que el ORM no vacíe ni borre las
      filas hijas: el borrado lo decide la base.
  - `app/modules/turnos/schemas.py`: `TurnoCreate` (`mascota_id`, `fecha`, `motivo`,
    `practicas` con **al menos un** elemento), `TurnoPracticaCreate` (solo `practica_id`),
    `TurnoRead` (mascota resumida + prácticas con `nombre` y `precio_unitario`).
    Sin precio ni total en el DTO de entrada; `Decimal` serializado como string; `fecha` en
    UTC (SU-02).
  - **Traspaso coordinado**: A entrega el fragmento de `Mascota.turnos` a B y el de
    `Practica.turnos` a C; cada dueño lo aplica al inicio del Paso 4. Dos líneas por archivo.
  - Verificación: `\d turno_practica` muestra PK compuesta, CASCADE e índice en
    `practica_id`; borrar un turno por SQL borra sus filas hijas.
  - No agregar reglas de fecha futura ni de turnos duplicados: no están en la consigna.
- **Dependencias**: `C-05`, `C-06`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §`turno`, §`turno_practica`, §Reglas transversales del modelo, §Por qué `turno_practica.turno_id` no necesita índice propio
  - `knowledge-base/05_reglas_de_negocio.md` RN-05, RN-06, RN-07, RN-09
  - `knowledge-base/06_funcionalidades.md` §US-014 a §US-016
  - `knowledge-base/07_flujos_principales.md` §Flujo 4, §Flujo 6
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-05, DD-06, DD-07

---

## FASE 2 — CRUD y contratos HTTP

> Fase del **20 %** ("Contratos y CRUD"). Cada change implementa `service.py` + `router.py`
> del módulo, con handlers `async def`, DTO ya definidos en la fase 1 y los códigos
> 201/204/404/409/422. Ningún endpoint fuera de la tabla de la consigna.
> Los CRUD dependen de `C-02` (sesión) además de su change de modelos.

### [C-08] `crud-duenios`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~5 h (Persona B).
  - `app/modules/duenios/service.py`:
    - Alta: `session.add()` + `commit()` sin consultar si el email existe; `IntegrityError`
      → `rollback()` → excepción propia traducida a 409 con mensaje propio.
    - Detalle: `select(Duenio).options(joinedload(Duenio.ficha))`; 404 si no existe.
    - PATCH: aplica **solo** los campos enviados con `exclude_unset`; email que colisiona →
      409; 404 si no existe.
    - Baja: intenta borrar; si la base rechaza por `ON DELETE RESTRICT` → `rollback()` → 409.
  - `app/modules/duenios/router.py`:
    - `POST /duenios/` → 201 `DuenioRead`, 409, 422.
    - `GET /duenios/{id}` → 200 con ficha, 404, 422 (id no entero).
    - `PATCH /duenios/{id}` → 200 con dueño y ficha, 404, 409, 422.
    - `DELETE /duenios/{id}` → 204 sin cuerpo, 404, 409.
    - Todos `async def`; el router no contiene lógica de negocio.
  - **No** implementar `GET /duenios/` (IN-01) ni `DELETE` de ficha (IN-02).
  - Smoke: email duplicado 409; `/duenios/abc` 422; PATCH parcial no borra los campos no
    enviados; borrar dueño con mascotas 409 (cuando C-05/C-10 estén).
- **Dependencias**: `C-04`, `C-02`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-003 a §US-006
  - `knowledge-base/07_flujos_principales.md` §Flujo 2, §Flujo 7
  - `knowledge-base/05_reglas_de_negocio.md` RN-01, RN-08, RN-11, RN-12, RN-14
  - `knowledge-base/04_modelo_de_datos.md` §`duenio`, §`ficha_duenio`, §Justificación del lado de cada clave foránea
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-03, DD-04

---

### [C-09] `ficha-y-mascotas-por-duenio`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona B).
  - `POST /duenios/{id}/ficha` → 201 `FichaRead`, 404 si el dueño no existe, 409 si ya tenía
    ficha (`UNIQUE(duenio_id)` → `IntegrityError` → `rollback`).
  - `GET /duenios/{id}/mascotas` → 200 con las mascotas del dueño, 404 si el dueño no existe.
  - El service de alta de ficha busca el dueño con precarga de `ficha`; la segunda ficha la
    rechaza la base, no una consulta previa.
  - Forma de la respuesta del listado de mascotas: la consigna solo exige el envoltorio
    paginado para `GET /mascotas/`; la ambigüedad está en preguntas abiertas. Decidir en el
    change y documentarlo.
  - Ambos handlers `async def`, en `duenios/service.py` y `duenios/router.py`.
  - Smoke: segunda ficha 409; dueño inexistente 404; dueño sin mascotas devuelve lista vacía.
- **Dependencias**: `C-08`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004, §US-007, §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 3
  - `knowledge-base/05_reglas_de_negocio.md` RN-03, RN-12, RN-14, RN-15
  - `knowledge-base/04_modelo_de_datos.md` §`ficha_duenio`
  - `knowledge-base/10_preguntas_abiertas.md` IN-01, IN-03 y pregunta del listado por dueño

---

### [C-10] `crud-mascotas`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona B).
  - `app/modules/mascotas/service.py`:
    - Alta con `duenio_id` de un dueño existente; FK inexistente → `IntegrityError` →
      `rollback()` → 409.
    - Detalle: `select(Mascota).options(joinedload(Mascota.duenio))`; 404 si no existe.
  - `app/modules/mascotas/router.py`:
    - `POST /mascotas/` → 201 `MascotaRead`, 409, 422.
    - `GET /mascotas/{id}` → 200 con su dueño, 404.
    - Handlers `async def`.
  - **No** implementar `DELETE /mascotas/{id}` (IN-02).
  - El listado paginado va en `C-11`, no acá.
  - Smoke: dueño inexistente 409; detalle trae el dueño con carga anticipada.
- **Dependencias**: `C-05`, `C-02`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-008, §US-010
  - `knowledge-base/05_reglas_de_negocio.md` RN-12, RN-14, RN-15
  - `knowledge-base/04_modelo_de_datos.md` §`mascota`
  - `knowledge-base/07_flujos_principales.md` §Flujo 7
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-04

---

### [C-11] `listado-paginado-mascotas`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona B).
  - `GET /mascotas/?page=&size=` con el envoltorio
    `{ items, total, page, size, pages }` (RN-13).
  - `size` vale 20 por defecto y va de 1 a 100; fuera de rango → 422.
  - `page` más allá de `pages` → 422; la primera página responde 200 aunque esté vacía.
  - `total` con `SELECT count(*)`; página con `offset`/`limit`. Dos consultas fijas, sin N+1.
  - Query params según el contrato de `02_descripcion_general.md` §API REST; la ubicación
    exacta (`query` vs `path`) es una ambigüedad registrada en preguntas abiertas.
  - Orden por defecto: no está especificado; si se elige uno, documentarlo, no inventarlo
    como regla.
  - Smoke: `size=0` y `size=101` → 422; `page` fuera de rango → 422; base vacía → 200 con
    `items: []`, `total: 0`, `pages: 0`.
- **Dependencias**: `C-10`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-009
  - `knowledge-base/05_reglas_de_negocio.md` RN-13
  - `knowledge-base/02_descripcion_general.md` §Envoltorio de paginación
  - `knowledge-base/10_preguntas_abiertas.md` pregunta de `page`/`size` y orden por defecto
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados

---

### [C-12] `crud-practicas`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~2 h (Persona C).
  - `app/modules/practicas/service.py`: alta (nombre `UNIQUE` → `IntegrityError` →
    `rollback` → 409) y listado completo del catálogo.
  - `app/modules/practicas/router.py`:
    - `POST /practicas/` → 201 `PracticaRead`, 409, 422 (precio ≤ 0).
    - `GET /practicas/` → 200 con el catálogo.
    - Handlers `async def`.
  - Precio con `Decimal`; la validación del DTO y el CHECK de la base deben coincidir.
  - Sin `DELETE` ni `PATCH` de prácticas (IN-02).
  - Smoke: nombre repetido 409; precio 0 → 422; listado devuelve las cuatro prácticas del
    seed cuando `C-16` esté.
- **Dependencias**: `C-06`, `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-012, §US-013
  - `knowledge-base/05_reglas_de_negocio.md` RN-02, RN-04, RN-12
  - `knowledge-base/04_modelo_de_datos.md` §`practica`
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-06

---

## FASE 3 — Altas con relaciones, lecturas sin N+1 y asincronía

> Fase del **15 % + 15 % + 10 %** restante. Es la parte con más riesgo técnico y la que más
> pesa en la defensa: una sola transacción para el alta de turno, carga anticipada explícita
> y la biblioteca sincrónica fuera del event loop.

### [C-13] `alta-turnos-con-practicas`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~5 h (Persona A).
  - `app/modules/turnos/service.py`, alta en **una sola transacción**:
    - Leer del catálogo las prácticas pedidas por `practica_id`.
    - Si **alguna no existe** → `rollback()` → 409 y **no queda guardado nada**: ni el turno
      ni ninguna fila de `turno_practica` (RN-23).
    - Copiar `precio` del catálogo a `precio_unitario` y calcular `total` con `Decimal` en el
      servidor (RN-06). El DTO no lleva precio ni total.
    - Persistir `Turno` + `TurnoPractica` juntos.
    - Práctica repetida en el mismo turno → PK compuesta → `IntegrityError` → `rollback` →
      409 (RN-07).
  - `app/modules/turnos/router.py`: `POST /turnos/` → 201 `TurnoRead`, 409, 422 (lista vacía
    incluida), handler `async def`.
  - Respuesta con `mascota` resumida y `practicas` con `practica_id`, `nombre` y
    `precio_unitario`; `fecha` en UTC (SU-02).
  - Smoke: turno válido con dos prácticas (precios copiados y total correcto); práctica
    inexistente deja la tabla de turnos sin filas nuevas; práctica repetida 409.
- **Dependencias**: `C-07`, `C-10`, `C-12`, `C-02`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-014
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/05_reglas_de_negocio.md` RN-05, RN-06, RN-07, RN-23
  - `knowledge-base/04_modelo_de_datos.md` §`turno`, §`turno_practica`, §Justificación del lado de cada clave foránea
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-03, DD-06, DD-07, SU-02

---

### [C-14] `detalle-y-baja-turno`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~4 h (Persona A).
  - `GET /turnos/{id}`:
    - Una consulta base con `joinedload(Turno.mascota)` y
      `selectinload(Turno.practicas).joinedload(TurnoPractica.practica)` para resolver
      nombres sin N+1.
    - 200 con turno, mascota y prácticas; 404 si no existe.
    - **Número fijo de consultas**, no crece con la cantidad de prácticas (RN-15).
  - `DELETE /turnos/{id}`:
    - Buscar el turno, borrar y `commit`; la base borra las filas de `turno_practica` por
      `ON DELETE CASCADE`; `passive_deletes` evita que el ORM las toque.
    - 204 sin cuerpo; 404 si no existe.
  - Verificación con `echo=True` (C-02): mismo número de consultas para un turno con 1 y con
    3 prácticas. Guardar la salida de consola para `C-18`.
  - Smoke: borrar turno y comprobar por SQL que no quedan filas hijas.
- **Dependencias**: `C-13`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-015, §US-016
  - `knowledge-base/07_flujos_principales.md` §Flujo 5, §Flujo 6
  - `knowledge-base/05_reglas_de_negocio.md` RN-09, RN-14, RN-15, RN-16
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-04, DD-05
  - `knowledge-base/04_modelo_de_datos.md` §Por qué `turno_practica.turno_id` no necesita índice propio

---

### [C-15] `laboratorio-stock-asincrono`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona C).
  - `app/modules/laboratorio/cliente.py`: incorporar el código **exacto** que entrega la
    cátedra (`consultar_stock(vacuna: str) -> int` con `time.sleep(1)`), **sin modificarlo**.
  - `app/modules/laboratorio/service.py`: invocar `consultar_stock` fuera del event loop con
    `await asyncio.to_thread(consultar_stock, vacuna)`.
  - `app/modules/laboratorio/router.py`: `GET /laboratorio/stock/{vacuna}` → 200
    `{"vacuna": ..., "stock": ...}`, handler `async def`.
  - Smoke: tres consultas simultáneas al laboratorio y `GET /health/live` responde de
    inmediato; registrar latencias para el caso C-09 (cátedra).
  - No hay otra integración externa ni variante asincrónica de la biblioteca.
- **Dependencias**: `C-02`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-017
  - `knowledge-base/07_flujos_principales.md` §Flujo 8
  - `knowledge-base/05_reglas_de_negocio.md` RN-17, RN-18, RN-19
  - `knowledge-base/09_decisiones_y_supuestos.md` SU-01
  - `knowledge-base/02_descripcion_general.md` §Integraciones externas

---

## FASE 4 — Entregables y verificación

> Cierre de la entrega. Acá viven los entregables que la consigna evalúa aparte del código:
> `reiniciar.py`, la carpeta `test/` con los casos C-01 a C-09 (cátedra), el `.sql` de C-08,
> la evidencia de consola de C-07 y el `README.md`. `test/` tiene un solo dueño para evitar
> conflictos de numeración y de datos.

### [C-16] `script-reiniciar-seed`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~3 h (Persona C).
  - `reiniciar.py` asincrónico que:
    1. Carga `DATABASE_URL` desde el mismo `.env` que la app (SU-04).
    2. Importa los seis modelos para poblar `SQLModel.metadata`.
    3. Hace `drop_all` y `create_all` (DD-01, sin Alembic).
    4. Carga el seed mínimo: **2 dueños** (uno con ficha), **3 mascotas**, **4 prácticas**,
       **1 turno con 2 prácticas** (con `precio_unitario` copiado y `total` calculado).
  - Funciona tanto sobre una base vacía como sobre una base ya poblada (el `drop_all` va
    primero).
  - Smoke: correrlo dos veces seguidas; verificar counts y que `GET /mascotas/` y
    `GET /turnos/{id}` devuelvan datos coherentes.
  - Es el prerequisito de todos los `.http`: se corre después de cada cambio de modelos.
- **Dependencias**: `C-02`, `C-04`, `C-05`, `C-06`, `C-07`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial
  - `knowledge-base/06_funcionalidades.md` §US-018
  - `knowledge-base/07_flujos_principales.md` §Flujo 9
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-01, SU-04
  - `knowledge-base/08_arquitectura_propuesta.md` §Entregables del repositorio

---

### [C-17] `tests-http-casos-01-05`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~4 h (Persona C).
  - `test/caso_C-01.http`: `GET /duenios/abc` → **422**, sin ejecutar el handler.
  - `test/caso_C-02.http`: email de dueño repetido y nombre de práctica repetido → **409**
    con mensaje propio.
  - `test/caso_C-03.http`: segunda ficha para el mismo dueño → **409**.
  - `test/caso_C-04.http`: mascota con dueño inexistente → **409**; turno con práctica
    inexistente → **409** y verificación de que **no quedó guardado nada**.
  - `test/caso_C-05.http`: `DELETE` de dueño con mascotas → **409**; `DELETE` de turno →
    **204** y sus prácticas ya no están.
  - Cada archivo con un comentario que indique la respuesta esperada; se ejecutan después de
    `python reiniciar.py`.
  - Si un caso falla, se reporta al dueño del módulo (A, B o C); **no** se parchea código desde
    `test/`.
- **Dependencias**: `C-08`, `C-09`, `C-10`, `C-12`, `C-13`, `C-14`, `C-16`
- **Governance**: MEDIO
- **Leer antes**:
  - `docs/MiniTP_Cap1a4_Consigna.pdf` §Casos de prueba mínimos, C-01 a C-05
  - `knowledge-base/06_funcionalidades.md` §US-019
  - `knowledge-base/05_reglas_de_negocio.md` RN-01 a RN-08, RN-12
  - `knowledge-base/07_flujos_principales.md` §Flujo 2, §Flujo 3, §Flujo 6, §Flujo 7
  - `knowledge-base/08_arquitectura_propuesta.md` §Entregables del repositorio

---

### [C-18] `tests-http-casos-06-09-y-evidencias`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~5 h (Persona C).
  - `test/caso_C-06.http`: turno válido con dos prácticas → **201**, con los precios copiados
    del catálogo y el total calculado por el servidor.
  - `test/caso_C-07.http`: detalle de un turno con **1** práctica y con **3** prácticas; en
    ambos casos la **misma cantidad de consultas** en la consola con `echo=True`.
  - `test/caso_C-08.sql`: `UPDATE practica SET precio = 0` ejecutado directo en la base; la
    base lo rechaza por el `CHECK`. `test/caso_C-08.http` registra el precio antes y después
    para mostrar que no cambió.
  - `test/caso_C-09.http`: tres consultas simultáneas al laboratorio + `GET /health/live`;
    el de salud responde de inmediato. Medir y anotar la latencia.
  - `test/evidencia_C-07.txt`: fragmento de consola con las consultas del detalle de un turno
    con una práctica y con tres. Es **entregable obligatorio**.
  - Todo se corre después de `python reiniciar.py`; si un caso falla, se reporta al dueño del
    módulo, no se corrige desde `test/`.
- **Dependencias**: `C-13`, `C-14`, `C-15`, `C-16`, `C-17`
- **Governance**: MEDIO
- **Leer antes**:
  - `docs/MiniTP_Cap1a4_Consigna.pdf` §Casos de prueba mínimos, C-06 a C-09
  - `knowledge-base/07_flujos_principales.md` §Flujo 4, §Flujo 5, §Flujo 8
  - `knowledge-base/05_reglas_de_negocio.md` RN-06, RN-09, RN-15, RN-19
  - `knowledge-base/09_decisiones_y_supuestos.md` SU-02
  - `knowledge-base/08_arquitectura_propuesta.md` §Entregables del repositorio

---

### [C-19] `readme-y-checklist-entrega`

- **Estado**: `[ ]` pendiente
- **Scope**:
  - **Esfuerzo**: ~4 h (Persona B).
  - `README.md` con los pasos para levantar el proyecto **desde cero**:
    requisitos (Python 3.12+, PostgreSQL 16), entorno virtual, `pip install -r requirements.txt`,
    copiar `env.example` a `.env`, crear la base, `python reiniciar.py` y
    `uvicorn app.main:app`.
  - Tabla de endpoints y códigos (la de `02_descripcion_general.md`), instrucciones para
    correr los `.http` de `test/` y el `.sql` del caso C-08.
  - Explicación en **1-2 líneas** de por qué `turno_practica.turno_id` no necesita índice
    propio: la PK compuesta `(turno_id, practica_id)` ya tiene un B-tree con `turno_id` como
    primera columna. Es un requisito explícito de la consigna.
  - Enlace a `test/evidencia_C-07.txt` y a los casos C-01 a C-09.
  - Registrar como **decisión propia** lo que quedó abierto (por ejemplo, el cuerpo de
    `/health/ready`, IN-04). No presentarlo como regla de la cátedra.
  - Aviso de que `.env` no se versiona y checklist final: `requirements.txt`, `env.example`,
    `reiniciar.py`, `test/`, `README.md`, sin credenciales reales.
  - Verificación: seguir los pasos desde una base vacía y confirmar que la app levanta y que
    el seed queda cargado.
- **Dependencias**: `C-17`, `C-18`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Entregables del repositorio
  - `knowledge-base/04_modelo_de_datos.md` §Por qué `turno_practica.turno_id` no necesita índice propio
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico, §Arquitectura general
  - `knowledge-base/06_funcionalidades.md` §US-018, §US-019
  - `knowledge-base/10_preguntas_abiertas.md` IN-04

---

> **Primer change recomendado**: `C-01` (`esqueleto-y-configuracion`), Persona A.
> Para arrancar: `/opsx:propose C-01-esqueleto-y-configuracion`.
> En paralelo, B y C pueden hacer `/opsx:propose` de `C-04` y `C-06` y leer la KB, sin tocar
> código hasta que `C-01` esté archivado.

