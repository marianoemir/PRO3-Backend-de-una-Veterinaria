from fastapi import Request


async def get_session(request: Request):
    """Toma el async_sessionmaker de app.state, crea una sesión y la cierra al terminar."""
    async with request.app.state.session_local() as session:
        yield session