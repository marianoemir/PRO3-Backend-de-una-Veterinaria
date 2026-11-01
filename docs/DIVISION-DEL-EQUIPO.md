# División del equipo — TP Veterinaria (SDD con Active Stack)

**Equipo**: Mariano · Facundo · Andrés
**Estado al**: 01/11/2026 · changes `01` y `02` **mergeados** en `main`; del `03` al `11` pendientes.
**Fecha y hora de entrega**: `____________` ← completar entre los tres y trabajar hacia atrás desde ahí.
**Fuente de verdad**: `docs/MiniTP_Cap1a4_Consigna.pdf`. Roadmap y detalle de cada change: `CHANGES.md`. Reglas del agente: `AGENTS.md` / `CLAUDE.md`.

---

## 0. Dónde estamos y qué hace cada uno ahora

**Ya está en `main`**: `01` fundacion-proyecto, `02` modelos-y-esquema y un refactor chico (el motor y la fábrica de sesiones viven en `app/core/database.py` con `crear_motor` y `crear_fabrica`; el `lifespan` de `app/main.py` los usa). Hacé `git pull` antes de empezar.

**Desde ahora los tres trabajan a la vez.** Nadie espera a nadie para arrancar, salvo las dependencias de la tabla de la sección 1.

| Persona | Empieza ya con | Después | Qué lo frena |
|---|---|---|---|
| **Mariano** | `09` reiniciar-y-seed | `06` turnos-alta-transaccional → `07` turnos-lecturas-y-baja | El `06` necesita el `09` mergeado (es suyo). No depende de Facundo ni de Andrés. |
| **Facundo** | `03` duenios-y-ficha | `05` mascotas-y-paginacion | El `05` necesita el `03` mergeado (es suyo). |
| **Andrés** | `04` practicas-catalogo y `08` laboratorio-sin-bloqueo | borradores de `.http` (sin commitear) | Nada: el `04` y el `08` son independientes entre sí, el orden da igual. Si el `08` ya está hecho, solo queda el `04`. |

**Al final**: el `10` (pruebas, Andrés) espera que estén mergeados del `03` al `09`, y el `11` (README, Facundo) espera el `10`. La cadena más larga es la de Mariano (`09 → 06 → 07`): si Mariano se atrasa, Andrés puede tomar el `07`.

**Cómo se revisa**: ver "Política de revisión" en la sección 2. En resumen: los PRs se revisan **en rondas** (se juntan dos y se revisan a la vez), salvo los que bloquean a otro, que se revisan apenas se abren.

---

## 1. De un vistazo

| # | Change | Dueño | Depende de | Lo revisa | Estimación* | Estado |
|---|---|---|---|---|---|---|
| 01 | `fundacion-proyecto` | Mariano | — | Facundo | 6–8 h | ✅ mergeado |
| 02 | `modelos-y-esquema` | Mariano | 01 | Facundo **y** Andrés | 8–10 h | ✅ mergeado |
| 03 | `duenios-y-ficha` | Facundo | 02 | Andrés | 7–9 h | ⬜ pendiente |
| 04 | `practicas-catalogo` | Andrés | 02 | Facundo | 2–3 h | ⬜ pendiente |
| 05 | `mascotas-y-paginacion` | Facundo | 03 | Andrés | 5–7 h | ⬜ pendiente |
| 06 | `turnos-alta-transaccional` | Mariano | 02, 09 | Facundo **y** Andrés | 6–7 h | ⬜ pendiente |
| 07 | `turnos-lecturas-y-baja` | Mariano | 06 | Andrés | 4 h | ⬜ pendiente |
| 08 | `laboratorio-sin-bloqueo` | Andrés | 01 | Facundo | 3 h | ⬜ pendiente |
| 09 | `reiniciar-y-seed` | Mariano | 02 | Facundo | 3 h | ⬜ pendiente |
| 10 | `pruebas-http-y-evidencia` | Andrés | 03–09 (todos) | Mariano | 8–10 h | ⬜ pendiente |
| 11 | `readme-y-entrega` | Facundo | 10 | Andrés | 4 h | ⬜ pendiente |

\* Orientativas: incluyen leer la KB, escribir los artefactos de OpenSpec y verificar.
**Carga aproximada**: Mariano ~30 h · Facundo ~18 h · Andrés ~15 h, más las revisiones cruzadas de cada uno.

### Quién espera a quién

```
Mariano:  [01] ─▶ [02] ─▶ [09] ─▶ [06] ─▶ [07] ─────────────────────────┐
                    │                                                    │
Facundo:            └──────▶ [03] ─▶ [05] ───────────────┐               │
                    │                                     ▼               ▼
Andrés:   [08]◀─[01]└──────▶ [04] ────────────────────▶ [10] ─────────▶ [11] (Facundo)
```

- Los dos hitos de Mariano (`01` y `02`) **ya están mergeados**: era lo único que frenaba a los otros dos. Ahora solo quedan las dependencias de la tabla: `05` espera `03`, `06` espera `09`, `07` espera `06`, `10` espera del `03` al `09`, `11` espera `10`.
- Después del `02` trabajan los tres a la vez sin pisarse: cada uno toca solo sus módulos.
- `06` usa los datos del seed de `09`, por eso `09` va antes. Así Mariano no depende de los CRUD de Facundo ni de Andrés.
- `10` (pruebas) espera a todos los endpoints. `11` (README) espera a `10`.

---

## 2. Cómo se hace cada change (el ciclo, siempre igual)

> Una **sesión nueva** de OpenCode por change, abierta en la raíz del repo. No arrastres contexto viejo.

```powershell
git checkout main
git pull
git checkout -b feature/<nombre-del-change>
```

1. **Proponer** — en OpenCode, pegar el bloque `/opsx:propose` del change (sección 5). **No** implementa nada: genera `proposal.md`, `design.md`, `specs/` y `tasks.md` en `openspec/changes/<change>/`.
2. **Revisar los 4 artefactos antes de seguir** (checklist de abajo). Mandarle al revisor solo `design.md` y `tasks.md` para que los mire rápido (10 minutos): es más barato corregir un diseño que código.
3. **Aplicar** — `/opsx:apply <change>` (prompt de la sección 5). Implementa las tasks en orden.
4. **Verificar** — correr el *Smoke* del change (en `CHANGES.md`) y pegar la **salida real** de los comandos; la explicación del agente no cuenta como evidencia.
5. **Archivar** — `/opsx:archive <change>`. Después marcar `[x]` **solo la línea de tu change** en `CHANGES.md`.
6. **Commit y PR** (lo hace la persona, no el agente):
   ```powershell
   git status
   git add <los archivos de tu change> openspec/changes/archive/<tu-change> openspec/specs/<tu-spec> CHANGES.md
   git status
   git commit -m "feat(<modulo>): <change>"
   git push -u origin feature/<nombre-del-change>
   ```
   **No uses `git add -A`**: en Windows Git puede marcar como modificados archivos que no tocaste (diferencias de saltos de línea CRLF/LF) y se cuelan al PR. Agregá los archivos a mano y revisá el segundo `git status`: tienen que aparecer solo los tuyos. Los avisos `LF will be replaced by CRLF` son normales.
   Después abrí el Pull Request en GitHub, pegá en la descripción la salida real del smoke, seguí la política de revisión de abajo, **mergeá a `main`** y avisá al grupo. Todos hacen `git pull`.

### Política de revisión (en rondas, para ir más rápido)

Revisar cada change apenas se abre frena a todos. Por eso se revisa **en rondas**:

1. **Artefactos (`design.md` y `tasks.md`)**: revisión corta y enseguida, antes del `/opsx:apply`. Es lo que más ahorra: un error de diseño detectado acá no se convierte en código.
2. **PRs de código**: cuando hay dos PRs abiertos, el revisor los mira **los dos juntos** en una sola sentada, y se mergean uno después del otro. No hace falta que cada PR espere su turno aislado.
3. **Excepción, PRs que bloquean a otro**: se revisan **apenas se abren**, sin esperar la ronda. Son `03` (bloquea `05`), `09` (bloquea `06`) y `06` (bloquea `07`).
4. **Mientras esperás una revisión, seguí con tu siguiente change** si no depende del que está en revisión (por ejemplo, Andrés pasa del `04` al `08`). Si depende, preparás borradores fuera de `openspec/`.
5. **Qué se mira en un PR** (15 minutos como máximo): `git diff --stat` toca solo los archivos del change; la descripción trae la salida real del smoke; la spec tiene sus escenarios; no hay `.env` ni credenciales.
6. **Si nadie revisó un PR que bloquea en 3 horas**, el dueño lo mergea con la evidencia pegada y avisa al grupo. (Plazo propuesto: ajustarlo entre los tres.)

### Checklist antes de `/opsx:apply` (revisión de artefactos)

- [ ] ¿Las dependencias del change están **archivadas y mergeadas** en `main`?
- [ ] ¿Cada regla citada (`RN-*`) existe en `knowledge-base/05_reglas_de_negocio.md`? ¿Alguna es invento del agente?
- [ ] ¿Lo ambiguo quedó como decisión del equipo (`DD-08` a `DD-15`) o como pregunta abierta, y no como decisión silenciosa?
- [ ] ¿Cada spec tiene **≥ 3 escenarios** (esperado, error de negocio y borde) y cada escenario una task de verificación?
- [ ] ¿Las decisiones de dominio (lado de la FK, regla de borrado, códigos HTTP) están **justificadas en `design.md`**?
- [ ] ¿El change toca solo sus archivos? ¿No crea endpoints que no están en la tabla de `02_descripcion_general.md`?

### Checklist antes de archivar

- [ ] El smoke del change se corrió y pasó (salida real a la vista).
- [ ] Cada escenario de la spec tiene su verificación.
- [ ] `uvicorn app.main:app` levanta y `python reiniciar.py` sigue funcionando (si ya existe).
- [ ] Sin `.env`, sin credenciales y sin datos reales en el diff (`git diff --stat`).
- [ ] Solo tu línea de `CHANGES.md` cambió.

---

## 3. Plan por etapas (qué hace cada uno y qué hace mientras espera)

| Etapa | Mariano | Facundo | Andrés |
|---|---|---|---|
| **0 · Preparación** ✅ | Copia las correcciones al repo, borra `openspec/changes/tp1`, hace los 4 commits de la fundación y **sube a `main`** | Espera el push, clona, crea su entorno y su base local (sección 4), abre OpenCode | Igual que Facundo |
| **1 · Fundación** ✅ | **`01` fundacion-proyecto** | Prepara el entorno; **revisa los artefactos de `01`**; lee KB `04`, `05`, `06` | Prepara el entorno; lee KB `04`, `05`, `07`, `09` y el PDF de la consigna |
| **2 · Modelos** ✅ | **`02` modelos-y-esquema** (el 30 %: es lo más cuidadoso) | Revisa los artefactos de `02` con lupa; lee KB `06` (US-003 a 011) y `07` | **`08` laboratorio-sin-bloqueo** (solo necesita `01`); revisa los artefactos de `02` |
| **3 · CRUD y seed** | `09` reiniciar-y-seed → `06` turnos-alta-transaccional | `03` duenios-y-ficha → `05` mascotas-y-paginacion | `04` practicas-catalogo; después prepara borradores de `.http` (sin commitear) |
| **4 · Lecturas** | `07` turnos-lecturas-y-baja (+ captura la evidencia de consola) | Termina `05`; prepara el borrador del README en un archivo local | Revisa PRs de `06`, `07`; espera que estén todos mergeados |
| **5 · Pruebas y README** | Revisa `10`; verifica `python reiniciar.py` sobre base vacía | `11` readme-y-entrega (cuando `10` esté mergeado) | **`10` pruebas-http-y-evidencia** |
| **6 · Cierre** | Sigue el README al pie de la letra en un entorno limpio; checklist final; arma el zip con `git archive` (nunca comprimir la carpeta: arrastra el `.env`) | Corrige el README con lo que encuentre Mariano | Corre los 9 casos una vez más contra `main` |

**Regla de las esperas**: nadie ejecuta `/opsx:propose` de un change con dependencias sin mergear. Mientras esperás: leer la KB, revisar artefactos y PRs de los demás, preparar borradores fuera de `openspec/`.

### Sugerencia de calendario (ajustar a la fecha real de entrega)

| Día | Hito |
|---|---|
| 1 | Etapa 0 y 1: fundación en `main`; `01` mergeado |
| 2 | `02` mergeado (hay que **cuidar este hito**: destraba a los otros dos) |
| 3 | `03`, `04`, `08` y `09` mergeados |
| 4 | `05`, `06` y `07` mergeados |
| 5 | `10` y `11`; verificación integral |
| Colchón | Un día completo antes de la entrega para corregir y ensayar el README desde cero |

---

## 4. Base de datos: PostgreSQL (responsable: Mariano)

**Sobre la versión**: tienen PostgreSQL 17.10 y el enunciado pide **16 o más**. No hay problema. Todo lo que usa este TP (tablas, `UNIQUE`, `CHECK`, claves foráneas con `RESTRICT` y `CASCADE`, `NUMERIC`, `TIMESTAMP WITH TIME ZONE`, índices, transacciones) se comporta igual en 16 y en 17. Lo único que existe en 17 y no en 16 son cosas que este TP no toca (`JSON_TABLE`, `MERGE ... RETURNING`, etc.). La advertencia anterior era de cautela, no de un riesgo concreto: mientras no escriban SQL exótico, el código es compatible.

Qué hace Mariano, **antes de que arranque el `01`**:

1. **Comprobar que el servidor anda y la versión** (PowerShell, el usuario `postgres` puede variar):
   ```powershell
   psql -U postgres -c "SELECT version();"
   ```
   Si `psql` no se reconoce, usar la consola de SQL de pgAdmin o agregar `...\PostgreSQL\17\bin` al `PATH`.
2. **Crear la base del proyecto**:
   ```powershell
   psql -U postgres -c "CREATE DATABASE veterinaria;"
   ```
3. **Definir el `.env` local** (no se versiona; cada uno el suyo) a partir de `env.example`:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:TU_CLAVE@localhost:5432/veterinaria
   ```
   - Si la clave tiene caracteres especiales (`@`, `:`, `/`, `#`), hay que **codificarlos** en la URL (`@` → `%40`).
   - Si el puerto 5432 lo usa otro servicio, cambiarlo en el `.env`; no en el código.
4. **Instalar las dependencias en un entorno virtual y comprobar que Python 3.13 las acepta** (`asyncpg>=0.30` es la que más puede fallar en versiones nuevas de Python):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install "fastapi[standard]>=0.111" "sqlmodel>=0.0.24" "sqlalchemy[asyncio]>=2.0" "asyncpg>=0.30" "python-dotenv>=1.0"
   ```
   Si algo falla, **avisar al grupo antes de seguir** (puede obligar a usar Python 3.12 para todos).
5. **Verificar la conexión asincrónica** con un script descartable (no se commitea) que ejecute `SELECT 1` con `create_async_engine`.
6. **Opcional, para quedarse tranquilos con la versión 16**: probar `python reiniciar.py` una vez sobre una instancia de PostgreSQL 16 (instalación en paralelo en otro puerto, o un contenedor temporal solo en su máquina). No forma parte del proyecto ni se entrega.
7. **Cuando haya modelos (`02`)**: mirar el esquema real con `\d` de cada tabla y comparar contra `knowledge-base/04_modelo_de_datos.md`.

**Facundo y Andrés**: cada uno instala PostgreSQL 16 o más en su máquina, crea su propia base `veterinaria` y su `.env`. No comparten base.

---

## 5. Los changes, uno por uno

> Cada bloque `/opsx:propose` se pega **tal cual** en una sesión nueva de OpenCode. El alcance, las reglas y los archivos de "Leer antes" están en `CHANGES.md` (sección del change).

### [01] `fundacion-proyecto` — Mariano

- **Depende de**: nada. **Desbloquea**: `02` y `08`. **Rama**: `feature/fundacion-proyecto`. **Revisa**: Facundo.
- **Toca**: `app/__init__.py`, `app/main.py`, `app/core/*`, stubs de los seis módulos, `health`, `requirements.txt`, `env.example`.
- **No toca**: reglas de dominio, modelos, ningún endpoint fuera de `health`.

```
/opsx:propose fundacion-proyecto
Leé primero la sección [01] de CHANGES.md y los archivos de "Leer antes".
Dejá app/main.py con los seis routers ya incluidos (vacíos salvo health), para que nadie más tenga que editarlo.
Lifespan: crear el motor y la fábrica de sesiones, guardarlos en app.state y cerrar el motor al apagar. get_session entrega una sesión por petición con expire_on_commit=False. Sin create_all en el arranque.
Si falta DATABASE_URL, que el arranque falle con un mensaje claro.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 de knowledge-base/09 o es pregunta abierta; justificá en design.md cada decisión de dominio.
Tocá solo los archivos de este change. No ejecutes /opsx:apply.
```
```
/opsx:apply fundacion-proyecto
Implementá las tasks en orden. Después de cada grupo corré el smoke del change. No commitees. Al final listá los comandos que corriste con su salida real.
```
- **Puntos de atención**: que `/health/ready` devuelva **503** con PostgreSQL detenido (probarlo de verdad: detené el servicio desde `services.msc`); que `echo=True` esté activo (hace falta para la evidencia del caso C-07); que ningún `.env` aparezca en `git status`.
- **Cuando termina**: merge a `main` y **aviso al grupo** → Andrés arranca `08` y los demás ya pueden clonar el esqueleto.

### [02] `modelos-y-esquema` — Mariano

- **Depende de**: `01`. **Desbloquea**: `03`, `04`, `09` (y a través de ellos todo lo demás). **Rama**: `feature/modelos-y-esquema`. **Revisan**: Facundo y Andrés.
- **Toca**: los cuatro `models.py` (`duenios`, `mascotas`, `practicas`, `turnos`). **Nadie más los toca.**
- **No toca**: `schemas.py`, `service.py`, `router.py`, `reiniciar.py`.
- **Por qué lo hace una sola persona**: es el 30 % de la nota y las relaciones se declaran en los dos extremos (`Duenio.mascotas` y `Mascota.duenio`, `Mascota.turnos` y `Turno.mascota`, `Practica.turnos` y `TurnoPractica.practica`): repartirlo obliga a coordinar líneas en archivos ajenos.

```
/opsx:propose modelos-y-esquema
Leé primero la sección [02] de CHANGES.md y knowledge-base/04_modelo_de_datos.md completo.
Los nombres de tablas y columnas son obligatorios y vienen del PDF: no renombres ni quites nada.
Declará todas las relaciones en los dos extremos con back_populates; Duenio.ficha devuelve un objeto (uselist=False); Turno.practicas con passive_deletes=True.
Agregá PK compuesta (turno_id, practica_id) en TurnoPractica, el índice en practica_id y NO agregues índice propio en turno_id. Dinero con Decimal/NUMERIC.
En design.md justificá, tabla por tabla, de qué lado va cada clave foránea y cada regla de borrado (RESTRICT, CASCADE, y el default donde la consigna no dice nada: DD-13).
Este change NO incluye DTO ni endpoints.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno (consultas \d y SQL de rechazo).
No inventes reglas. Tocá solo los cuatro models.py. No ejecutes /opsx:apply.
```
```
/opsx:apply modelos-y-esquema
Implementá las tasks en orden. Para verificar usá un script temporal NO versionado que haga create_all y comprobá con psql el \d de las 6 tablas y las pruebas de rechazo por SQL (precio 0, práctica repetida en un turno, borrar dueño con mascotas, borrar turno con cascada). No commitees. Mostrame la salida real de cada comando.
```
- **Puntos de atención**: `configure_mappers()` sin errores; el `\d turno_practica` tiene que mostrar PK compuesta, `CASCADE`, CHECK e índice en `practica_id`; las FK de `ficha_duenio`, `mascota` y `turno` con los nombres de columna exactos.
- **Revisión cruzada**: este es el change que **más conviene que miren dos personas**, comparando contra la tabla del PDF.
- **Cuando termina**: merge, aviso, y Facundo/Andrés arrancan sus changes.

### [03] `duenios-y-ficha` — Facundo

- **Depende de**: `02`. **Desbloquea**: `05`, `10`. **Rama**: `feature/duenios-y-ficha`. **Revisa**: Andrés.
- **Toca**: `app/modules/duenios/{schemas,service,router}.py`. **No toca**: `duenios/models.py`.

```
/opsx:propose duenios-y-ficha
Leé primero la sección [03] de CHANGES.md y los archivos de "Leer antes".
Alta, PATCH, ficha y baja: se escribe y se captura IntegrityError -> rollback() -> 409 con mensaje propio. Prohibido hacer un SELECT previo para ver si existe.
DuenioUpdate con nombre y email opcionales (DD-08); PATCH con exclude_unset; GET /duenios/{id}/mascotas devuelve lista simple (DD-10).
Definí en duenios/schemas.py la vista resumida de mascota que necesites; no importes DTO de otros módulos.
No implementes GET /duenios/ ni DELETE de ficha.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 o es pregunta abierta; justificá en design.md cada decisión de dominio.
Tocá solo los archivos de este change. No ejecutes /opsx:apply.
```
```
/opsx:apply duenios-y-ficha
Implementá las tasks en orden. Después de cada grupo corré el smoke del change contra la app levantada. No commitees. Al final listá los comandos con su salida real.
```
- **Puntos de atención**: `/duenios/abc` debe dar 422 sin ejecutar el handler; el detalle del dueño usa `joinedload(Duenio.ficha)` (sin carga perezosa); borrar un dueño con mascotas da 409 por `RESTRICT` (se prueba con datos por SQL si `09` todavía no está mergeado).

### [04] `practicas-catalogo` — Andrés

- **Depende de**: `02`. **Desbloquea**: `10`. **Rama**: `feature/practicas-catalogo`. **Revisa**: Facundo.
- **Toca**: `app/modules/practicas/{schemas,service,router}.py`. **No toca**: `practicas/models.py`.

```
/opsx:propose practicas-catalogo
Leé primero la sección [04] de CHANGES.md y los archivos de "Leer antes".
El precio se valida mayor que cero en el DTO (422) y además lo garantiza el CHECK de la base. Dinero con Decimal, serializado como string.
Nombre repetido: se escribe y se captura IntegrityError -> rollback() -> 409. Sin SELECT previo.
Solo POST /practicas/ y GET /practicas/ (orden por id). Sin PATCH ni DELETE.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 o es pregunta abierta; justificá en design.md cada decisión de dominio.
Tocá solo los archivos de este change. No ejecutes /opsx:apply.
```
```
/opsx:apply practicas-catalogo
Implementá las tasks en orden. Corré el smoke del change contra la app levantada. No commitees. Al final listá los comandos con su salida real.
```

### [05] `mascotas-y-paginacion` — Facundo

- **Depende de**: `03`. **Desbloquea**: `10`. **Rama**: `feature/mascotas-y-paginacion`. **Revisa**: Andrés.
- **Toca**: `app/modules/mascotas/{schemas,service,router}.py`.

```
/opsx:propose mascotas-y-paginacion
Leé primero la sección [05] de CHANGES.md y los archivos de "Leer antes".
POST /mascotas/ recibe duenio_id: si el dueño no existe lo rechaza la FK -> IntegrityError -> rollback() -> 409. Sin SELECT previo.
GET /mascotas/ con ?page=&size= y el envoltorio { items, total, page, size, pages }: size 20 por defecto y de 1 a 100; página más allá de pages -> 422; la primera página SIEMPRE responde 200, aunque no haya resultados (pages = 0). Total con count(*), página con offset/limit, orden por id: dos consultas fijas.
GET /mascotas/{id} con el dueño cargado en la misma consulta (joinedload). Definí tu propia vista resumida del dueño en mascotas/schemas.py.
No implementes DELETE /mascotas/{id}.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 o es pregunta abierta; justificá en design.md cada decisión de dominio.
Tocá solo los archivos de este change. No ejecutes /opsx:apply.
```
```
/opsx:apply mascotas-y-paginacion
Implementá las tasks en orden. Corré el smoke del change contra la app levantada (incluí size=0, size=101, page fuera de rango y base vacía). No commitees. Al final listá los comandos con su salida real.
```

### [06] `turnos-alta-transaccional` — Mariano

- **Depende de**: `02`, `09`. **Desbloquea**: `07`. **Rama**: `feature/turnos-alta-transaccional`. **Revisan**: Facundo y Andrés.
- **Toca**: `app/modules/turnos/{schemas,service,router}.py`.

```
/opsx:propose turnos-alta-transaccional
Leé primero la sección [06] de CHANGES.md y los archivos de "Leer antes".
POST /turnos/ en UNA sola transacción: turno + todas sus filas de turno_practica o nada. Si una práctica no existe -> rollback() -> 409 y no queda guardado ni el turno ni ninguna práctica.
El DTO de entrada trae mascota_id, fecha, motivo y practicas (al menos una, solo practica_id): ni precio ni total. El servidor copia el precio del catálogo a precio_unitario y calcula el total con Decimal.
Práctica repetida en el turno -> la PK compuesta lo rechaza -> IntegrityError -> rollback() -> 409. Mascota inexistente -> 409 por FK. Lista vacía -> 422.
La respuesta se arma sin carga perezosa. La fecha de salida va en UTC. Sin id de fila en las prácticas (DD-11).
Definí en turnos/schemas.py tus propias vistas resumidas de mascota y práctica; no importes DTO de otros módulos.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 o es pregunta abierta; justificá en design.md cada decisión de dominio.
Tocá solo los archivos de este change. No ejecutes /opsx:apply.
```
```
/opsx:apply turnos-alta-transaccional
Implementá las tasks en orden. Probá con los datos del seed (python reiniciar.py primero): turno válido con las prácticas 1 y 3 (total "27000.00"), práctica inexistente (y comprobá con SELECT count(*) FROM turno que no cambió), práctica repetida, lista vacía. No commitees. Al final listá los comandos con su salida real.
```
- **Puntos de atención**: es el único change donde se **lee antes de escribir** (el catálogo de prácticas, para copiar precios): eso es correcto y no viola la regla de "sin consulta previa", porque la regla aplica a las restricciones UNIQUE/FK/CHECK, no a leer datos que hay que copiar. Dejarlo explicado en `design.md`.

### [07] `turnos-lecturas-y-baja` — Mariano

- **Depende de**: `06`. **Desbloquea**: `10`. **Rama**: `feature/turnos-lecturas-y-baja`. **Revisa**: Andrés.
- **Toca**: `app/modules/turnos/{service,router}.py`.

```
/opsx:propose turnos-lecturas-y-baja
Leé primero la sección [07] de CHANGES.md y los archivos de "Leer antes".
GET /turnos/{id}: una consulta base con joinedload(Turno.mascota) y selectinload(Turno.practicas).joinedload(TurnoPractica.practica). El número de consultas NO crece con la cantidad de prácticas. 404 si no existe.
DELETE /turnos/{id}: la base borra turno_practica por ON DELETE CASCADE; el ORM no las toca (passive_deletes). 204; 404 si no existe.
Incluí una task que capture la consola (echo=True) del detalle de un turno con 1 práctica y con 3 prácticas, para la evidencia del caso C-07.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 o es pregunta abierta; justificá en design.md cada decisión de dominio.
Tocá solo los archivos de este change. No ejecutes /opsx:apply.
```
```
/opsx:apply turnos-lecturas-y-baja
Implementá las tasks en orden. Mostrame la consola con las consultas del detalle para 1 y para 3 prácticas (misma cantidad) y la comprobación por SQL de que el borrado no deja filas hijas. No commitees.
```
- **Entrega a Andrés**: guardar la salida de consola en un archivo local (no se commitea acá) y pasársela para `10`.

### [08] `laboratorio-sin-bloqueo` — Andrés

- **Depende de**: `01`. **Desbloquea**: `10`. **Rama**: `feature/laboratorio-sin-bloqueo`. **Revisa**: Facundo.
- **Toca**: `app/modules/laboratorio/*`. **`cliente.py` se crea con el código exacto de la cátedra y no se modifica nunca.**

```
/opsx:propose laboratorio-sin-bloqueo
Leé primero la sección [08] de CHANGES.md y los archivos de "Leer antes".
cliente.py debe contener EXACTAMENTE el código de la consigna (consultar_stock con time.sleep(1)) y no se modifica.
El service llama a consultar_stock con await asyncio.to_thread(...). El handler es async def y no ejecuta ninguna llamada bloqueante.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 o es pregunta abierta; justificá en design.md cada decisión de dominio.
Tocá solo los archivos de este change. No ejecutes /opsx:apply.
```
```
/opsx:apply laboratorio-sin-bloqueo
Implementá las tasks en orden. Probá tres consultas simultáneas a /laboratorio/stock/{vacuna} con un GET /health/live en el medio y anotá las latencias reales. No commitees. Al final listá los comandos con su salida real.
```

### [09] `reiniciar-y-seed` — Mariano

- **Depende de**: `02`. **Desbloquea**: `06` y `10`. **Rama**: `feature/reiniciar-y-seed`. **Revisa**: Facundo.
- **Toca**: `reiniciar.py`.

```
/opsx:propose reiniciar-y-seed
Leé primero la sección [09] de CHANGES.md y knowledge-base/04_modelo_de_datos.md §Seed data inicial.
reiniciar.py es asincrónico, lee DATABASE_URL del mismo .env que la app, importa los modelos de los cuatro módulos, hace drop_all, create_all y carga: 2 dueños (uno con ficha), 3 mascotas, 4 prácticas y 1 turno con 2 prácticas (precio_unitario copiado y total calculado).
Respetá los ids del ejemplo de la consigna: mascota 1 = Toby (perro), práctica 1 = Consulta 15000.00, práctica 3 = Vacuna antirrábica 12000.00; el próximo turno debe recibir id 2. Datos ficticios.
Debe funcionar sobre una base vacía y sobre una ya poblada.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas. Tocá solo reiniciar.py. No ejecutes /opsx:apply.
```
```
/opsx:apply reiniciar-y-seed
Implementá las tasks en orden. Corré python reiniciar.py dos veces seguidas y mostrame el conteo de filas por tabla; probalo también sobre una base recién creada. No commitees.
```
- **Aviso al grupo cuando mergea**: a partir de acá cada uno corre `python reiniciar.py` para tener datos.

### [10] `pruebas-http-y-evidencia` — Andrés

- **Depende de**: `03`, `04`, `05`, `06`, `07`, `08`, `09`. **Desbloquea**: `11`. **Rama**: `feature/pruebas-http-y-evidencia`. **Revisa**: Mariano.
- **Toca**: `test/**`. **No toca código de la app**: si un caso falla, se reporta al dueño del módulo (quien corrige en una rama propia).

```
/opsx:propose pruebas-http-y-evidencia
Leé primero la sección [10] de CHANGES.md y la sección "Casos de prueba mínimos" del PDF docs/MiniTP_Cap1a4_Consigna.pdf.
Un archivo .http por caso (test/caso_C-01.http ... caso_C-09.http), cada uno con la respuesta esperada en un comentario, para correr después de python reiniciar.py. El caso C-08 lleva además test/caso_C-08.sql. Incluí test/evidencia_C-07.txt con las consultas de consola del detalle de un turno con una práctica y con tres.
Si un caso falla no corrijas código de la app: dejá registrado el fallo y a qué módulo pertenece.
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
No inventes reglas: lo no decidido está en DD-08 a DD-15 o es pregunta abierta. Tocá solo test/. No ejecutes /opsx:apply.
```
```
/opsx:apply pruebas-http-y-evidencia
Implementá las tasks en orden. Ejecutá cada caso contra la app levantada (después de python reiniciar.py) y mostrame la respuesta real de cada uno. No commitees.
```

### [11] `readme-y-entrega` — Facundo

- **Depende de**: `10`. **Rama**: `feature/readme-y-entrega`. **Revisa**: Andrés (y Mariano ejecuta los pasos).
- **Toca**: `README.md`.

```
/opsx:propose readme-y-entrega
Leé primero la sección [11] de CHANGES.md y los archivos de "Leer antes".
El README debe permitir levantar el proyecto desde cero: requisitos (Python 3.12+, PostgreSQL 16+), entorno virtual, pip install -r requirements.txt, copiar env.example a .env, crear la base, python reiniciar.py y uvicorn app.main:app.
Incluí la explicación en una o dos líneas de por qué turno_practica.turno_id no necesita índice propio (la PK compuesta ya tiene un índice con turno_id como primera columna), la tabla de endpoints, cómo correr los .http y el .sql, el enlace a test/evidencia_C-07.txt y la sección "Decisiones propias del equipo" con DD-08 a DD-15 (no presentarlas como reglas de la cátedra).
Todo en español. La spec debe tener al menos tres escenarios verificables (esperado, error de negocio y borde) y tasks.md debe indicar cómo se verifica cada uno.
Tocá solo README.md. No ejecutes /opsx:apply.
```
```
/opsx:apply readme-y-entrega
Escribí el README según las tasks. Después seguí cada paso literalmente y mostrame la salida de cada comando. No commitees.
```
- **Verificación final**: Mariano, en un entorno virtual nuevo y una base vacía, sigue el README sin conocimiento previo. Todo lo que no funcione se corrige antes de entregar.

---

## 6. Dónde se van a chocar en Git (y cómo evitarlo)

| Punto de choque | Cómo se evita |
|---|---|
| `CHANGES.md` (casillas `[x]`) | Cada uno marca **solo su línea**, al archivar. Si hay conflicto, es de una línea: se resuelve conservando ambas marcas. |
| `openspec/specs/` (se sincroniza al archivar) | Cada change tiene sus propias capacidades. Archivar **de a uno**, con `git pull` antes, y avisar al grupo cuando mergeás. |
| `app/main.py` | Lo deja completo `01` (los seis routers incluidos). Nadie más lo edita. |
| `requirements.txt`, `env.example`, `.gitignore` | Solo Mariano. Si necesitás una dependencia, se la pedís y la agrega en una rama aparte. |
| `AGENTS.md` y `CLAUDE.md` | Solo Mariano; siempre idénticos: `(Get-FileHash AGENTS.md).Hash -eq (Get-FileHash CLAUDE.md).Hash` debe dar `True`. |
| Los cuatro `models.py` | Solo Mariano (en `02`). Si un CRUD necesita una relación nueva, se pide. |
| El agente edita un archivo que no es tuyo | `git checkout -- <archivo>` antes de commitear, y reforzar en el prompt "tocá solo los archivos de este change". |

**Reglas generales**
- Un change a la vez por persona.
- Un PR por change, revisado por otra persona antes del merge.
- Commits convencionales (`feat(duenios): ...`, `fix(turnos): ...`, `docs: ...`). **El agente no commitea ni pushea**: lo hace cada uno.
- Nunca subir `.env`, `.venv/`, `__pycache__/` ni keys. Si una key se filtra al repo o a un chat, se **rota** (se borra y se genera otra).
- Cupo de modelo: una sesión nueva por change, pedidos cortos, archivos puntuales ("leé solo X"), y si el cupo se acaba se retoma en la sesión siguiente: el estado vive en `openspec/` y en Git.

---

## 7. Si algo sale mal

| Situación | Qué hacer |
|---|---|
| Un change que ya está mergeado tiene un error | El dueño abre `feature/fix-<tema>`, corrige y hace PR. No se reescribe un change archivado: se agrega un fix. |
| El dueño de un módulo se atrasa | Avisa **cuanto antes** en el grupo. Otro toma el siguiente change **de su propia lista** o revisa; nadie abre archivos ajenos sin avisar. |
| Un caso de `10` falla | Andrés lo reporta al dueño del módulo con la petición y la respuesta real. El dueño corrige en una rama propia. |
| Se agota el cupo del modelo | Cambiar de proveedor (OpenRouter con key propia de cada uno) o redactar a mano el artefacto que falta; el ciclo se retoma donde quedó. |
| Un change crece más de lo previsto | Partirlo **antes** de seguir, no a mitad de camino; avisar para actualizar `CHANGES.md`. |
| Conflicto en `CHANGES.md` | Mantener las dos marcas `[x]` y seguir. |

---

## 8. Checklist de entrega (lo corre Mariano, con los otros dos mirando)

- [ ] `main` tiene todos los changes mergeados y las 11 líneas de `CHANGES.md` en `[x]`.
- [ ] En un **entorno virtual nuevo** y una **base vacía**: `pip install -r requirements.txt` → `.env` desde `env.example` → `python reiniciar.py` → `uvicorn app.main:app` funcionan siguiendo solo el README.
- [ ] Los 9 casos de `test/` dan lo esperado; `test/evidencia_C-07.txt` existe y muestra la misma cantidad de consultas con 1 y con 3 prácticas.
- [ ] Todos los nombres de tablas y columnas coinciden con la tabla del PDF.
- [ ] El README explica por qué `turno_practica.turno_id` no lleva índice propio.
- [ ] `git ls-files` no contiene `.env`, `.venv`, `__pycache__` ni ninguna credencial.
- [ ] `AGENTS.md` y `CLAUDE.md` idénticos.
- [ ] Zip de entrega: `git archive --format=zip -o ..\entrega.zip HEAD` (no incluye `.env` ni `.git`).
