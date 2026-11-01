from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TurnoPracticaCreate(BaseModel):
    """Práctica pedida en el alta: solo el id, porque el precio lo pone el servidor (RN-06)."""

    practica_id: int


class TurnoCreate(BaseModel):
    """Cuerpo del alta de turno: ni precio por práctica ni total viajan desde el cliente (RN-06)."""

    mascota_id: int
    fecha: datetime
    motivo: str
    practicas: list[TurnoPracticaCreate] = Field(min_length=1)


class MascotaResumenRead(BaseModel):
    """Vista resumida de mascota, propia del módulo turnos (no se importa de `mascotas`)."""

    id: int
    nombre: str
    especie: str


class TurnoPracticaRead(BaseModel):
    """Práctica reservada en el turno: sin id de fila, porque `turno_practica` no lo tiene (DD-11)."""

    practica_id: int
    nombre: str
    precio_unitario: Decimal


class TurnoRead(BaseModel):
    """Turno reservado con su mascota y sus prácticas, en el orden del ejemplo de la consigna."""

    id: int
    fecha: datetime
    motivo: str
    total: Decimal
    mascota: MascotaResumenRead
    practicas: list[TurnoPracticaRead]
