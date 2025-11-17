import aiohttp
from bs4 import BeautifulSoup
import re
import asyncio

from dataCollectors.utils.page_collector import PageCollector
from dataCollectors.utils.session_manager import SessionManager


class ThemeCollector(PageCollector,SessionManager):
    BASE_URL = "https://letterboxd.com/film/{film_slug}/{theme_type}/"

    def __init__(self, film_slug: str, film_ref, nanogenre: bool = False):
        super().__init__(film_ref)
        if not isinstance(film_slug, str):
            raise ValueError(f"Invalid film slug: {film_slug}")
        self.film_slug = film_slug
        if nanogenre is True:
            self.url = self.BASE_URL.format(film_slug=film_slug,theme_type='nanogenres')
        else:
            self.url = self.BASE_URL.format(film_slug=film_slug,theme_type='themes')

        self.dom = None
        self.themes = []  # list of dicts: {"name": str, "slug": str, "films": [film_slugs]}

    async def fetch_page(self, session: aiohttp.ClientSession = None):
        if session is None:
            async with aiohttp.ClientSession() as temp_session:
                self.dom = await self._get_dom(temp_session)
        else:
            self.dom = await self._get_dom(session)

    async def _get_dom(self, session: aiohttp.ClientSession):
        async with session.get(self.url) as resp:
            html = await resp.text()
            return BeautifulSoup(html, "html.parser")

    async def extract_details(self):
        if self.dom is None:
            raise ValueError("DOM is not loaded. Call fetch_page() first.")

        theme_sections = self.dom.find_all("section", class_="genre-group")
        for section in theme_sections:
            theme_data = {
                "name": None,
                "slug": None,
            }

            # Extract theme name & slug
            title_link = section.find("h2", class_="title").find("a", href=True)
            if title_link:
                label_span = title_link.find("span", class_="label")
                if label_span:
                    theme_data["name"] = label_span.text.strip()

                match = re.search(r'/films/(?:theme|mini-theme|nanogenre)/([^/]+)/', title_link["href"])
                if match:
                    theme_data["slug"] = match.group(1)

            # Extract films in this theme

            self.themes.append(theme_data)


async def main():
    collector = ThemeCollector("regeneration",True)
    await collector.fetch_page()
    await collector.extract_details()
    print(collector.themes)

asyncio.run(main())