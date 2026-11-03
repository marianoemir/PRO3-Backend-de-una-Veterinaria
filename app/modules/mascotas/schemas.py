from pydantic import BaseModel, ConfigDict, Field


class MascotaCreate(BaseModel):
    """Alta de mascota: sin `id`, lo genera la base (RN-10)."""

    nombre: str
    especie: str = Field(min_length=1)
    duenio_id: int


class DuenioResumenRead(BaseModel):
    """Vista resumida propia de este módulo; no importa DTO de `duenios` (RN-10)."""

    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class MascotaRead(BaseModel):
    """Mascota con el dueño al que pertenece, ya precargado (RN-14)."""

    id: int
    nombre: str
    especie: str
    duenio: DuenioResumenRead

    model_config = ConfigDict(from_attributes=True)


class PaginaMascotasRead(BaseModel):
    """Envoltorio de paginación de `GET /mascotas/` (RN-13)."""

    items: list[MascotaRead]
    total: int
    page: int
    size: int
    pages: int
