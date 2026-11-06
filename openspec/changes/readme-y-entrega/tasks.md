# Tareas: readme-y-entrega

> Dueño: **Facundo**. Dependencias: change 10 archivado.
> Alcance: `README.md` y ajustes de cierre. Sin endpoints nuevos.

## 1. README

- [x] 1.1 Pasos desde cero: requisitos, entorno virtual por shell, `pip install -r requirements.txt`, `.env`, base en pgAdmin, `python reiniciar.py`, `uvicorn app.main:app`.
- [x] 1.2 Tabla de endpoints y códigos; cómo correr los `.http` y el `.sql` del caso C-08.
- [x] 1.3 Explicación de por qué `turno_practica.turno_id` no necesita índice propio.
- [x] 1.4 Enlace a `test/evidencia_C-07.txt` y a los casos C-01 a C-09.
- [x] 1.5 Sección "Decisiones propias del equipo" (DD-08 a DD-15) y checklist de entrega.

## 2. Ajustes de cierre

- [x] 2.1 `DuenioUpdate` rechaza `null` explícito en `nombre` y `email` (422); omitirlos sigue siendo válido.
- [x] 2.2 `min_length=1` en los textos obligatorios de los DTO de alta.
- [x] 2.3 `caso_C-05.http`: `GET /turnos/1` → 404 después del DELETE.
- [x] 2.4 README: nota del `null` (422), fila de DD-12 y checklist ("versiones fijadas").
- [x] 2.5 **Verificación**: `PATCH /duenios/1` con `{"nombre": null}` → 422; con `{"nombre": "Ana"}` → 200 y el email no cambia.

## 3. Verificación final (antes de archivar)

- [x] 3.1 Venv nuevo con Python 3.12: `pip install -r requirements.txt` y `pip check` sin errores; `python -c "import app.main"` con una `DATABASE_URL` cualquiera no falla por imports (verificado con Python 3.13, no 3.12).
- [ ] 3.2 Seguir el README **al pie de la letra** desde una base vacía y un entorno virtual nuevo (quien verifica no es quien lo escribió).
- [x] 3.3 Regenerar `test/evidencia_C-07.txt` con la versión final: tras `python reiniciar.py`, ejecutar `caso_C-07.http` (los dos POST crean los turnos 2 y 3) y copiar de la consola los dos `SELECT` que aparecen justo antes de la línea de acceso `GET /turnos/2` y de `GET /turnos/3`. No copiar los del POST. Los dos detalles deben mostrar la misma cantidad de `SELECT`.
- [x] 3.4 Correr C-01 a C-09 tras `python reiniciar.py` y confirmar la respuesta de cada comentario (C-08 desde pgAdmin, C-09 con la nota de PowerShell) — Verificados a mano con la API real el 2026-11-05: C-01 (422), C-02 (409 con mensaje propio en email y en nombre de práctica), C-03 (201 la primera ficha y 409 la segunda), C-04, C-05, C-06, C-07 (2 SELECT con 1 y con 3 prácticas), C-08 (UPDATE rechazado por ck_practica_precio_positivo, 23514, precio intacto en 15000.00) y C-09 (GET /health/live respondió en 32,6 ms con 3 consultas al laboratorio en curso).
- [x] 3.5 Completar fecha y hora de entrega en `docs/DIVISION-DEL-EQUIPO.md` (Sin fecha fijada por la cátedra al 2026-11-05 (a confirmar con el profesor)).
- [ ] 3.6 Archivar el change (`/opsx-archive`), marcar `[x]` la línea [11] de `CHANGES.md`, PR revisado por otra persona y mergeado.
