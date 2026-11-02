from pydantic import BaseModel, ConfigDict


class DuenioCreate(BaseModel):
    """Alta de dueño: sin `id`, la base lo genera (RN-10)."""

    nombre: str
    email: str


class FichaRead(BaseModel):
    id: int
    duenio_id: int
    telefono: str
    direccion: str

    model_config = ConfigDict(from_attributes=True)


class FichaCreate(BaseModel):
    """Alta de ficha: `telefono` y `direccion` obligatorios (DD-12)."""

    telefono: str
    direccion: str


class DuenioRead(BaseModel):
    id: int
    nombre: str
    email: str
    ficha: FichaRead | None

    model_config = ConfigDict(from_attributes=True)


class DuenioUpdate(BaseModel):
    """PATCH parcial: solo se aplican los campos enviados (RN-11, DD-08)."""

    nombre: str | None = None
    email: str | None = None


class MascotaResumenRead(BaseModel):
    """Vista resumida propia de este módulo; no importa DTO de `mascotas` (RN-10)."""

    id: int
    nombre: str
    especie: str

    model_config = ConfigDict(from_attributes=True)

