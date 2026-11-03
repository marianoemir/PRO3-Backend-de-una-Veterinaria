# Tareas: pruebas-http-y-evidencia

> Dueño: **Andrés**. Duración estimada total: **4–6 h**. Dependencias: changes 03 a 09 archivados y mergeados.
> Alcance: **solo `test/`**. No se toca `app/`, `reiniciar.py` ni `main.py`.

## Notas previas (leer antes de empezar)

- **La base debe existir** para correr los casos: `python reiniciar.py` antes de levantar la app (`uvicorn app.main:app`).
- **Base URL**: `http://localhost:8000`. Todos los `.http` asumen la base recién reiniciada (ids del seed).
- **`echo=True`** está habilitado en `app/core/database.py` (DD-02): la consola muestra los `SELECT`, base de la evidencia C-07.
- **Si un caso falla**: registrar el caso, el código observado y el módulo dueño; **no** editar `app/` desde `test/`.
- **TDD**: no hay suite pytest obligatoria. Cada tarea se verifica con una petición `.http` observable o una consulta SQL.

## 1. Preparación

- [x] 1.1 Crear el directorio `test/` y la convención de los `.http` (base URL, precondición `python reiniciar.py`, comentario con respuesta esperada). **Verificación**: `ls test/` existe y un `.http` de prueba abre en REST Client sin error de sintaxis.
- [x] 1.2 Confirmar el estado del seed (ids 1..4 de prácticas, mascota 1 = Toby, turno 1 con prácticas 1 y 3) con una consulta rápida a la app. **Verificación**: `GET /practicas/` devuelve 4 prácticas y `GET /turnos/1` (si existiera) o SQL `SELECT count(*) FROM turno` = 1.

## 2. Casos de contrato C-01 a C-06

- [x] 2.1 Escribir `test/caso_C-01.http` (`GET /duenios/abc` → **422**, sin ejecutar el handler). **Verificación**: ejecutar el archivo tras `reiniciar.py` y confirmar 422.
- [x] 2.2 Escribir `test/caso_C-02.http` (email de dueño y nombre de práctica repetidos → **409** con mensaje propio). **Verificación**: crear un dueño/práctica con email/nombre ya existente y confirmar 409 con mensaje propio, sin segunda fila.
- [x] 2.3 Escribir `test/caso_C-03.http` (segunda ficha para el mismo dueño → **409**). **Verificación**: `POST /duenios/1/ficha` dos veces; la segunda responde 409.
- [x] 2.4 Escribir `test/caso_C-04.http` (mascota con dueño inexistente → **409**; turno con práctica inexistente → **409** y nada guardado). **Verificación**: ejecutar ambos requests y comprobar por SQL `SELECT count(*) FROM turno` sin cambios tras el segundo.
- [x] 2.5 Escribir `test/caso_C-05.http` (borrar dueño con mascotas → **409**; borrar turno → **204** y sin prácticas). **Verificación**: `DELETE /duenios/1` → 409; `DELETE /turnos/1` → 204; SQL `SELECT count(*) FROM turno_practica WHERE turno_id = 1` = 0.
- [x] 2.6 Escribir `test/caso_C-06.http` (turno válido con dos prácticas → **201**, precios copiados y total `"27000.00"`). **Verificación**: ejecutar y comparar el JSON con el ejemplo de la consigna (mascota 1 Toby, prácticas 1 y 3).

## 3. Caso C-07 (detalle y número fijo de consultas)

- [x] 3.1 Escribir `test/caso_C-07.http` que cree un turno con una práctica (práctica 2) y otro con tres (prácticas 1, 2, 3), y luego ejecute `GET /turnos/{id}` para cada uno. **Verificación**: ambos GET responden 200 con mascota y prácticas.
- [x] 3.2 Ejecutar el caso con `uvicorn` y `echo=True`, capturar la consola y contar los `SELECT` de cada detalle (esperado: 2 en ambos). **Verificación**: la consola muestra la misma cantidad de `SELECT` y ninguna `MissingGreenlet`.
- [x] 3.3 Guardar el fragmento relevante en `test/evidencia_C-07.txt` (solo los `SELECT` de ambos detalles, sin credenciales ni ruido). **Verificación**: el archivo existe y contiene ambos fragmentos con la misma cantidad de `SELECT`.

## 4. Caso C-08 (CHECK en la base)

- [x] 4.1 Escribir `test/caso_C-08.sql` con `UPDATE practica SET precio = 0 WHERE id = 1;` (y opcionalmente `precio = -1`), con comentario del rechazo por `CHECK`. **Verificación**: ejecutar con `psql`/cliente SQL y confirmar error `check_violation` (sqlstate 23514) y 0 filas modificadas.
- [x] 4.2 Escribir `test/caso_C-08.http` con lectura del catálogo antes y después del intento, mostrando que el precio sigue intacto. **Verificación**: `GET /practicas/` devuelve `"15000.00"` para la práctica 1 tras el intento.

## 5. Caso C-09 (asincronía sin bloqueos)

- [x] 5.1 Escribir `test/caso_C-09.http` con tres `GET /laboratorio/stock/{vacuna}` y un `GET /health/live` en el medio, con respuesta esperada y nota de concurrencia. **Verificación**: el archivo es válido en REST Client y documenta el comando paralelo con `curl`.
- [x] 5.2 Ejecutar las tres consultas al laboratorio en paralelo y medir que `GET /health/live` responde de inmediato (anotar latencias). **Verificación**: la latencia del endpoint de salud es ~0 ms mientras las del laboratorio son ~1000 ms.

## 6. Verificación integrada

- [x] 6.1 Correr la suite completa tras `python reiniciar.py` (casos C-01..C-09) y registrar el resultado de cada uno. **Verificación**: tabla de resultados (caso → código esperado → código observado) sin discrepancias; si hay fallo, anotar caso, código observado y módulo dueño.
- [x] 6.2 Verificar que el diff del change contiene solo archivos bajo `test/`. **Verificación**: `git status` / `git diff --stat` muestra únicamente `test/`.

## Workflow follow-up

- Archivar el change con `/opsx:archive pruebas-http-y-evidencia` y marcar `[x]` en `CHANGES.md` (solo la línea `[10]`) una vez revisado.
- Entregar `test/evidencia_C-07.txt` al dueño de `[11]` `readme-y-entrega` (Facundo) para el README.