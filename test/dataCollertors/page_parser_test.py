import aiohttp
import pytest

from api.dataCollectors.utils.page_parser import PageParser


@pytest.mark.asyncio
async def test_real_get_parsed_page():
    url = "https://letterboxd.com/films/"

    async with aiohttp.ClientSession() as session:
        parsed_page = await PageParser.get_parsed_page(session, url)

    assert parsed_page is not None
    assert parsed_page.find("body") is not None  # Ensure body existsists


@pytest.mark.asyncio
async def test_fetch_page_real():
    """Test `__fetch_page` with a real URL using an actual session."""

    url = "https://letterboxd.com"

    async with aiohttp.ClientSession() as session:  # Explicitly create session
        response = await PageParser._PageParser__fetch_page(session, url)

    assert response is not None
    assert "html" in response.lower()
