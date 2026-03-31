import pytest
import aiohttp
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession


from dataCollectors.utils.page_parser import PageParser

URLS = [
    "https://letterboxd.com",
    "https://letterboxd.com/films",
    "https://letterboxd.com/films/popular",
    # Film Detail Parser
    "https://letterboxd.com/film/pulp-fiction/",
    # Film List
    "https://letterboxd.com/jack/list/2025/",
    "https://letterboxd.com/jack/list/2025/page/1/",
    "https://letterboxd.com/jack/list/2025/page/2/",
    "https://letterboxd.com/jack/list/2025/page/3/"
    # --
    "https://letterboxd.com/jack/list/2025/detail",
    "https://letterboxd.com/jack/list/2025/detail/page/1/",
    "https://letterboxd.com/jack/list/2025/detail/page/2/",
    "https://letterboxd.com/jack/list/2025/detail/page/3/",
    # Member Collector
    "https://letterboxd.com/film/maya-deren-take-zero/members/",
    # Ratings Collector
    "https://letterboxd.com/jack/films/"



]


# @pytest.mark.asyncio
# @pytest.mark.parametrize("url", URLS)
# async def test_returns_beautifulsoup(url):
#     async with aiohttp.ClientSession() as session:
#         result = await PageParser.get_parsed_page(session, url)
#         assert isinstance(result, BeautifulSoup)


# @pytest.mark.asyncio
# @pytest.mark.parametrize("url", URLS)
# async def test_url_returns_200(url):
#
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, headers=headers) as response:
#             if response.status != 200:
#                 body = await response.text()
#                 pytest.fail(
#                     f"\n{'='*60}"
#                     f"\nURL:     {url}"
#                     f"\nStatus:  {response.status}"
#                     f"\nHeaders: {dict(response.headers)}"
#                     f"\nBody:\n{body[:2000]}"
#                     f"\n{'='*60}"
#                 )





@pytest.fixture
async def session():
    async with AsyncSession() as s:
        yield s


@pytest.mark.asyncio
@pytest.mark.parametrize("url", URLS)
async def test_url_returns_200(url):
    async with AsyncSession() as session:
        response = await session.get(url, impersonate="chrome")
        if response.status_code != 200:
            pytest.fail(
                f"\n{'='*60}"
                f"\nURL:     {url}"
                f"\nStatus:  {response.status_code}"
                f"\nHeaders: {dict(response.headers)}"
                f"\nBody:\n{response.text[:2000]}"
                f"\n{'='*60}"
            )


@pytest.mark.asyncio
@pytest.mark.parametrize("url", URLS)
async def test_page_is_parseable(url):
    async with AsyncSession() as session:
        response = await session.get(url, impersonate="chrome")
        assert response.status_code == 200
        dom = BeautifulSoup(response.text, "lxml")
        assert dom.find("body") is not None
        assert "just a moment" not in dom.find("title").text.lower(), \
            f"Cloudflare challenge page still returned for {url}"