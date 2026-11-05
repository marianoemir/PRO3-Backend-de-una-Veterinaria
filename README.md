# PRO3 — Backend de una Veterinaria

API REST para una veterinaria de barrio: dueños, fichas, mascotas, catálogo de prácticas y turnos.
Construida con **FastAPI + SQLModel (async) + PostgreSQL 16+**. Solo backend: sin frontend, autenticación, Docker ni CI.

---

## Requisitos

| Requisito | Versión / detalle |
|---|---|
| Python | 3.12 o superior (`python --version` o `python3 --version`); en Windows, si `python` no responde, usá `py -3` |
| PostgreSQL | 16 o superior, con **pgAdmin** (viene con el instalador) |
| Git | opcional, solo para clonar |

> **No hace falta `psql` ni `createdb` en el `PATH`.** La base se crea desde pgAdmin; `psql` se menciona solo como alternativa.

---

## Puesta en marcha desde cero

Todos los comandos se ejecutan **desde la raíz del repositorio**.

### 1. Obtener el código

```bash
git clone https://github.com/marianoemir/PRO3-Backend-de-una-Veterinaria.git
cd PRO3-Backend-de-una-Veterinaria
```

### 2. Crear y activar el entorno virtual

Elegí el bloque de **tu** shell. En Windows el entorno virtual usa `Scripts/`; en Linux/macOS, `bin/`.

**PowerShell (Windows)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**CMD (Windows)**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**Git Bash (Windows)**

```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Si en Linux/macOS no existe el comando `python`, usá `python3` también para el resto de los pasos.

**Si PowerShell bloquea la activación** con `UnauthorizedAccess` (política de ejecución `Restricted`), no hace falta cambiar la configuración del sistema: en los pasos 3, 6 y 7 reemplazá `pip`, `python` y `uvicorn` por `.\.venv\Scripts\python.exe -m pip`, `.\.venv\Scripts\python.exe` y `.\.venv\Scripts\python.exe -m uvicorn`, respectivamente.

En Linux/macOS el equivalente es `.venv/bin/python`, y así con cada comando.

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Instala `fastapi[standard]` (incluye `uvicorn`), `sqlmodel`, `sqlalchemy[asyncio]`, `asyncpg` y `python-dotenv`.

### 4. Crear el archivo `.env`

El repositorio incluye `env.example` con la forma del valor. Copialo y completá tus credenciales:

**PowerShell**

```powershell
Copy-Item env.example .env
```

**CMD**

```bat
copy env.example .env
```

**Git Bash / Linux / macOS**

```bash
cp env.example .env
```

Después editá `.env` y reemplazá usuario y clave por los de tu PostgreSQL local:

```dotenv
DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/veterinaria
```

> `.env` está en `.gitignore`: **nunca** se versiona. No subas credenciales reales al repositorio.

### 5. Crear la base de datos `veterinaria`

**Con pgAdmin (camino recomendado, no requiere `psql`)**

1. Abrí pgAdmin y conectate a tu servidor local (`localhost:5432`).
2. Clic derecho sobre **Databases** → **Create** → **Database…**
3. En **Database** escribí `veterinaria` y presioná **Save**.

**Alternativa con `psql`** (solo si tenés los binarios en el `PATH`):

```bash
psql -U postgres -c "CREATE DATABASE veterinaria;"
# o
createdb -U postgres veterinaria
```

`reiniciar.py` no crea la base: solo borra y recrea **tablas** dentro de una base existente.

### 6. Crear el esquema y cargar el seed

```bash
python reiniciar.py
```

> ⚠️ **`reiniciar.py` borra todas las tablas y sus datos** de la base apuntada por `DATABASE_URL`, y luego las recrea con el seed mínimo. No lo apuntes a una base con datos que quieras conservar.

Salida esperada (la consola también imprime líneas INFO de SQLAlchemy por echo=True; lo importante es el resumen final):

```text
Reiniciando postgresql+asyncpg://usuario:***@localhost:5432/veterinaria (se borran todas las tablas y sus datos)
Reinicio completo. Conteos por tabla:
  duenio: 2
  ficha_duenio: 1
  mascota: 3
  practica: 4
  turno: 1
  turno_practica: 2
```

El seed deja: 2 dueños (Ana Gómez con ficha, Bruno Díaz sin ficha), 3 mascotas (Toby, Michi, Rocco), 4 prácticas (Consulta `15000.00`, Desparasitación `8000.00`, Vacuna antirrábica `12000.00`, Castración `35000.00`) y 1 turno con 2 prácticas. Los ids son fijos para que los ejemplos del enunciado funcionen tal cual: mascota `1` = Toby, práctica `1` = Consulta, práctica `3` = Vacuna antirrábica, y el próximo turno recibe `id = 2`.

### 7. Levantar la API

```bash
uvicorn app.main:app --reload
```

La API queda en <http://127.0.0.1:8000>:

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- Salud sin base: `GET /health/live` → `200 {"estado": "vivo"}`
- Salud con base: `GET /health/ready` → `200 {"estado": "listo", "base": "ok"}` (o `503` si PostgreSQL no responde)

Para detener el servidor: `Ctrl + C`.

---

## Endpoints

Solo existen estas rutas (no se agregaron endpoints fuera de la consigna).

| Método | Ruta | Cuerpo | Respuesta | Códigos |
|---|---|---|---|---|
| GET | `/health/live` | — | `{"estado": "vivo"}` | 200 |
| GET | `/health/ready` | — | `{"estado": "listo", "base": "ok"}` | 200, 503 |
| POST | `/duenios/` | `DuenioCreate` | dueño creado | 201, 409, 422 |
| GET | `/duenios/{id}` | — | dueño con su ficha | 200, 404, 422 |
| PATCH | `/duenios/{id}` | `DuenioUpdate` | dueño con su ficha | 200, 404, 409, 422 |
| DELETE | `/duenios/{id}` | — | — | 204, 404, 409, 422 |
| POST | `/duenios/{id}/ficha` | `FichaCreate` | ficha creada | 201, 404, 409, 422 |
| GET | `/duenios/{id}/mascotas` | — | lista de mascotas | 200, 404, 422 |
| POST | `/mascotas/` | `MascotaCreate` | mascota creada | 201, 409, 422 |
| GET | `/mascotas/?page=&size=` | — | envoltorio paginado | 200, 422 |
| GET | `/mascotas/{id}` | — | mascota con su dueño | 200, 404, 422 |
| POST | `/practicas/` | `PracticaCreate` | práctica creada | 201, 409, 422 |
| GET | `/practicas/` | — | catálogo de prácticas | 200 |
| POST | `/turnos/` | `TurnoCreate` | turno con mascota y prácticas | 201, 409, 422 |
| GET | `/turnos/{id}` | — | turno con mascota y prácticas | 200, 404, 422 |
| DELETE | `/turnos/{id}` | — | — | 204, 404, 422 |
| GET | `/laboratorio/stock/{vacuna}` | — | `{"vacuna": ..., "stock": ...}` | 200 |

Códigos: **201** al crear, **204** al borrar, **404** si el recurso no existe, **409** si la base rechaza la escritura (email o nombre repetido, FK inexistente, baja con dependencias), **422** si el cuerpo o los parámetros no cumplen el contrato, **503** si la base no está disponible en `/health/ready`.

### Paginación de mascotas

`GET /mascotas/?page=&size=` responde:

```json
{ "items": [], "total": 0, "page": 1, "size": 20, "pages": 0 }
```

`size` vale **20** por defecto y acepta de **1 a 100**. Una página más allá de `pages` responde **422**. La primera página siempre responde 200, aunque la base esté vacía.

### Alta de turno (ejemplo)

No se envían precios ni total: los toma el servidor del catálogo y los congela en el turno.

```json
{
  "mascota_id": 1,
  "fecha": "2026-11-12T10:30:00-03:00",
  "motivo": "Control anual",
  "practicas": [{ "practica_id": 1 }, { "practica_id": 3 }]
}
```

Respuesta `201` (la fecha sale en UTC):

```json
{
  "id": 2,
  "fecha": "2026-11-12T13:30:00Z",
  "motivo": "Control anual",
  "total": "27000.00",
  "mascota": { "id": 1, "nombre": "Toby", "especie": "perro" },
  "practicas": [
    { "practica_id": 1, "nombre": "Consulta", "precio_unitario": "15000.00" },
    { "practica_id": 3, "nombre": "Vacuna antirrábica", "precio_unitario": "12000.00" }
  ]
}
```

---

## Modelo de datos e índices

Seis tablas: `duenio`, `ficha_duenio`, `mascota`, `practica`, `turno` y `turno_practica`. Las garantías (UNIQUE, CHECK, FK) las hace cumplir PostgreSQL, no consultas previas desde la aplicación.

**¿Por qué `turno_practica.turno_id` no necesita índice propio?**
La clave primaria compuesta `(turno_id, practica_id)` ya crea un índice B-tree con `turno_id` como primera columna, que PostgreSQL usa para buscar por turno; `practica_id` no es la primera columna de esa clave, así que no se beneficia de ese índice y por eso sí lleva uno propio (`ix_turno_practica_practica_id`).

---

## Casos de prueba (`test/`)

Todos los casos asumen la base recién reiniciada:

```bash
python reiniciar.py
```

| Caso | Qué verifica | Resultado esperado |
|---|---|---|
| `test/caso_C-01.http` | Parámetro de ruta no entero | `GET /duenios/abc` → **422** |
| `test/caso_C-02.http` | Unicidad de email y de nombre de práctica | **409** con mensaje propio |
| `test/caso_C-03.http` | Una sola ficha por dueño | 1.ª → **201**, 2.ª → **409** |
| `test/caso_C-04.http` | FK inexistente en mascota y en turno | **409**; el turno inválido no deja filas |
| `test/caso_C-05.http` | Borrado con dependencias | dueño con mascotas → **409**; turno → **204** sin prácticas |
| `test/caso_C-06.http` | Alta de turno transaccional | **201**, `total` `"27000.00"` con precios copiados |
| `test/caso_C-07.http` | Detalle de turno sin N+1 | misma cantidad de `SELECT` con 1 y con 3 prácticas |
| `test/caso_C-08.sql` | CHECK de precio en la base | `UPDATE` a precio 0 → error **23514**, 0 filas |
| `test/caso_C-09.http` | Laboratorio sin bloquear el event loop | `/health/live` responde de inmediato |

### Cómo correr los `.http`

Se usan con la extensión **[REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)** de VS Code (es la herramienta que asumen los archivos del repo):

1. Instalá la extensión **REST Client** en VS Code.
2. Abrí el archivo `test/caso_C-0X.http` y presioná **Send Request** sobre cada bloque (o `Ctrl + Alt + R`).
3. Cada archivo declara `@baseUrl = http://localhost:8000` y deja la respuesta esperada en un comentario.

> **C-09 no se puede medir con REST Client**, porque ejecuta las peticiones en serie. La nota al final de `test/caso_C-09.http` indica cómo medir la concurrencia real desde PowerShell: lanzar las tres consultas al laboratorio con `Start-Job` y medir el endpoint de salud con `Measure-Command`.

```powershell
Start-Job { curl.exe -s http://localhost:8000/laboratorio/stock/rabia } | Out-Null
Start-Job { curl.exe -s http://localhost:8000/laboratorio/stock/parvo } | Out-Null
Start-Job { curl.exe -s http://localhost:8000/laboratorio/stock/moquillo } | Out-Null
Start-Sleep -Milliseconds 300
Measure-Command { curl.exe -s http://localhost:8000/health/live }
```

El health debe responder en ~0 ms mientras cada consulta al laboratorio tarda ~1000 ms.

### Cómo correr el `.sql` (caso C-08)

**Con pgAdmin:** abrí el **Query Tool** sobre la base `veterinaria` (Tools → Query Tool), cargá `test/caso_C-08.sql` con el botón de abrir archivo y ejecutalo con **F5** o el botón ▶. Esperado: `ERROR: new row for relation "practica" violates check constraint ... (SQLSTATE 23514)` y 0 filas modificadas.

**Con `psql`** (si está en el `PATH`):

```bash
psql -U postgres -d veterinaria -f test/caso_C-08.sql
```

Después de ejecutarlo, `test/caso_C-08.http` confirma que la práctica 1 sigue con precio `"15000.00"`.

### Evidencia del caso C-07

[`test/evidencia_C-07.txt`](test/evidencia_C-07.txt) es el fragmento de consola (`echo=True`) con el detalle de un turno con **1 práctica** y con **3 prácticas**: en ambos casos se ejecutan los mismos **2 `SELECT`**, uno para el turno con su mascota y otro para las prácticas con su catálogo. Es la prueba de que la lectura no cae en N+1.

---

## Decisiones propias del equipo

> La consigna no define estos puntos. Los resolvió el equipo para no bloquear la entrega: **son decisiones nuestras, no reglas de la cátedra**. Están registradas en `knowledge-base/09_decisiones_y_supuestos.md` y en el `design.md` del change que las usa.

| ID | Decisión | Efecto observable |
|---|---|---|
| DD-08 | `DuenioUpdate` acepta `nombre` y `email`, ambos opcionales, y el `PATCH` aplica solo lo enviado (`exclude_unset`). | `PATCH` con un solo campo no borra el otro; `{}` responde 200 sin cambios; email en colisión → 409. |
| DD-09 | El email no se normaliza: se guarda tal cual llega. | `A@x.com` y `a@x.com` son distintos para el `UNIQUE` de PostgreSQL. |
| DD-10 | `GET /duenios/{id}/mascotas` devuelve una lista simple. | `[]` si el dueño no tiene mascotas (200); dueño inexistente → 404; el envoltorio paginado es solo para `GET /mascotas/`. |
| DD-11 | El detalle de turno no incluye id de fila de `turno_practica`. | Cada práctica trae `practica_id`, `nombre` y `precio_unitario`; `turno_practica` no tiene columna `id`. |
| DD-12 | Validaciones mínimas en los DTO. | Los textos obligatorios (`nombre`, `email`, `especie`, `motivo`, `telefono`, `direccion`) no pueden ser vacíos; no se valida fecha pasada, turnos duplicados ni formato de email. |
| DD-13 | `ON DELETE` no especificado queda en el default `NO ACTION` (ficha, turno→mascota, práctica en turno). | No se agregó `CASCADE` donde la consigna no lo pide; la base rechaza el borrado. |
| DD-14 | `GET /health/ready` informa el estado de la base. | 200 `{"estado": "listo", "base": "ok"}` / 503 `{"estado": "no_disponible", "base": "error"}`. |
| DD-15 | Paginación y organización de `test/`. | `page` y `size` por query string, listados ordenados por `id`, un `.http` por caso más `caso_C-08.sql`, base `veterinaria` en `env.example`. |

**Tomadas durante la implementación** (registradas en los `design.md` archivados):

- **`page` es 1-based** en `GET /mascotas/` (`Query(1, ge=1)`). Se deriva del ejemplo del envoltorio (`"page": 1`) y de "la primera página"; `page=0` o negativo responde **422**.
- **Un dueño con ficha y sin mascotas tampoco se puede borrar**: `DELETE /duenios/{id}` responde **409** porque `ficha_duenio.duenio_id` quedó en `NO ACTION` (DD-13 / IN-03). No se borra la ficha antes para habilitar la baja: sería inventar una cascada que la consigna no autoriza.
- **`PATCH /duenios/{id}` con `null` explícito responde 422**: `nombre` y `email` son opcionales (se pueden omitir) pero no pueden enviarse como `null`, porque las columnas son `NOT NULL`; lo rechaza el DTO antes de llegar a la base.

---

## Problemas frecuentes

| Mensaje | Causa | Solución |
|---|---|---|
| `FATAL: DATABASE_URL no está definida. Copiá env.example a .env y configurá la conexión.` | No existe `.env` o le falta `DATABASE_URL`. El arranque aborta con código 1. | Copiá `env.example` a `.env` (paso 4) y completá la URL. |
| `ERROR: no se pudo reiniciar la base ...` | La base `veterinaria` no existe o las credenciales de `DATABASE_URL` son incorrectas. El script revierte la transacción y sale con código 2. | Creá la base desde pgAdmin (paso 5) y revisá usuario, clave y puerto en `.env`. |
| `python -m venv .venv` no muestra nada y después `Activate.ps1` dice que no se reconoce (no existe la carpeta `.venv`) | En Windows, el primer `python` del `PATH` puede ser un alias del instalador que no hace nada y falla en silencio; las dependencias terminan instalándose en el Python global. | Usá el lanzador con versión explícita: `py -3.13 -m venv .venv` (o `py -3.12`). Comprobá que `Test-Path .\.venv\Scripts\Activate.ps1` dé `True` y que `where.exe python` devuelva primero el de `.venv`. |
| `[Errno 10048] ... solo se permite un uso de cada dirección de socket` | El puerto 8000 ya está ocupado por otra API que sigue corriendo. | Frená la otra instancia con Ctrl+C, o levantá esta en otro puerto: `uvicorn app.main:app --port 8001`. |
| `Reiniciando ... (se borran todas las tablas y sus datos)` | Aviso normal de `reiniciar.py`: destruye el contenido de la base apuntada. | Confirmá que `DATABASE_URL` apunta a la base de desarrollo, no a una con datos reales. |

---

## Checklist de entrega

- [x] Código fuente completo en `app/` (seis módulos: `health`, `duenios`, `mascotas`, `practicas`, `turnos`, `laboratorio`).
- [x] `requirements.txt` con las dependencias y sus versiones fijadas.
- [x] `env.example` sin secretos (`.env` no versionado).
- [x] `reiniciar.py` que recrea el esquema y carga el seed.
- [x] `test/` con los nueve casos (`caso_C-01.http` … `caso_C-09.http`), `caso_C-08.sql` y `evidencia_C-07.txt`.
- [x] `README.md` con la puesta en marcha y las decisiones propias.
- [x] Sin credenciales reales en el repositorio (`git ls-files .env` no devuelve nada).

---

## Estructura del proyecto

```text
app/
├── main.py                 # FastAPI + lifespan (motor y fábrica de sesiones)
├── core/
│   ├── config.py           # carga .env y expone DATABASE_URL
│   └── database.py         # motor async, fábrica de sesiones, get_session
└── modules/
    ├── health/             # /health/live y /health/ready
    ├── duenios/            # dueños y fichas
    ├── mascotas/           # mascotas y paginación
    ├── practicas/          # catálogo de prácticas
    ├── turnos/             # turnos y turno_practica
    └── laboratorio/        # stock (cliente sync ejecutado en un hilo)
reiniciar.py                # drop_all + create_all + seed
test/                       # casos C-01..C-09, C-08.sql y evidencia C-07
```
