from fastapi import APIRouter

from .service import consultar_stock_service

router = APIRouter(prefix="/laboratorio", tags=["laboratorio"])


@router.get("/stock/{vacuna}")
async def consultar_stock_endpoint(vacuna: str) -> dict:
    return await consultar_stock_service(vacuna)
