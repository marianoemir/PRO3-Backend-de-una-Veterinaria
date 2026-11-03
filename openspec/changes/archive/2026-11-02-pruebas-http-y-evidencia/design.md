# Design — pruebas-http-y-evidencia ([10], Andrés)

## Context

Todos los módulos de la API están implementados y archivados (changes 03 a 09). El contrato HTTP, los modelos, el seed y el esquema están fijos. Este change agrega únicamente evidencia verificable bajo `test/`, sin tocar código de la aplicación. La motivación y el alcance están en `proposal.md`.

## Goals / Non-Goals

**Goals:**

- Proveer un archivo `.http` por caso C-01..C-09, con la respuesta esperada en un comentario, ejecutable tras `python reiniciar.py`.
- Proveer `test/caso_C-08.sql` con el `UPDATE` directo y el rechazo por `CHECK`.
- Proveer `test/evidencia_C-07.txt` con el fragmento de consola del detalle con 1 y con 3 prácticas.
- Mantener el alcance estrictamente en `test/`.

**Non-Goals:**

- No modificar `app/`, `reiniciar.py`, modelos, servicios ni routers.
- No agregar endpoints nuevos ni cambiar el contrato.
- No introducir una suite pytest: la verificación es por peticiones `.http` y consultas SQL, como exige la consigna.
- No corregir código de la app desde `test/`: un fallo se reporta al dueño del módulo.

## Decisions

### Formato de los `.http`

Se usa el formato REST Client (un request por archivo, con `###` y comentarios `#`), con `base_url = http://localhost:8000` y la respuesta esperada documentada en un comentario al inicio de cada archivo. Se elige un archivo por caso (no uno por endpoint) para que cada caso sea ejecutable de forma aislada y coincida con la nomenclatura `caso_C-0X.http` exigida por la consigna.

### Estado inicial de los casos

Todos los `.http` asumen la base recién reiniciada (`python reiniciar.py`). El seed fija los ids: dueños 1 y 2, mascotas 1-3, prácticas 1-4, turno 1 con prácticas 1 y 3. El caso C-06 crea el turno con `id = 2` (siguiente al seed). El caso C-07 necesita turnos adicionales con 1 y con 3 prácticas, que se crean con `POST /turnos/` dentro del propio archivo `.http` antes de la lectura.

### Caso C-07 y evidencia de consola

El archivo `caso_C-07.http` crea un turno con una práctica (práctica 2) y otro con tres (prácticas 1, 2, 3), y luego ejecuta `GET /turnos/{id}` para cada uno. Con `echo=True` en `app/core/database.py` (DD-02), la consola muestra la misma cantidad de `SELECT` (2: uno con `joinedload(Turno.mascota)` y otro con `selectinload(Turno.practicas).joinedload(TurnoPractica.practica)`). El fragmento de consola se guarda en `test/evidencia_C-07.txt`.

### Caso C-08

El archivo `caso_C-08.sql` ejecuta `UPDATE practica SET precio = 0 WHERE id = 1;` (y, opcionalmente, un precio negativo) directo en PostgreSQL, documentando que la base lo rechaza por `CHECK (precio > 0)` con `sqlstate 23514` y que ninguna fila queda modificada. `caso_C-08.http` complementa con una lectura del catálogo antes y después, para mostrar que el precio sigue intacto.

### Caso C-09

El archivo `caso_C-09.http` lanza tres `GET /laboratorio/stock/{vacuna}` y un `GET /health/live` en el medio, documentando que el de salud responde de inmediato (verificación manual de latencia, ya que REST Client ejecuta secuencialmente; se anota la limitación y la forma de medir con curl/paralelo).

### Fallos

Si un caso no responde lo esperado, se registra en el propio archivo (comentario con el código observado y el módulo dueño) o en un reporte aparte, sin editar `app/`. La corrección corresponde al dueño del módulo en su rama.

## Risks / Trade-offs

- [Riesgo] El estado de la base cambia si se corren los casos fuera de orden o sin reiniciar. → Mitigación: cada archivo declara como precondición `python reiniciar.py`, y el caso C-06/C-07 se apoyan en ids del seed.
- [Riesgo] REST Client ejecuta los requests de un `.http` de forma secuencial; C-09 pide concurrencia real. → Mitigación: documentar el comando equivalente con `curl` en paralelo y anotar la latencia esperada.
- [Riesgo] La captura de consola del C-07 puede incluir credenciales o ruido. → Mitigación: guardar solo el fragmento relevante (los `SELECT` de los dos detalles), sin `DATABASE_URL` ni trazas ajenas.
- [Trade-off] Un `.http` por caso (en vez de uno por endpoint) duplica preámbulos, pero facilita la corrección caso por caso y coincide con la nomenclatura exigida.

## Migration Plan

No aplica: no hay cambios de esquema, datos ni código. Solo se agregan archivos bajo `test/`. Para deshacer, borrar la carpeta `test/`.

## Open Questions

Ninguna. Todo lo no decidido por la consigna está resuelto en DD-08 a DD-15 o en `10_preguntas_abiertas.md`, y no afecta a este change (que no toca código).