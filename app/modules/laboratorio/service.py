import asyncio

from .cliente import consultar_stock


async def consultar_stock_service(vacuna: str) -> dict:
    stock = await asyncio.to_thread(consultar_stock, vacuna)
    return {"vacuna": vacuna, "stock": stock}
