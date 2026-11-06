# PRO3 — Backend de una Veterinaria

**Grupo:** Lobos Solitarios

**Integrantes:** Mariano Chirino, Andrés Fabre, Facundo Quiroga.

API REST para una veterinaria de barrio: dueños, fichas, mascotas, catálogo de prácticas y turnos.
Construida con **FastAPI + SQLModel (async) + PostgreSQL 16+**. Solo backend: sin frontend, autenticación, Docker ni CI.

---

## Requisitos

| Requisito | Versión / detalle |
|---|---|
| Python | 3.12 o superior; probado con 3.12 y 3.13 (`python --version` o `python3 --version`); en Windows se usa `py -3.13` (o `py -3.12`) para crear el entorno (el comando `python` puede ser un alias roto) |
| PostgreSQL | 16 o superior, con **pgAdmin** (viene con el instalador) |
| Git | opcional, solo para clonar (sin Git se puede descargar el ZIP, ver paso 1 de tu guía) |

> **No hace falta `psql` ni `createdb` en el `PATH`.** La base se crea desde pgAdmin (Paso 0); `psql` se menciona solo como alternativa.

---

## Puesta en marcha desde cero

Elegí **una** terminal y seguí **solo su guía**, de arriba abajo, sin saltearte pasos:

| Si usás... | Seguí la guía | Cómo reconocerla |
|---|---|---|
| Windows con **PowerShell** (recomendada) | [Guía A](#guía-a--windows-powershell) | el prompt empieza con `PS`, por ejemplo `PS C:\Proyectos>` |
| Windows con **CMD** (Símbolo del sistema) | [Guía B](#guía-b--windows-cmd) | el prompt es solo la ruta y `>`, por ejemplo `C:\Proyectos>` |
| **Linux** o **macOS** (también Git Bash en Windows) | [Guía C](#guía-c--linux--macos) | el prompt termina en `$` o `%` |

> **No mezcles terminales.** Los comandos de una guía no funcionan en otra: `Copy-Item` y `Activate.ps1` solo existen en PowerShell; `copy` y `activate.bat`, solo en CMD; `cp` y `source`, solo en Linux/macOS. La terminal integrada de VS Code puede abrir cualquiera de las tres: mirá el prompt antes de pegar.

Cada bloque de código se pega **entero y tal cual**, salvo donde el texto diga que tenés que cambiar algo (tu clave de PostgreSQL). Los comandos se ejecutan **desde la raíz del repositorio**, que es la carpeta que se crea al clonar.

### Paso 0 — Preparar PostgreSQL y crear la base `veterinaria` (una sola vez)

`reiniciar.py` **no crea la base**: solo borra y recrea las **tablas** dentro de una base que ya exista. Por eso la base se crea antes de cualquier otro paso. Este paso es igual sin importar qué terminal uses después.

**0.a — Tener PostgreSQL instalado y andando.** Hace falta PostgreSQL 16 o superior. Si no lo tenés, descargá el instalador desde <https://www.postgresql.org/download/> (en Windows, el instalador gráfico). Durante la instalación:

- dejá tildado **pgAdmin 4** (es la herramienta con ventanas para manejar la base);
- elegí una **contraseña** para el usuario `postgres` y **anotala**: es la que después va en el archivo `.env`;
- dejá el puerto **5432**.

Para comprobar que el servidor está andando en Windows: Inicio → escribí `services.msc` → Enter, y buscá el servicio `postgresql-x64-17` (el número es tu versión). Tiene que decir **En ejecución**; si no, clic derecho → **Iniciar**.

**0.b — Crear la base con pgAdmin (recomendado en Windows).**

1. Inicio → escribí `pgAdmin 4` → Enter. Tarda unos segundos en abrir. La primera vez puede pedirte una **contraseña maestra**: es propia de pgAdmin (no la de PostgreSQL); elegí una y recordala.
2. En el panel izquierdo desplegá **Servers**. Aparece un servidor llamado `PostgreSQL 17` (el número es tu versión). Hacé clic sobre él: te pide la contraseña del usuario `postgres`, la que elegiste al instalar.
3. Una vez conectado, desplegá el servidor, hacé **clic derecho sobre Databases** → **Create** → **Database…**
4. En la pestaña **General**, en el campo **Database**, escribí `veterinaria`. Dejá todo lo demás como está y presioná **Save**.
5. Comprobá que `veterinaria` aparece dentro de **Databases**, en el panel izquierdo (si no se ve, clic derecho sobre **Databases** → **Refresh**).

**0.c — Alternativa por terminal con `psql`** (si no querés usar pgAdmin). Te pide la contraseña de `postgres`:

PowerShell (cambiá `17` por tu versión; `dir "C:\Program Files\PostgreSQL"` te muestra cuál tenés):

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE veterinaria;"
```

CMD:

```bat
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE veterinaria;"
```

Linux:

```bash
sudo -u postgres psql -c "CREATE DATABASE veterinaria;"
```

macOS (Homebrew o Postgres.app):

```bash
createdb veterinaria
```

En Linux y macOS el usuario y la clave de PostgreSQL pueden ser distintos de `postgres`/`TU_CLAVE` (por ejemplo, en macOS suele ser tu usuario del sistema, sin clave): ajustalos en el paso 4. Si `psql` ya está en el `PATH` de tu terminal, alcanza con `psql -U postgres -c "CREATE DATABASE veterinaria;"`. Para ver qué bases existen: `psql -U postgres -l`.

**Si la base `veterinaria` ya existe** (pgAdmin o `psql` avisan `ya existe`), no es un error del proyecto: no hace falta crearla, seguí con la guía. Ojo: `reiniciar.py` borra las tablas de esa base. Si tiene datos que querés conservar, creá otra con otro nombre (por ejemplo `veterinaria_test`) y poné ese nombre al final de `DATABASE_URL` en el paso 4.

---

### Guía A — Windows PowerShell

Abrí **PowerShell**: menú Inicio, escribí `PowerShell` y Enter. El prompt tiene que empezar con `PS`. Si empieza sin `PS`, estás en CMD: usá la [Guía B](#guía-b--windows-cmd).

#### 1. Obtener el código

Creá la carpeta donde vas a guardar el proyecto y entrá en ella (si la carpeta ya existe, el aviso de error de `mkdir` es inofensivo):

```powershell
mkdir C:\Proyectos
cd C:\Proyectos
```

Cloná el repositorio y entrá a la carpeta del proyecto:

```powershell
git clone https://github.com/marianoemir/PRO3-Backend-de-una-Veterinaria.git
cd PRO3-Backend-de-una-Veterinaria
```

`git clone` **crea una carpeta nueva** llamada `PRO3-Backend-de-una-Veterinaria` dentro de la carpeta donde estás, y el `cd` entra en ella. Esa es la **raíz del repositorio**: todos los pasos siguientes se ejecutan ahí, **en esta misma terminal** (si la cerrás, volvé a abrirla y entrá otra vez con `cd`).

Comprobá que estás en el lugar correcto. Tiene que listar, entre otros, `README.md`, `requirements.txt`, `reiniciar.py` y `env.example`:

```powershell
dir
```

> **Sin Git:** en la página del repositorio en GitHub, botón verde **Code** → **Download ZIP**. Descomprimilo, abrí la terminal dentro de la carpeta que contiene `requirements.txt` y seguí desde el paso 2.

#### 2. Crear y activar el entorno virtual

Verificá la versión de Python con el lanzador de Windows:

```powershell
py -0p
py -3.13 --version
```

`py -0p` lista los Pythons instalados y `py -3.13 --version` tiene que mostrar `Python 3.13.x`. Si solo tenés 3.12, usá `py -3.12` en lugar de `py -3.13` en todos los comandos de esta guía. **No uses `py -3` a secas**: elige la versión más nueva que tengas (por ejemplo 3.14), y el proyecto está probado con 3.12 y 3.13. Si no muestra nada o `py` no se reconoce, mirá [Problemas frecuentes](#problemas-frecuentes): en Windows el comando `python` suele ser un alias roto que falla en silencio, y por eso en esta guía el entorno se crea con `py`, el lanzador oficial de Python para Windows.

Creá el entorno virtual y comprobá que quedó bien armado:

```powershell
py -3.13 -m venv .venv
Test-Path .\.venv\Scripts\Activate.ps1
```

`Test-Path` tiene que responder **`True`**. Si responde `False`, el entorno quedó incompleto: recrealo y volvé a comprobar:

```powershell
py -3.13 -m venv .venv --clear
Test-Path .\.venv\Scripts\Activate.ps1
```

Activalo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Queda activo cuando el prompt empieza con **`(.venv)`**, por ejemplo `(.venv) PS C:\Proyectos\PRO3-Backend-de-una-Veterinaria>`. Si no aparece `(.venv)`, no está activo.

**Si PowerShell bloquea la activación** con `UnauthorizedAccess` (política de ejecución `Restricted`), no hace falta cambiar la configuración del sistema: en los pasos 3, 5 y 6 reemplazá `pip`, `python` y `uvicorn` por `.\.venv\Scripts\python.exe -m pip`, `.\.venv\Scripts\python.exe` y `.\.venv\Scripts\python.exe -m uvicorn`, respectivamente. (La otra salida es usar la [Guía B](#guía-b--windows-cmd).)

#### 3. Instalar las dependencias

```powershell
pip install -r requirements.txt
```

Tiene que mostrar líneas `Collecting ...` y terminar con `Successfully installed ...` (el aviso `A new release of pip is available` es informativo y se ignora). Si en cambio dice `Requirement already satisfied` en todas las líneas, el entorno **no** está activo: volvé al paso 2. Instala `fastapi[standard]` (incluye `uvicorn`), `sqlmodel`, `sqlalchemy[asyncio]`, `asyncpg` y `python-dotenv`.

#### 4. Crear el archivo `.env`

Se crea con **un solo comando**, así no hay editor de por medio ni riesgo de que se cuele un espacio al principio. Reemplazá `TU_CLAVE` por la contraseña de tu usuario de PostgreSQL (`postgres` es el usuario por defecto; si tu usuario es otro, cambiá también ese texto) y, si en el Paso 0 usaste otro nombre de base, cambiá `veterinaria` por ese nombre. Dejá las comillas simples: evitan problemas con caracteres como `$`.

```powershell
Set-Content -Path .env -Value 'DATABASE_URL=postgresql+asyncpg://postgres:TU_CLAVE@localhost:5432/veterinaria' -Encoding ascii
Get-Content .env
```

Tiene que mostrar **exactamente una línea** que empieza con `DATABASE_URL=`, sin nada antes. Si tu contraseña tiene caracteres especiales, no se puede poner tal cual en la URL: escribilos codificados (`@` → `%40`, `:` → `%3A`, `/` → `%2F`, `#` → `%23`, `?` → `%3F`, `%` → `%25`).

**Alternativa con editor** (si preferís editar a mano): copiá el ejemplo con `Copy-Item env.example .env`, abrilo con `notepad .env`, dejá solo la línea `DATABASE_URL=...` empezando en la primera columna (sin espacios ni comillas), guardá con `Ctrl+S` y **cerrá el Bloc de notas por completo** (todas sus pestañas; si queda abierto, el prompt puede no volver). Comprobá con `Get-Content .env`.

> `.env` está en `.gitignore`: **nunca** se versiona. No subas credenciales reales al repositorio.

#### 5. Crear el esquema y cargar el seed

```powershell
python reiniciar.py
```

> ⚠️ **`reiniciar.py` borra todas las tablas y sus datos** de la base apuntada por `DATABASE_URL`, y luego las recrea con el seed mínimo. No lo apuntes a una base con datos que quieras conservar.

Salida esperada (la consola también imprime líneas INFO de SQLAlchemy por `echo=True`; lo importante es el resumen final):

```text
Reiniciando postgresql+asyncpg://postgres:***@localhost:5432/veterinaria (se borran todas las tablas y sus datos)
Reinicio completo. Conteos por tabla:
  duenio: 2
  ficha_duenio: 1
  mascota: 3
  practica: 4
  turno: 1
  turno_practica: 2
```

El seed deja: 2 dueños (Ana Gómez con ficha, Bruno Díaz sin ficha), 3 mascotas (Toby, Michi, Rocco), 4 prácticas (Consulta `15000.00`, Desparasitación `8000.00`, Vacuna antirrábica `12000.00`, Castración `35000.00`) y 1 turno con 2 prácticas. Los ids son fijos para que los ejemplos del enunciado funcionen tal cual: mascota `1` = Toby, práctica `1` = Consulta, práctica `3` = Vacuna antirrábica, y el próximo turno recibe `id = 2`. Si falla, mirá la tabla de [Problemas frecuentes](#problemas-frecuentes).

#### 6. Levantar la API

```powershell
uvicorn app.main:app --reload
```

La terminal queda **ocupada** mostrando el log del servidor (es lo normal: no la cierres). Cuando veas `Application startup complete`, la API está lista en <http://127.0.0.1:8000>:

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- Salud sin base: `GET /health/live` → `200 {"estado": "vivo"}`
- Salud con base: `GET /health/ready` → `200 {"estado": "listo", "base": "ok"}` (o `503` si PostgreSQL no responde)

**Dejá la API corriendo mientras hacés las pruebas**: los casos de `test/` le mandan peticiones y fallan con `The connection was rejected` si está apagada. Para correr otros comandos con la API levantada, abrí **una segunda terminal** en la misma carpeta (o mandá las peticiones desde VS Code con REST Client, que no necesita terminal). Recién cuando termines de probar, frená el servidor con `Ctrl + C`.

**Siguiente:** probá los endpoints con los casos de la sección [Casos de prueba](#casos-de-prueba-test).

---

### Guía B — Windows CMD

Abrí **CMD**: menú Inicio, escribí `cmd` y Enter. El prompt es la ruta seguida de `>`, sin `PS` al principio. Si empieza con `PS`, estás en PowerShell: usá la [Guía A](#guía-a--windows-powershell).

#### 1. Obtener el código

Creá la carpeta donde vas a guardar el proyecto y entrá en ella (si la carpeta ya existe, el aviso de error de `mkdir` es inofensivo; `cd /d` también cambia de unidad si hace falta):

```bat
mkdir C:\Proyectos
cd /d C:\Proyectos
```

Cloná el repositorio y entrá a la carpeta del proyecto:

```bat
git clone https://github.com/marianoemir/PRO3-Backend-de-una-Veterinaria.git
cd PRO3-Backend-de-una-Veterinaria
```

`git clone` **crea una carpeta nueva** llamada `PRO3-Backend-de-una-Veterinaria` dentro de la carpeta donde estás, y el `cd` entra en ella. Esa es la **raíz del repositorio**: todos los pasos siguientes se ejecutan ahí, **en esta misma terminal** (si la cerrás, volvé a abrirla y entrá otra vez con `cd`).

Comprobá que estás en el lugar correcto. Tiene que listar, entre otros, `README.md`, `requirements.txt`, `reiniciar.py` y `env.example`:

```bat
dir
```

> **Sin Git:** en la página del repositorio en GitHub, botón verde **Code** → **Download ZIP**. Descomprimilo, abrí la terminal dentro de la carpeta que contiene `requirements.txt` y seguí desde el paso 2.

#### 2. Crear y activar el entorno virtual

Verificá la versión de Python con el lanzador de Windows:

```bat
py -0p
py -3.13 --version
```

`py -0p` lista los Pythons instalados y `py -3.13 --version` tiene que mostrar `Python 3.13.x`. Si solo tenés 3.12, usá `py -3.12` en lugar de `py -3.13` en todos los comandos de esta guía. **No uses `py -3` a secas**: elige la versión más nueva que tengas (por ejemplo 3.14), y el proyecto está probado con 3.12 y 3.13. Si no muestra nada o `py` no se reconoce, mirá [Problemas frecuentes](#problemas-frecuentes): en Windows el comando `python` suele ser un alias roto que falla en silencio, y por eso en esta guía el entorno se crea con `py`, el lanzador oficial de Python para Windows.

Creá el entorno virtual y comprobá que quedó bien armado:

```bat
py -3.13 -m venv .venv
if exist .venv\Scripts\activate.bat (echo OK) else (echo FALTA)
```

Tiene que responder **`OK`**. Si responde `FALTA`, el entorno quedó incompleto: recrealo y volvé a comprobar:

```bat
py -3.13 -m venv .venv --clear
if exist .venv\Scripts\activate.bat (echo OK) else (echo FALTA)
```

Activalo:

```bat
.venv\Scripts\activate.bat
```

Queda activo cuando el prompt empieza con **`(.venv)`**, por ejemplo `(.venv) C:\Proyectos\PRO3-Backend-de-una-Veterinaria>`. Si no aparece `(.venv)`, no está activo.

#### 3. Instalar las dependencias

```bat
pip install -r requirements.txt
```

Tiene que mostrar líneas `Collecting ...` y terminar con `Successfully installed ...` (el aviso `A new release of pip is available` es informativo y se ignora). Si en cambio dice `Requirement already satisfied` en todas las líneas, el entorno **no** está activo: volvé al paso 2. Instala `fastapi[standard]` (incluye `uvicorn`), `sqlmodel`, `sqlalchemy[asyncio]`, `asyncpg` y `python-dotenv`.

#### 4. Crear el archivo `.env`

Se crea con **un solo comando**, así no hay editor de por medio ni riesgo de que se cuele un espacio al principio. Reemplazá `TU_CLAVE` por la contraseña de tu usuario de PostgreSQL (`postgres` es el usuario por defecto; si tu usuario es otro, cambiá también ese texto) y, si en el Paso 0 usaste otro nombre de base, cambiá `veterinaria` por ese nombre. No pongas un espacio antes de `> .env`: el comando de arriba ya está armado para que no quede ninguno.

```bat
(echo DATABASE_URL=postgresql+asyncpg://postgres:TU_CLAVE@localhost:5432/veterinaria)> .env
type .env
```

Tiene que mostrar **exactamente una línea** que empieza con `DATABASE_URL=`, sin nada antes. Si tu contraseña tiene caracteres especiales, no se puede poner tal cual en la URL: escribilos codificados (`@` → `%40`, `:` → `%3A`, `/` → `%2F`, `#` → `%23`, `?` → `%3F`, `%` → `%25`).

**Alternativa con editor** (si preferís editar a mano): copiá el ejemplo con `copy env.example .env`, abrilo con `notepad .env`, dejá solo la línea `DATABASE_URL=...` empezando en la primera columna (sin espacios ni comillas), guardá con `Ctrl+S` y cerrá el Bloc de notas por completo. Comprobá con `type .env`. **Si tu contraseña tiene `&`, `^` o `%`, usá esta alternativa** en lugar del comando de arriba.

> `.env` está en `.gitignore`: **nunca** se versiona. No subas credenciales reales al repositorio.

#### 5. Crear el esquema y cargar el seed

```bat
python reiniciar.py
```

> ⚠️ **`reiniciar.py` borra todas las tablas y sus datos** de la base apuntada por `DATABASE_URL`, y luego las recrea con el seed mínimo. No lo apuntes a una base con datos que quieras conservar.

Salida esperada (la consola también imprime líneas INFO de SQLAlchemy por `echo=True`; lo importante es el resumen final):

```text
Reiniciando postgresql+asyncpg://postgres:***@localhost:5432/veterinaria (se borran todas las tablas y sus datos)
Reinicio completo. Conteos por tabla:
  duenio: 2
  ficha_duenio: 1
  mascota: 3
  practica: 4
  turno: 1
  turno_practica: 2
```

El seed deja: 2 dueños (Ana Gómez con ficha, Bruno Díaz sin ficha), 3 mascotas (Toby, Michi, Rocco), 4 prácticas (Consulta `15000.00`, Desparasitación `8000.00`, Vacuna antirrábica `12000.00`, Castración `35000.00`) y 1 turno con 2 prácticas. Los ids son fijos para que los ejemplos del enunciado funcionen tal cual: mascota `1` = Toby, práctica `1` = Consulta, práctica `3` = Vacuna antirrábica, y el próximo turno recibe `id = 2`. Si falla, mirá la tabla de [Problemas frecuentes](#problemas-frecuentes).

#### 6. Levantar la API

```bat
uvicorn app.main:app --reload
```

La terminal queda **ocupada** mostrando el log del servidor (es lo normal: no la cierres). Cuando veas `Application startup complete`, la API está lista en <http://127.0.0.1:8000>:

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- Salud sin base: `GET /health/live` → `200 {"estado": "vivo"}`
- Salud con base: `GET /health/ready` → `200 {"estado": "listo", "base": "ok"}` (o `503` si PostgreSQL no responde)

**Dejá la API corriendo mientras hacés las pruebas**: los casos de `test/` le mandan peticiones y fallan con `The connection was rejected` si está apagada. Para correr otros comandos con la API levantada, abrí **una segunda terminal** en la misma carpeta (o mandá las peticiones desde VS Code con REST Client, que no necesita terminal). Recién cuando termines de probar, frená el servidor con `Ctrl + C`.

**Siguiente:** probá los endpoints con los casos de la sección [Casos de prueba](#casos-de-prueba-test).

---

### Guía C — Linux / macOS

Abrí la aplicación **Terminal**. (En **Git Bash** de Windows los pasos son los mismos con tres cambios: usá `python` en lugar de `python3`, activá con `source .venv/Scripts/activate` y editá `.env` con `notepad .env`.)

#### 1. Obtener el código

Creá la carpeta donde vas a guardar el proyecto y entrá en ella:

```bash
mkdir -p ~/Proyectos
cd ~/Proyectos
```

Cloná el repositorio y entrá a la carpeta del proyecto:

```bash
git clone https://github.com/marianoemir/PRO3-Backend-de-una-Veterinaria.git
cd PRO3-Backend-de-una-Veterinaria
```

`git clone` **crea una carpeta nueva** llamada `PRO3-Backend-de-una-Veterinaria` dentro de la carpeta donde estás, y el `cd` entra en ella. Esa es la **raíz del repositorio**: todos los pasos siguientes se ejecutan ahí, **en esta misma terminal** (si la cerrás, volvé a abrirla y entrá otra vez con `cd`).

Comprobá que estás en el lugar correcto. Tiene que listar, entre otros, `README.md`, `requirements.txt`, `reiniciar.py` y `env.example`:

```bash
ls
```

> **Sin Git:** en la página del repositorio en GitHub, botón verde **Code** → **Download ZIP**. Descomprimilo, abrí la terminal dentro de la carpeta que contiene `requirements.txt` y seguí desde el paso 2.

#### 2. Crear y activar el entorno virtual

Verificá la versión de Python (tiene que ser 3.12 o superior):

```bash
python3 --version
```

Creá el entorno virtual y comprobá que quedó bien armado:

```bash
python3 -m venv .venv
ls .venv/bin/activate
```

`ls` tiene que mostrar `.venv/bin/activate`. Si dice `No such file or directory`, en Debian/Ubuntu falta el paquete del entorno virtual: instalalo con `sudo apt install python3-venv`, borrá la carpeta con `rm -rf .venv` y repetí los dos comandos.

Activalo:

```bash
source .venv/bin/activate
```

Queda activo cuando el prompt empieza con **`(.venv)`**. Dentro del entorno activo, `python` y `pip` ya apuntan al entorno (no hace falta `python3` en los pasos siguientes).

#### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Tiene que mostrar líneas `Collecting ...` y terminar con `Successfully installed ...` (el aviso `A new release of pip is available` es informativo y se ignora). Si en cambio dice `Requirement already satisfied` en todas las líneas, el entorno **no** está activo: volvé al paso 2. Instala `fastapi[standard]` (incluye `uvicorn`), `sqlmodel`, `sqlalchemy[asyncio]`, `asyncpg` y `python-dotenv`.

#### 4. Crear el archivo `.env`

Se crea con **un solo comando**, así no hay editor de por medio ni riesgo de que se cuele un espacio al principio. Reemplazá `TU_CLAVE` por la contraseña de tu usuario de PostgreSQL (`postgres` es el usuario por defecto; si tu usuario es otro, cambiá también ese texto) y, si en el Paso 0 usaste otro nombre de base, cambiá `veterinaria` por ese nombre. Dejá las comillas simples.

```bash
printf '%s\n' 'DATABASE_URL=postgresql+asyncpg://postgres:TU_CLAVE@localhost:5432/veterinaria' > .env
cat .env
```

Tiene que mostrar **exactamente una línea** que empieza con `DATABASE_URL=`, sin nada antes. Si tu contraseña tiene caracteres especiales, no se puede poner tal cual en la URL: escribilos codificados (`@` → `%40`, `:` → `%3A`, `/` → `%2F`, `#` → `%23`, `?` → `%3F`, `%` → `%25`).

**Alternativa con editor** (si preferís editar a mano): copiá el ejemplo con `cp env.example .env`, abrilo con `nano .env` (en macOS también `open -e .env`), dejá solo la línea `DATABASE_URL=...` empezando en la primera columna, y guardá (en nano: `Ctrl+O`, `Enter`, `Ctrl+X`). Comprobá con `cat .env`.

> `.env` está en `.gitignore`: **nunca** se versiona. No subas credenciales reales al repositorio.

#### 5. Crear el esquema y cargar el seed

```bash
python reiniciar.py
```

> ⚠️ **`reiniciar.py` borra todas las tablas y sus datos** de la base apuntada por `DATABASE_URL`, y luego las recrea con el seed mínimo. No lo apuntes a una base con datos que quieras conservar.

Salida esperada (la consola también imprime líneas INFO de SQLAlchemy por `echo=True`; lo importante es el resumen final):

```text
Reiniciando postgresql+asyncpg://postgres:***@localhost:5432/veterinaria (se borran todas las tablas y sus datos)
Reinicio completo. Conteos por tabla:
  duenio: 2
  ficha_duenio: 1
  mascota: 3
  practica: 4
  turno: 1
  turno_practica: 2
```

El seed deja: 2 dueños (Ana Gómez con ficha, Bruno Díaz sin ficha), 3 mascotas (Toby, Michi, Rocco), 4 prácticas (Consulta `15000.00`, Desparasitación `8000.00`, Vacuna antirrábica `12000.00`, Castración `35000.00`) y 1 turno con 2 prácticas. Los ids son fijos para que los ejemplos del enunciado funcionen tal cual: mascota `1` = Toby, práctica `1` = Consulta, práctica `3` = Vacuna antirrábica, y el próximo turno recibe `id = 2`. Si falla, mirá la tabla de [Problemas frecuentes](#problemas-frecuentes).

#### 6. Levantar la API

```bash
uvicorn app.main:app --reload
```

La terminal queda **ocupada** mostrando el log del servidor (es lo normal: no la cierres). Cuando veas `Application startup complete`, la API está lista en <http://127.0.0.1:8000>:

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- Salud sin base: `GET /health/live` → `200 {"estado": "vivo"}`
- Salud con base: `GET /health/ready` → `200 {"estado": "listo", "base": "ok"}` (o `503` si PostgreSQL no responde)

**Dejá la API corriendo mientras hacés las pruebas**: los casos de `test/` le mandan peticiones y fallan con `The connection was rejected` si está apagada. Para correr otros comandos con la API levantada, abrí **una segunda terminal** en la misma carpeta (o mandá las peticiones desde VS Code con REST Client, que no necesita terminal). Recién cuando termines de probar, frená el servidor con `Ctrl + C`.

**Siguiente:** probá los endpoints con los casos de la sección [Casos de prueba](#casos-de-prueba-test).

---

## Endpoints

Solo existen estas rutas (no se agregaron endpoints fuera de la consigna).

| Método | Ruta | Cuerpo | Respuesta | Códigos |
|---|---|---|---|---|
| GET | `/health/live` | — | `{"estado": "vivo"}` | 200 |
| GET | `/health/ready` | — | `{"estado": "listo", "base": "ok"}` | 200 (la base responde), 503 (la base no responde) |
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
| GET | `/laboratorio/stock/{vacuna}` | — | `{"vacuna": ..., "stock": ...}` (tarda ~1 s: simula un laboratorio externo) | 200 |

Códigos: **201** al crear, **204** al borrar, **404** si el recurso no existe, **409** si la base rechaza la escritura (email o nombre repetido, FK inexistente, baja con dependencias), **422** si el cuerpo o los parámetros no cumplen el contrato, **503** si la base no está disponible en `/health/ready`.

### Cómo leer la columna «Códigos»

La columna lista **todos los códigos posibles** de cada endpoint, no los que vas a ver siempre. Con los datos en orden obtenés el primero (200, 201 o 204); los demás aparecen solo cuando algo sale mal. Por ejemplo, `/health/ready` da **200** mientras PostgreSQL responde y **503** únicamente si la base no responde (PostgreSQL apagado, clave incorrecta en `.env` o base inexistente): no es un error de la aplicación, es el aviso de que está viva pero no puede atender. Si probás con Swagger, tené en cuenta que muestra solo el 200 en «Responses», aunque la API puede devolver los otros.

> La raíz `http://127.0.0.1:8000/` **no tiene endpoint** (la consigna no pide ninguno ahí): `{"detail":"Not Found"}` con 404 es lo normal. Entrá a `/docs` para probar todo desde el navegador (botón **Try it out**, después **Execute**).

### Ejemplos listos para probar

Después de `python reiniciar.py` existen estos datos, que podés usar como ids:

| Recurso | Ids del seed |
|---|---|
| Dueños | `1` Ana Gómez (con ficha, tiene a Toby y Michi) · `2` Bruno Díaz (sin ficha, tiene a Rocco) |
| Mascotas | `1` Toby (perro) · `2` Michi (gato) · `3` Rocco (perro) |
| Prácticas | `1` Consulta `15000.00` · `2` Desparasitación `8000.00` · `3` Vacuna antirrábica `12000.00` · `4` Castración `35000.00` |
| Turnos | `1` (Toby, con las prácticas 1 y 3, total `27000.00`) |

Los ids nuevos los asigna la base: la primera alta después de reiniciar recibe `3` en dueños, `4` en mascotas, `5` en prácticas y `2` en turnos. En Swagger, reemplazá los `"string"` del ejemplo por valores reales antes de ejecutar. Los ejemplos que escriben datos (POST, PATCH, DELETE) modifican la base: para volver al estado inicial corré `python reiniciar.py`.

**Salud**

| Petición | Resultado |
|---|---|
| `GET /health/live` | **200** `{"estado": "vivo"}` |
| `GET /health/ready` | **200** `{"estado": "listo", "base": "ok"}` · con la base caída: **503** |

**Dueños y fichas**

| Petición | Resultado esperado | Caso de error |
|---|---|---|
| `GET /duenios/1` | **200**, Ana Gómez con su ficha | `GET /duenios/999` → **404** (no existe) · `GET /duenios/abc` → **422** (el id no es un entero) |
| `POST /duenios/` con `{"nombre": "Carla Ruiz", "email": "carla.ruiz@ejemplo.com"}` | **201**, el dueño creado con su `id` | repetir un email que ya existe, por ejemplo `"ana.gomez@ejemplo.com"` → **409** · falta `nombre` o `email` → **422** |
| `PATCH /duenios/1` con `{"nombre": "Ana María Gómez"}` | **200**, el dueño actualizado (podés mandar solo uno de los dos campos; `{}` también da **200** sin cambios) | `PATCH /duenios/999` → **404** · `{"email": "bruno.diaz@ejemplo.com"}` (email de otro dueño) → **409** |
| `DELETE /duenios/{id}` de un dueño recién creado, sin ficha ni mascotas (ver nota) | **204**, sin cuerpo | `DELETE /duenios/1` → **409**: Ana tiene mascotas y la base lo impide (`RESTRICT`) · `DELETE /duenios/999` → **404** |
| `POST /duenios/2/ficha` con `{"telefono": "1145550002", "direccion": "Calle Falsa 123"}` | **201**, la ficha creada | `POST /duenios/1/ficha` → **409** (Ana ya tiene ficha: una por dueño) · `POST /duenios/999/ficha` → **404** |
| `GET /duenios/1/mascotas` | **200**, lista con Toby y Michi (`/duenios/2/mascotas` devuelve a Rocco) | `GET /duenios/999/mascotas` → **404** |

> Con el seed, **ninguno de los dos dueños se puede borrar**: Ana tiene mascotas y ficha, y Bruno tiene a Rocco (**409** por `RESTRICT`). Para ver un `DELETE` exitoso (**204**), creá primero un dueño nuevo con `POST /duenios/` y borrá ese. Ojo: un dueño con ficha y sin mascotas tampoco se puede borrar, porque la ficha no tiene `CASCADE` (decisión DD-13).

> **La ficha se crea una sola vez por dueño y no se puede modificar ni borrar:** la consigna no incluye un endpoint para eso (`PATCH /duenios/{id}` solo cambia `nombre` y `email`). Por eso `POST /duenios/1/ficha` falla (Ana ya tiene una, con teléfono `1145550001` y dirección `Av. Ficticia 100`) y el alta exitosa solo se ve con un dueño que todavía no tiene ficha: Bruno (id `2`) o uno recién creado. Una vez creada, `GET /duenios/{id}` la devuelve junto con el dueño. **Cuidado con los `"string"` de ejemplo de Swagger:** si ejecutás con ellos, la ficha queda guardada con el texto literal `string` como teléfono y dirección (la API no valida esos campos) y no se puede corregir; en ese caso, `python reiniciar.py` restaura el estado inicial.

Respuesta de `GET /duenios/1` (**200**):

```json
{
  "id": 1,
  "nombre": "Ana Gómez",
  "email": "ana.gomez@ejemplo.com",
  "ficha": {
    "id": 1,
    "duenio_id": 1,
    "telefono": "1145550001",
    "direccion": "Av. Ficticia 100"
  }
}
```

**Mascotas**

| Petición | Resultado esperado | Caso de error |
|---|---|---|
| `GET /mascotas/1` | **200**, Toby con su dueño | `GET /mascotas/999` → **404** · `GET /mascotas/abc` → **422** |
| `GET /mascotas/?page=1&size=2` | **200**, envoltorio paginado con 2 mascotas, `total: 3`, `pages: 2` | `size=0`, `size=101` o `page=0` → **422** · una página más allá de las existentes (por ejemplo `page=3&size=2`) → **422** |
| `POST /mascotas/` con `{"nombre": "Luna", "especie": "gato", "duenio_id": 2}` | **201**, la mascota creada | `"duenio_id": 999` (dueño inexistente) → **409** (la base rechaza la FK) · falta un campo → **422** |

**Prácticas**

| Petición | Resultado esperado | Caso de error |
|---|---|---|
| `GET /practicas/` | **200**, las 4 prácticas del catálogo con precios como texto (`"15000.00"`) | — |
| `POST /practicas/` con `{"nombre": "Limpieza dental", "precio": "20000.00"}` | **201**, la práctica creada | `"nombre": "Consulta"` (ya existe) → **409** · falta un campo → **422** |

**Turnos**

| Petición | Resultado esperado | Caso de error |
|---|---|---|
| `GET /turnos/1` | **200**, el turno con su mascota y sus dos prácticas (ver respuesta completa más abajo) | `GET /turnos/999` → **404** |
| `POST /turnos/` con el cuerpo de la sección *Alta de turno* | **201**, turno `id: 2` con `total: "27000.00"` | `"mascota_id": 999` o `"practica_id": 999` → **409** (FK inexistente; no queda nada guardado) · cuerpo mal formado → **422** |
| `DELETE /turnos/1` | **204**, sin cuerpo; un `GET /turnos/1` posterior da **404** | `DELETE /turnos/999` → **404** |

**Laboratorio**

| Petición | Resultado esperado |
|---|---|
| `GET /laboratorio/stock/rabia` | **200** `{"vacuna": "rabia", "stock": ...}`, después de ~1 segundo (el laboratorio es externo y lento; mientras tanto el resto de la API sigue respondiendo, ver caso C-09). También probados: `parvo` y `moquillo`. |

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

**Lado de cada clave foránea y regla de borrado**

| FK | Va en | Relación | Al borrar el padre | Por qué |
|---|---|---|---|---|
| `ficha_duenio.duenio_id` → `duenio` | `ficha_duenio` (con `UNIQUE`) | 1:1 de dependencia | `NO ACTION` | La ficha no existe sin el dueño; el `UNIQUE` limita a una ficha por dueño. La consigna no define el borrado (DD-13), así que no se inventa un `CASCADE`. |
| `mascota.duenio_id` → `duenio` | `mascota` (lado "muchos") | 1:N, agregación | `RESTRICT` | RN-08: no se borra un dueño con mascotas; la base lo rechaza sin consulta previa. |
| `turno.mascota_id` → `mascota` | `turno` (lado "muchos") | 1:N, asociación | `NO ACTION` | La consigna no lo define y no hay `DELETE /mascotas/{id}`; no se destruye historia clínica por accidente. |
| `turno_practica.turno_id` → `turno` | `turno_practica` (intermedia) | composición | `CASCADE` | RN-09: al borrar un turno se borran sus prácticas, en la misma transacción. |
| `turno_practica.practica_id` → `practica` | `turno_practica` (intermedia) | M:N con datos (`precio_unitario`) | `NO ACTION` | Un `CASCADE` borraría el histórico de turnos ya cobrados. |

**Índices.** PostgreSQL no indexa las claves foráneas automáticamente. `ix_mascota_duenio_id` evita un recorrido completo de `mascota` al borrar un dueño (`RESTRICT`) y en `GET /duenios/{id}/mascotas`. `ix_turno_mascota_id` cumple la misma función en `turno`. `ix_turno_practica_practica_id` se explica arriba.

Justificación completa: `openspec/changes/archive/2026-10-31-modelos-y-esquema/design.md`, secciones 2 y 3.

---

## Casos de prueba (`test/`)

Todos los casos asumen la base recién reiniciada. Con el entorno virtual activo, en la raíz del repositorio (el comando es igual en PowerShell, CMD y Linux/macOS):

```text
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

> **C-09 no se puede medir con REST Client**, porque ejecuta las peticiones en serie. La nota al final de `test/caso_C-09.http` explica la idea: lanzar las tres consultas al laboratorio en paralelo y medir el endpoint de salud mientras corren. Con la API levantada (paso 6), abrí una **segunda terminal** y usá el bloque de la tuya.

**PowerShell**

```powershell
Measure-Command { curl.exe -s http://localhost:8000/laboratorio/stock/rabia }
1..3 | ForEach-Object { Start-Process curl.exe -ArgumentList "-s","-o","NUL","http://localhost:8000/laboratorio/stock/rabia" -WindowStyle Hidden }
Start-Sleep -Milliseconds 100
Measure-Command { curl.exe -s http://localhost:8000/health/live }
```

La primera medición muestra lo que tarda **una** consulta al laboratorio sola (`TotalMilliseconds` cerca de 1000). La última mide el health con tres consultas lentas en vuelo: tiene que responder en decenas de milisegundos, no en ~1000.

**Linux / macOS**

```bash
curl -s http://localhost:8000/laboratorio/stock/rabia > /dev/null &
curl -s http://localhost:8000/laboratorio/stock/parvo > /dev/null &
curl -s http://localhost:8000/laboratorio/stock/moquillo > /dev/null &
sleep 0.3
time curl -s http://localhost:8000/health/live
```

**CMD:** no tiene una forma simple de lanzar procesos en paralelo; usá PowerShell para este caso.

El health debe responder en ~0 ms mientras cada consulta al laboratorio tarda ~1000 ms.

### Cómo correr el `.sql` (caso C-08)

**Con pgAdmin:** abrí el **Query Tool** sobre la base `veterinaria` (Tools → Query Tool), cargá `test/caso_C-08.sql` con el botón de abrir archivo y ejecutalo con **F5** o el botón ▶. Esperado: `ERROR: new row for relation "practica" violates check constraint ... (SQLSTATE 23514)` y 0 filas modificadas.

**Con `psql`** (si está en el `PATH`; el comando es igual en PowerShell, CMD y Linux/macOS, y se corre desde la raíz del repositorio):

```text
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

| Mensaje o síntoma | Causa | Solución |
|---|---|---|
| `"Copy-Item" no se reconoce como un comando interno o externo` (o `Start-Process`, `Test-Path`) | Estás en **CMD** y pegaste comandos de PowerShell. | Abrí PowerShell (prompt con `PS`) y seguí la Guía A, o seguí la Guía B completa en CMD. |
| `'cp' no se reconoce...` o `'source' no se reconoce...` | Estás en Windows y pegaste comandos de Linux/macOS. | Seguí la Guía A (PowerShell) o la Guía B (CMD). |
| `Activate.ps1` no se reconoce / no existe la carpeta `.venv` | `python -m venv .venv` no terminó de crear el entorno (en Windows, el primer `python` del `PATH` puede ser un alias que falla en silencio). | Comprobá con `Test-Path .\.venv\Scripts\Activate.ps1` (PowerShell) y recrealo con `py -3.13 -m venv .venv --clear`. |
| `UnauthorizedAccess` al activar en PowerShell | La política de ejecución impide correr scripts. | Usá el atajo de la Guía A (paso 2) o la Guía B (CMD). |
| `pip install` dice `Requirement already satisfied` en todo | El entorno virtual no está activo (falta `(.venv)` en el prompt) y se usa el Python global. | Activalo según tu guía (paso 2) y repetí el `pip install`. |
| `python --version` no muestra nada, o `python` abre la tienda de Microsoft | En Windows, `python` puede ser un alias que falla en silencio (suele aparecer como `C:\Windows\System32\python`). | Usá `py -3.13` (o `py -3.12`) en lugar de `python` para crear el entorno (`py -3.13 -m venv .venv`). Una vez activado el entorno, `python` sí funciona. Si `py` tampoco se reconoce, instalá Python 3.12+ desde python.org marcando **Add python.exe to PATH**. |
| `FATAL: DATABASE_URL no está definida. Copiá env.example a .env y configurá la conexión.` | No existe `.env` o le falta `DATABASE_URL`, o estás en otra carpeta. El arranque aborta con código 1. | Hacé el paso 4 de tu guía y comprobá con `dir` / `ls` que `.env` está junto a `reiniciar.py`. |
| `ERROR: no se pudo reiniciar la base ...` | La base no existe o las credenciales de `DATABASE_URL` son incorrectas. El script revierte la transacción y sale con código 2. | Creá la base (Paso 0) y revisá usuario, clave, puerto y nombre de la base en `.env`. |
| `ERROR: la base de datos «veterinaria» ya existe` | La base ya estaba creada. | No es un error del proyecto: seguí con el paso 1 de tu guía, o usá otro nombre de base en `DATABASE_URL` (ver Paso 0). |
| `psql` no se reconoce | `psql` no está en el `PATH`. | Creá la base desde pgAdmin (Paso 0); no necesitás `psql`. |
| REST Client: `The connection was rejected. Either the requested service isn't running...` | La API está apagada (o corre en otro puerto): los casos necesitan `uvicorn` levantado. | Levantala con `uvicorn app.main:app --reload` desde la raíz del proyecto, dejala abierta y mandá de nuevo la petición. |
| El prompt no vuelve después de `notepad .env` | El Bloc de notas sigue abierto (en Windows 11 puede tener varias pestañas). | Guardá, cerrá todas las ventanas del Bloc de notas y el prompt vuelve. Si no, `Ctrl+C`. |
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
