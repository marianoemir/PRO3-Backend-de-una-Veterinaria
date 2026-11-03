# Propuesta: pruebas-http-y-evidencia

## Why

Todos los módulos de la API ya están implementados y archivados (changes 03 a 09), pero falta la evidencia ejecutable que demuestra que cada regla de negocio y cada caso de la consigna se cumple. Sin los archivos `.http`, el `.sql` del caso C-08 y la captura de consola del C-07 no hay forma reproducible de verificar el contrato ni de entregar el trabajo.

## What Changes

- Crear `test/caso_C-01.http` … `test/caso_C-09.http`, un archivo por caso de la consigna, cada uno con la respuesta esperada en un comentario, para correr después de `python reiniciar.py`.
- Crear `test/caso_C-08.sql` con el `UPDATE practica SET precio = 0` ejecutado directo en la base, con el rechazo por `CHECK` documentado.
- Crear `test/evidencia_C-07.txt` con el fragmento de consola (con `echo=True`) del detalle de un turno con una práctica y con tres.
- No se toca código de la aplicación. Si un caso falla, se registra el fallo y el módulo al que pertenece, sin parchear desde `test/`.

## Capabilities

### New Capabilities

- `pruebas-http-y-evidencia`: suite de casos de prueba HTTP de la cátedra (C-01 a C-09) y evidencia de consola del caso C-07, ejecutables tras reiniciar la base.

### Modified Capabilities

Ninguna. Este change no altera el comportamiento de la API; solo agrega evidencia verificable bajo `test/`.

## Impact

- **Código afectado**: solo archivos nuevos bajo `test/`. No se edita `app/`, `reiniciar.py`, modelos, servicios ni routers.
- **Base de datos**: sin cambios de esquema ni de datos; los casos se corren sobre el seed de `reiniciar.py`.
- **Dependencias**: requiere los changes 03 a 09 archivados y mergeados (confirmado).
- **Riesgo principal**: los casos dependen del estado exacto del seed (ids 1..4 de prácticas, mascota 1 = Toby, turno 1 con 2 prácticas). Mitigación: ejecutar siempre tras `python reiniciar.py`.