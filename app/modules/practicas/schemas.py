from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PracticaCreate(BaseModel):
    nombre: str
    precio: Decimal = Field(gt=0)


class PracticaRead(BaseModel):
    id: int
    nombre: str
    precio: Decimal

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("precio")
    def _serialize_precio(self, v: Decimal) -> str:
        return f"{v:.2f}"
