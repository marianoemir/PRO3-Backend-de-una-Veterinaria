# Funcionalidades

Organizadas por **épica** y luego por **historia de usuario**. Cada historia referencia las reglas de [05_reglas_de_negocio.md](05_reglas_de_negocio.md). Solo se describen funcionalidades presentes en el enunciado.

## Épica 1: Base del servicio y salud

### US-001 — Ciclo de vida del motor y la sesión
**Como** desarrollador
**Quiero** que el motor y la fábrica de sesiones se creen en el `lifespan` y se cierren al apagar
**Para** que la aplicación gestione el pool de conexiones correctamente

**Criterios de aceptación**:
- [ ] El motor asincrónico y la fábrica de sesiones se crean en el `lifespan` y se guardan en `app.state`.
- [ ] El motor se cierra al apagar la aplicación.
- [ ] La sesión llega a cada handler con `Depends(get_session)`, una por petición, con `expire_on_commit=False`.

**Reglas relacionadas**: RN-20, RN-21

### US-002 — Salud del servicio
**Como** operador
**Quiero** consultar si el proceso está vivo y si la base responde
**Para** distinguir un problema de la app de un problema de la base

**Criterios de aceptación**:
- [ ] `GET /health/live` responde `{"estado": "vivo"}` con 200 y **no toca la base**.
- [ ] `GET /health/ready` ejecuta `SELECT 1` y responde 200 si la base contesta.
- [ ] `GET /health/ready` responde **503** si la base no contesta.

**Reglas relacionadas**: RN-22

## Épica 2: Dueños y ficha

### US-003 — Alta de dueño
**Como** dueño de mascota
**Quiero** registrar mi nombre y email
**Para** quedar en el padrón de la veterinaria

**Criterios de aceptación**:
- [ ] `POST /duenios/` responde **201** con `DuenioRead`.
- [ ] El DTO de alta no incluye `id`.
- [ ] Email repetido → **409** con mensaje propio.
- [ ] Cuerpo inválido → **422**.

**Reglas relacionadas**: RN-01, RN-10, RN-12

### US-004 — Detalle de dueño con su ficha
**Como** personal de la veterinaria
**Quiero** ver un dueño junto con su ficha
**Para** contactarlo

**Criterios de aceptación**:
- [ ] `GET /duenios/{id}` responde **200** con el dueño y su ficha.
- [ ] Se resuelve con carga anticipada y número fijo de consultas.
- [ ] Id inexistente → **404**; id no entero → **422**.

**Reglas relacionadas**: RN-14, RN-15, RN-12

### US-005 — PATCH parcial de dueño
**Como** dueño de mascota
**Quiero** modificar sólo los campos que envío
**Para** no tener que reenviar toda mi información

**Criterios de aceptación**:
- [ ] `PATCH /duenios/{id}` aplica sólo los campos enviados, con `exclude_unset`.
- [ ] Responde **200** con el dueño y su ficha.
- [ ] Email que colisiona → **409**; id inexistente → **404**; cuerpo inválido → **422**.

**Reglas relacionadas**: RN-11, RN-01, RN-12

### US-006 — Baja de dueño
**Como** personal de la veterinaria
**Quiero** dar de baja un dueño
**Para** limpiar el padrón

**Criterios de aceptación**:
- [ ] `DELETE /duenios/{id}` responde **204** sin cuerpo.
- [ ] Dueño con mascotas a su nombre → **409** (lo decide la base con RESTRICT).
- [ ] Id inexistente → **404**.

**Reglas relacionadas**: RN-08, RN-12

### US-007 — Alta de ficha
**Como** dueño de mascota
**Quiero** cargar mi teléfono y dirección
**Para** que la veterinaria pueda contactarme

**Criterios de aceptación**:
- [ ] `POST /duenios/{id}/ficha` responde **201** con `FichaRead`.
- [ ] Segunda ficha para el mismo dueño → **409**.
- [ ] Dueño inexistente → **404**.

**Reglas relacionadas**: RN-03, RN-12

## Épica 3: Mascotas

### US-008 — Alta de mascota
**Como** dueño de mascota
**Quiero** registrar mi mascota a mi nombre
**Para** poder reservarle turnos

**Criterios de aceptación**:
- [ ] `POST /mascotas/` recibe `duenio_id` de un dueño existente y responde **201** con `MascotaRead`.
- [ ] Dueño inexistente → **409**.
- [ ] Cuerpo inválido → **422**.

**Reglas relacionadas**: RN-12

### US-009 — Listado paginado de mascotas
**Como** personal de la veterinaria
**Quiero** recorrer las mascotas paginadas
**Para** consultarlas sin traer todo

**Criterios de aceptación**:
- [ ] `GET /mascotas/?page=&size=` devuelve `{ items, total, page, size, pages }`.
- [ ] `size` vale 20 por defecto y va de 1 a 100.
- [ ] Página más allá de `pages` → **422**; la primera página siempre responde aunque esté vacía.

**Reglas relacionadas**: RN-13, RN-12

### US-010 — Detalle de mascota con su dueño
**Como** personal de la veterinaria
**Quiero** ver la mascota junto con su dueño
**Para** saber a quién pertenece

**Criterios de aceptación**:
- [ ] `GET /mascotas/{id}` responde **200** con la mascota y su dueño.
- [ ] Lectura con carga anticipada de la relación «a uno».
- [ ] Id inexistente → **404**.

**Reglas relacionadas**: RN-14, RN-15

### US-011 — Mascotas de un dueño
**Como** personal de la veterinaria
**Quiero** listar las mascotas de un dueño
**Para** atender un caso por titular

**Criterios de aceptación**:
- [ ] `GET /duenios/{id}/mascotas` responde **200** con las mascotas del dueño.
- [ ] Dueño inexistente → **404**.

## Épica 4: Prácticas

### US-012 — Alta de práctica
**Como** personal de la veterinaria
**Quiero** agregar una práctica con su precio
**Para** mantener el catálogo de servicios

**Criterios de aceptación**:
- [ ] `POST /practicas/` responde **201** con `PracticaRead`.
- [ ] Precio ≤ 0 → rechazado por el DTO (**422**) y por el `CHECK` de la base.
- [ ] Nombre repetido → **409**.

**Reglas relacionadas**: RN-02, RN-04, RN-12

### US-013 — Catálogo de prácticas
**Como** personal de la veterinaria
**Quiero** ver el catálogo completo
**Para** elegir qué prácticas reservar

**Criterios de aceptación**:
- [ ] `GET /practicas/` responde **200** con el catálogo.

## Épica 5: Turnos

### US-014 — Reserva de turno con sus prácticas
**Como** dueño de mascota
**Quiero** reservar un turno indicando mascota, fecha, motivo y las prácticas
**Para** que atiendan a mi mascota

**Criterios de aceptación**:
- [ ] `POST /turnos/` recibe `mascota_id`, `fecha`, `motivo` y `practicas: [{ practica_id }]`.
- [ ] El cuerpo **no** lleva precio por práctica ni total.
- [ ] La lista de prácticas tiene al menos una; si está vacía → **422**.
- [ ] El precio de cada práctica se copia del catálogo y el total lo calcula el servidor.
- [ ] Práctica repetida en el mismo turno → **409** (PK compuesta).
- [ ] Práctica inexistente → **409** y **no queda guardado nada**.
- [ ] Responde **201** con el turno, su mascota y sus prácticas con `precio_unitario`.

**Reglas relacionadas**: RN-05, RN-06, RN-07, RN-23

### US-015 — Detalle de turno
**Como** personal de la veterinaria
**Quiero** ver un turno con su mascota y sus prácticas
**Para** preparar la atención

**Criterios de aceptación**:
- [ ] `GET /turnos/{id}` responde **200** con turno, mascota y prácticas.
- [ ] Usa `joinedload` para mascota y `selectinload` para prácticas.
- [ ] La cantidad de consultas no crece con la cantidad de prácticas.
- [ ] Id inexistente → **404**.

**Reglas relacionadas**: RN-14, RN-15, RN-16

### US-016 — Baja de turno
**Como** personal de la veterinaria
**Quiero** cancelar un turno
**Para** liberar la agenda

**Criterios de aceptación**:
- [ ] `DELETE /turnos/{id}` responde **204**.
- [ ] Las filas de `turno_practica` desaparecen por `ON DELETE CASCADE` de la base (no por el ORM).
- [ ] Id inexistente → **404**.

**Reglas relacionadas**: RN-09, RN-12

## Épica 6: Laboratorio

### US-017 — Consulta de stock de vacuna
**Como** personal de la veterinaria
**Quiero** consultar el stock de una vacuna en el laboratorio
**Para** saber si puedo reservar la práctica

**Criterios de aceptación**:
- [ ] `GET /laboratorio/stock/{vacuna}` responde `{ "vacuna": ..., "stock": ... }`.
- [ ] Invoca `consultar_stock` de `app/modules/laboratorio/cliente.py` **sin modificarla**.
- [ ] La llamada sincrónica no bloquea el event loop: `GET /health/live` responde de inmediato con consultas en curso.

**Reglas relacionadas**: RN-17, RN-18, RN-19

## Épica 7: Operación del repositorio

### US-018 — Reinicio con datos conocidos
**Como** evaluador
**Quiero** dejar la base en un estado conocido
**Para** correr los casos de prueba siempre desde el mismo punto

**Criterios de aceptación**:
- [ ] `python reiniciar.py` borra las tablas, las crea con `create_all` y carga los datos iniciales.
- [ ] Carga al menos: 2 dueños (uno con ficha), 3 mascotas, 4 prácticas, 1 turno con 2 prácticas.

**Reglas relacionadas**: —

### US-019 — Casos de prueba en `.http`
**Como** evaluador
**Quiero** archivos `.http` con los casos C-01 a C-09
**Para** verificar el comportamiento esperado

**Criterios de aceptación**:
- [ ] Cada caso indica en un comentario la respuesta esperada.
- [ ] Se corren después de `python reiniciar.py`.
- [ ] Incluye el archivo `.sql` del caso C-08 y la evidencia de consola del C-07.

**Reglas relacionadas**: —
