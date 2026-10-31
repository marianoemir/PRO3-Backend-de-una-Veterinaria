# 03_actores_y_roles.md

> **No hay autenticación ni autorización** en este trabajo (fuera de alcance según la consigna). No existen usuarios, roles, tokens ni permisos: toda ruta es pública.

## Actores

| Actor | Qué hace con la API |
|---|---|
| **Personal de la veterinaria** (único actor funcional) | Registra dueños y su ficha, mascotas, prácticas del catálogo y turnos; consulta el stock de vacunas del laboratorio. |
| **Corrector / cátedra** | Ejecuta `python reiniciar.py`, levanta la app y corre los casos `.http` de `test/`; revisa modelos, restricciones y evidencia. |
| **Laboratorio** (sistema externo) | Provee la biblioteca sincrónica `cliente.py` (`consultar_stock`). No es un actor humano. |

## Qué NO existe

- Login, registro de usuarios, roles (`admin`, `vet`, `owner`…) ni middleware de permisos.
- Veterinario como entidad: el turno es de una **mascota** y no tiene profesional asignado.
- Facturas, pagos, recetas o diagnósticos.

Si alguien propone agregar alguno, es un cambio de alcance: consultar a la cátedra.
