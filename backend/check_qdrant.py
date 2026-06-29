import asyncio

from app.integrations.qdrant_client import (
    init_qdrant,
    get_collection_info,
)

async def main():
    await init_qdrant()

    info = await get_collection_info()

    print(info)

asyncio.run(main())