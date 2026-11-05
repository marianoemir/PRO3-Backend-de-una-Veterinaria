from pydantic import BaseModel, ConfigDict, Field, field_validator


class DuenioCreate(BaseModel):
    """Alta de dueño: sin `id`, la base lo genera (RN-10)."""

    nombre: str = Field(min_length=1)
    email: str = Field(min_length=1)


class FichaRead(BaseModel):
    id: int
    duenio_id: int
    telefono: str
    direccion: str

    model_config = ConfigDict(from_attributes=True)


class FichaCreate(BaseModel):
    """Alta de ficha: `telefono` y `direccion` obligatorios (DD-12)."""

    telefono: str = Field(min_length=1)
    direccion: str = Field(min_length=1)


class DuenioRead(BaseModel):
    id: int
    nombre: str
    email: str
    ficha: FichaRead | None

    model_config = ConfigDict(from_attributes=True)


class DuenioUpdate(BaseModel):
    """PATCH parcial: solo se aplican los campos enviados (RN-11, DD-08)."""

    nombre: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=1)

    @field_validator("nombre", "email")
    @classmethod
    def _no_null_explicito(cls, valor: str | None) -> str | None:
        """Omitir el campo es válido; enviarlo como `null` no: ambas columnas son NOT NULL."""
        if valor is None:
            raise ValueError("el campo no puede ser null; omitilo para no modificarlo")
        return valor


class MascotaResumenRead(BaseModel):
    """Vista resumida propia de este módulo; no importa DTO de `mascotas` (RN-10)."""

    id: int
    nombre: str
    especie: str

    model_config = ConfigDict(from_attributes=True)

