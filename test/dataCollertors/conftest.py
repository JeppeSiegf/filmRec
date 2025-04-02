import aiohttp
import pytest


@pytest.fixture
async def aiohttp_session():
    async with aiohttp.ClientSession() as session:
        yield session
