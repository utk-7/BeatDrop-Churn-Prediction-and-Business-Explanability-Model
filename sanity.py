import asyncio
from app.main import lifespan, app

async def test():
    async with lifespan(app):
        pass

asyncio.run(test())
