from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.mascotas.models import Mascota
    from app.modules.practicas.models import Practica


class Turno(SQLModel, table=True):
    """Turno de una mascota. `total` es la suma de los precios unitarios (RN-06)."""

    __tablename__ = "turno"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_turno_total_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    # Sin ondelete: queda el default de PostgreSQL (NO ACTION, DD-13).
    mascota_id: int = Field(foreign_key="mascota.id", index=True)
    fecha: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    motivo: str
    total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    mascota: "Mascota" = Relationship(back_populates="turnos")
    practicas: list["TurnoPractica"] = Relationship(
        back_populates="turno", passive_deletes=True
    )


class TurnoPractica(SQLModel, table=True):
    """Práctica reservada en un turno, con el precio congelado al reservar (DD-07)."""

    __tablename__ = "turno_practica"
    __table_args__ = (
        CheckConstraint(
            "precio_unitario > 0",
            name="ck_turno_practica_precio_unitario_positivo",
        ),
    )

    turno_id: int = Field(primary_key=True, foreign_key="turno.id", ondelete="CASCADE")
    # Sin ondelete: queda el default de PostgreSQL (NO ACTION, DD-13).
    practica_id: int = Field(primary_key=True, foreign_key="practica.id", index=True)
    precio_unitario: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))

    turno: "Turno" = Relationship(back_populates="practicas")
    practica: "Practica" = Relationship(back_populates="turnos")
