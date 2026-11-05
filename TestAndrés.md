# Validación de instalación limpia — Andrés

**Fecha:** 2026-11-05  
**Repositorio remoto probado:** `https://github.com/marianoemir/PRO3-Backend-de-una-Veterinaria.git`  
**Commit del clon limpio:** `3ca491c2736f33f917c76d74fc9dd32363023e74`

## Entorno

- Sistema operativo: Windows 11 Pro 64 bits (`10.0.26200`).
- Python: `Python 3.13.7`.
- PostgreSQL cliente: `psql (PostgreSQL) 17.11`.

## Procedimiento ejecutado

Se realizó un clon nuevo en:

`C:\Users\andre\AppData\Local\Temp\opencode\PRO3-Backend-de-una-Veterinaria-clean-test-20261105`

No se copió ningún `.venv`, `.env` ni archivo desde otro checkout.

| Paso README | Comando exacto | Resultado |
|---|---|---|
| 2 — Entorno virtual (PowerShell) | `python -m venv .venv` | OK; se creó el entorno. |
| 2 — Activación (PowerShell) | `.\.venv\Scripts\Activate.ps1` | OK; sin error de política de ejecución. |
| 3 — Dependencias | `pip install -r requirements.txt` | OK; finalizó con `Successfully installed ...`. Solo mostró el aviso informativo de actualización de pip. |

## Continuación con credencial local proporcionada

La credencial fue proporcionada por el usuario para continuar la prueba. Se usó el usuario `postgres`, que es el usuario explícito en el comando alternativo del paso 5 del README. La contraseña fue escrita únicamente en el `.env` ignorado del clon temporal y no se registra en este informe.

| Paso README | Comando exacto | Resultado |
|---|---|---|
| 4 — Crear `.env` (PowerShell) | `Copy-Item env.example .env` | OK; se creó `.env` desde el ejemplo y se completó con la credencial proporcionada. |
| 5 — Crear base (alternativa `psql`) | `psql -U postgres -c "CREATE DATABASE veterinaria;"` | **Falló** (código 1). Salida completa: `ERROR:  la base de datos «veterinaria» ya existe` |

## Bloqueo reproducible

**Paso 5 — Crear la base `veterinaria`.**

La configuración de `.env` ya puede completarse con las credenciales proporcionadas. Sin embargo, la creación de la base falla porque `veterinaria` ya existe. El procedimiento pedido exige una base nueva y prohíbe arreglar o asumir su estado. No se ejecutó `python reiniciar.py` contra esa base preexistente para evitar borrar tablas o datos ajenos.

El archivo `env.example` contiene exclusivamente:

```dotenv
DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/veterinaria
```

El README indica ejecutar `Copy-Item env.example .env` y luego reemplazar `usuario` y `clave` por las credenciales locales. No se copió un `.env` previo ni se adivinaron credenciales. La contraseña llegó luego por indicación expresa del usuario.

Para continuar haría falta que la persona responsable indique explícitamente si se puede eliminar/reutilizar la base existente, o que proporcione un servidor PostgreSQL donde `veterinaria` no exista. No se hizo ninguna de esas acciones por cuenta propia.

## Verificaciones que quedan pendientes por el bloqueo

- `python reiniciar.py` y los conteos del seed.
- `uvicorn app.main:app --reload`.
- `GET /docs`, `/health/live` y `/health/ready`.
- Casos `C-01`, `C-05` y `C-06` (todos requieren, según sus comentarios, haber ejecutado antes `python reiniciar.py`).

Resultados esperados leídos en los casos:

- C-01: `GET /duenios/abc` → 422.
- C-05: borrar `duenios/1` → 409; borrar `turnos/1` → 204 y luego consultarlo → 404.
- C-06: alta de turno → 201, `id=2`, fecha UTC y total `"27000.00"`.

## Revisión del README

- La explicación del índice de `turno_practica.turno_id` es clara: la PK compuesta `(turno_id, practica_id)` ya genera un B-tree cuyo primer campo es `turno_id`; por ese orden sirve para buscar por turno. Explica correctamente por qué se agrega un índice independiente para `practica_id`.
- El README documenta que `.env` no se versiona.

## Estado final del clon limpio

- `git status --short`: sin salida (limpio; `.venv` y `.env` están ignorados).
- `git ls-files .env`: sin salida.
- `.env` existe solo en el clon temporal, está ignorado y no está versionado.

## Dudas / observaciones

1. La credencial local es un requisito externo al repositorio; el README explica dónde colocarla, pero una prueba autónoma requiere conocerla.
2. La base `veterinaria` ya existía en el servidor local. El README no incluye una comprobación previa ni una alternativa para hacer la prueba desde cero cuando eso sucede. Borrarla o reutilizarla sería una decisión destructiva que no se tomó.
3. El checkout original desde el que se inició la tarea tenía un `README.md` de solo dos líneas; el clon remoto sí contiene el README completo probado aquí. La validación se hizo sobre el clon remoto limpio, que es el artefacto relevante.
4. Este informe se agregó al checkout de trabajo porque fue solicitado explícitamente. Por eso el checkout de trabajo ya no quedará limpio hasta que el archivo se incorpore a un commit o se elimine; el clon sometido a la prueba sí quedó limpio.
