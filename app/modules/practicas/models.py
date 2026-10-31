from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.turnos.models import TurnoPractica


class Practica(SQLModel, table=True):
    """Catálogo de prácticas. Independiente: no tiene claves foráneas."""

    __tablename__ = "practica"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_practica_precio_positivo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))

    turnos: list["TurnoPractica"] = Relationship(back_populates="practica")
