from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.mascotas.models import Mascota


class Duenio(SQLModel, table=True):
    """Dueño de mascotas. Raíz del grafo: no tiene claves foráneas."""

    __tablename__ = "duenio"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)

    ficha: Optional["FichaDuenio"] = Relationship(
        back_populates="duenio", sa_relationship_kwargs={"uselist": False}
    )
    mascotas: list["Mascota"] = Relationship(back_populates="duenio")


class FichaDuenio(SQLModel, table=True):
    """Datos adicionales del dueño: uno a uno, la ficha no existe sin él."""

    __tablename__ = "ficha_duenio"

    id: int | None = Field(default=None, primary_key=True)
    # Sin ondelete: queda el default de PostgreSQL (NO ACTION, DD-13).
    duenio_id: int = Field(foreign_key="duenio.id", unique=True)
    telefono: str
    direccion: str

    duenio: "Duenio" = Relationship(back_populates="ficha")
