# Flujos Principales

## Flujo 1: Arranque de la aplicación

**Disparador**: `uvicorn app.main:app`
**Actor**: operador

**Pasos**:
1. `app/core/config.py` lee `DATABASE_URL` del entorno (cargado desde `.env` con python-dotenv).
2. El `lifespan` crea el motor asincrónico (`create_async_engine`) y la fábrica de sesiones (`async_sessionmaker`, `expire_on_commit=False`).
3. Ambos se guardan en `app.state`.
4. Se registran los routers de los seis módulos.
5. Al apagar, el `lifespan` cierra el motor.

**Casos de error**:
- `DATABASE_URL` ausente → la app no debe arrancar; ver [10_preguntas_abiertas.md](10_preguntas_abiertas.md).
- Base inaccesible → la app arranca pero `/health/ready` responde 503.

## Flujo 2: Alta de dueño con conflicto de email

**Disparador**: `POST /duenios/`
**Actor**: dueño de mascota

**Pasos**:
1. FastAPI valida el cuerpo contra `DuenioCreate` (sin `id`). Si falla → **422**, el handler no se ejecuta.
2. El router delega en el `service` pasándole la sesión.
3. El `service` hace `session.add()` + `commit()` directamente, **sin** consultar si el email ya existe.
4. Si la base acepta → **201** con `DuenioRead`.
5. Si la base rechaza por `UNIQUE(email)` → el `service` atrapa `IntegrityError`, hace `rollback()` y levanta una excepción propia que el router traduce a **409 con mensaje propio**.

**Casos de error**:
- Email repetido → 409.
- Cuerpo inválido → 422.

## Flujo 3: Alta de ficha (uno a uno)

**Disparador**: `POST /duenios/{id}/ficha`
**Actor**: dueño de mascota

**Pasos**:
1. El `service` busca el dueño con carga anticipada de `ficha`; si no existe → **404**.
2. Crea `FichaDuenio` con `duenio_id`.
3. `commit()`: si el dueño ya tenía ficha, `UNIQUE(duenio_id)` rechaza → `IntegrityError` → `rollback()` → **409**.
4. Si acepta → **201** con `FichaRead`.

## Flujo 4: Reserva de turno con prácticas (composición + M:N con datos)

**Disparador**: `POST /turnos/`
**Actor**: dueño de mascota

```
Cliente → router → service → [validación DTO] → [lectura de prácticas] → [cálculo de precios] → [una transacción] → DB
```

**Pasos**:
1. El DTO `TurnoCreate` valida: `mascota_id`, `fecha` (con zona horaria), `motivo`, `practicas` con **al menos un** elemento. Lista vacía → **422**.
2. El `service` abre **una sola transacción**.
3. Lee del catálogo las prácticas pedidas y copia `precio` a `precio_unitario` en la fila de `turno_practica`.
4. Calcula `total` como la suma de los `precio_unitario` (servidor, no cliente).
5. Persiste el `Turno` y sus `TurnoPractica` juntos.
6. Si una práctica no existe → no se guarda **nada** (ni turno ni filas hijas) y se responde **409**.
7. Si una práctica viene repetida → la PK compuesta `(turno_id, practica_id)` rechaza → **409**.
8. Responde **201** con `TurnoRead`: `id`, `fecha` en UTC, `motivo`, `total` como string decimal, `mascota` resumida y `practicas` con `practica_id`, `nombre`, `precio_unitario`.

**Ejemplo de entrada**:
```json
{
  "mascota_id": 1,
  "fecha": "2026-11-12T10:30:00-03:00",
  "motivo": "Control anual",
  "practicas": [{ "practica_id": 1 }, { "practica_id": 3 }]
}
```

**Ejemplo de salida**:
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

## Flujo 5: Detalle de turno sin N+1

**Disparador**: `GET /turnos/{id}`
**Actor**: personal de la veterinaria

**Pasos**:
1. El `service` arma **una** consulta con `joinedload(Turno.mascota)` y `selectinload(Turno.practicas)`, más lo necesario para resolver el nombre de cada práctica.
2. Cantidad de consultas **fija**: no crece con la cantidad de prácticas del turno.
3. Si no hay turno → **404**.
4. Si el código intenta acceder a una relación no precargada, SQLAlchemy falla con `MissingGreenlet` — la prueba de que no hay carga perezosa.

**Verificación**: caso **C-07** — mismo número de consultas con una práctica y con tres, mirando la consola con `echo=True`.

## Flujo 6: Baja de turno con composición

**Disparador**: `DELETE /turnos/{id}`

**Pasos**:
1. El `service` busca el turno; si no existe → **404**.
2. Ejecuta el `DELETE` del turno.
3. La base borra las filas de `turno_practica` por **`ON DELETE CASCADE`**.
4. El ORM **no** intenta vaciar ni borrar las filas por su cuenta: `Turno.practicas` se declara con `passive_deletes` para que la decisión sea de la base.
5. Responde **204**.

**Verificación**: caso **C-05** — después del 204, las prácticas del turno ya no están.

## Flujo 7: Baja de dueño bloqueada por agregación

**Disparador**: `DELETE /duenios/{id}`

**Pasos**:
1. El `service` busca el dueño; si no existe → **404**.
2. Intenta borrar.
3. Si tiene mascotas a su nombre, la base rechaza por **`ON DELETE RESTRICT`** → `IntegrityError` → `rollback()` → **409**.
4. Si no tiene mascotas → **204**.

## Flujo 8: Consulta al laboratorio sin bloquear el event loop

**Disparador**: `GET /laboratorio/stock/{vacuna}`

**Pasos**:
1. El router (`async def`) delega en el `service`.
2. El `service` invoca `consultar_stock(vacuna)` — función **sincrónica** que hace `time.sleep(1)` — **sin modificarla**, ejecutándola fuera del bucle de eventos (por ejemplo `asyncio.to_thread` o el threadpool de Starlette; ver [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md)).
3. Responde `{ "vacuna": ..., "stock": ... }` con 200.

**Verificación**: caso **C-09** — tres consultas simultáneas al laboratorio y `GET /health/live` responde de inmediato.

## Flujo 9: Reinicio del entorno de prueba

**Disparador**: `python reiniciar.py`

**Pasos**:
1. Borra las tablas (`drop_all`).
2. Las crea con `SQLModel.metadata.create_all`.
3. Carga los datos iniciales: 2 dueños (uno con ficha), 3 mascotas, 4 prácticas, 1 turno con 2 prácticas.
4. Los archivos `.http` de `test/` se corren después de este paso.
