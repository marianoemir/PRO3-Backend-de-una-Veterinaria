from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.duenios.models import Duenio
    from app.modules.turnos.models import Turno


class Mascota(SQLModel, table=True):
    """Mascota de un dueño. RESTRICT impide borrar un dueño con mascotas (RN-08)."""

    __tablename__ = "mascota"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    especie: str
    duenio_id: int = Field(foreign_key="duenio.id", ondelete="RESTRICT", index=True)

    duenio: "Duenio" = Relationship(back_populates="mascotas")
    turnos: list["Turno"] = Relationship(back_populates="mascota")
