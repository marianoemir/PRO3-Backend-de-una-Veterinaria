from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import crear_fabrica, crear_motor
from app.modules.duenios.router import router as duenios_router
from app.modules.health.router import router as health_router
from app.modules.laboratorio.router import router as laboratorio_router
from app.modules.mascotas.router import router as mascotas_router
from app.modules.practicas.router import router as practicas_router
from app.modules.turnos.router import router as turnos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = crear_motor(settings.DATABASE_URL)
    session_local = crear_fabrica(engine)
    app.state.engine = engine
    app.state.session_local = session_local
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)
app.include_router(duenios_router)
app.include_router(mascotas_router)
app.include_router(practicas_router)
app.include_router(turnos_router)
app.include_router(laboratorio_router)