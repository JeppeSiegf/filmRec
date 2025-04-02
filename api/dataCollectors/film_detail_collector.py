import asyncio
import os
import re
import urllib.parse
from json import loads
import aiohttp
import unicodedata
from aiohttp import ClientConnectionError
from flask import request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from api.dataCollectors.page_parser import PageParser


class FilmDetailCollector(PageParser):

    _shared_session = None

    @classmethod
    async def enable_shared_session(cls):
        """
        Enables a shared session with custom settings.
        All subsequent FilmDetailCollector instances will reuse this session.
        """
        if cls._shared_session is None or cls._shared_session.closed:
            timeout = aiohttp.ClientTimeout(
                total=None,
                connect=300,
                sock_connect=300,
                sock_read=300
            )
            connector = aiohttp.TCPConnector(limit_per_host=20, force_close=False, ssl=False)
            cls._shared_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'Connection': 'keep-alive'}
            )

    @classmethod
    async def disable_shared_session(cls):
        """
        Closes and clears the shared session.
        """
        if cls._shared_session and not cls._shared_session.closed:
            await cls._shared_session.close()
            cls._shared_session = None

    def __init__(self, film_ref: str) -> None:
        if not isinstance(film_ref, str):
            raise ValueError(f'Invalid film reference: {film_ref}')

        self.ref = film_ref
        self.url = f"https://letterboxd.com/film/{film_ref}/"

        self.dom = None
        self.script = None

        self.title = ''
        self.title_original = ''
        self.description = ''
        self.release_year = 0
        self.runtime = 0
        self.total_watches = 0
        self.image_ref = ''
        self.image_ref_large = ''
        self.banner_ref = ''

        self.genre = []
        self.languages = {}
        self.crew = {}
        self.cast = {}


    async def fetch_page(self, session: aiohttp.ClientSession = None):
        """
        Fetches and parses the film page.
        If a session is provided, that session is used.
        Otherwise, a new session is created and closed after use.
        """
        if session is None:
            # Create a temporary session with custom settings.
            timeout = aiohttp.ClientTimeout(
                total=None,
                connect=300,
                sock_connect=300,
                sock_read=300
            )
            connector = aiohttp.TCPConnector(limit_per_host=20, force_close=False, ssl=False)
            async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={'Connection': 'keep-alive'}
            ) as temp_session:
                self.dom = await self.get_parsed_page(temp_session, self.url)
        else:
            self.dom = await self.get_parsed_page(session, self.url)

    async def fetch_page_script(self, dom):
        if self.dom is None:
            raise ValueError("DOM is not initialized. Call fetch_page_dom first.")

        script = dom.find("script", type="application/ld+json")
        script = loads(script.text.split('*/')[1].split('/*')[0]) if script else None
        return script

    async def extract_details(self):

        self.script = await self.fetch_page_script(self.dom)
        if self.script:
            await asyncio.gather(
                self.get_title(self.dom),
                self.get_title_original(self.dom),
                self.get_description(self.dom),
                self.get_release_year(self.dom, self.script),
                self.get_runtime(self.dom),
                self.get_film_genres(self.script),
                self.get_languages(self.dom),
                self.get_movie_poster(self.script),
                self.get_total_watches(self.script),
                self.get_full_crew(self.dom),
                self.get_cast(self.dom),
                self.get_banner(self.dom),

            )

    async def get_title(self, dom):
        elem = dom.find("h1", {"class": ["filmtitle"]})
        elem = elem.text if elem else None
        self.title = elem

    async def get_title_original(self, dom):
        elem = dom.find("h2", {"class": ["originalname"]})
        elem = elem.text if elem else None
        self.title_original = elem

    async def get_description(self, dom):
        elem = dom.find("div", {"class": ["truncate"]})
        self.description = elem.text.strip() if elem else None

    async def get_runtime(self, dom):
        elem = dom.find("p", {"class": ["text-link", "text-footer"]})
        if elem:
            text = elem.get_text(strip=True)
            runtime_match = re.search(r"(\d+)\s*mins", text)  # Extracts the number before "mins"
            self.runtime = int(runtime_match.group(1)) if runtime_match else None
        else:
            self.runtime = None

    async def get_film_genres(self, script):

        if isinstance(script, dict) and 'genre' in script:
            genres = script['genre']
            # Ensure genres is a list of strings
            if isinstance(genres, list):
                for genre in genres:
                    if isinstance(genre, str):
                        # Append the genre to the genres list
                        self.genre.append(genre)

    async def get_languages(self, dom):
        language_data = []
        primary_languages = set()

        def clean_text(text):
            return unicodedata.normalize("NFKC", text.strip())

        # Primary languages
        primary_section = dom.find("h3", string=re.compile(r"Primary Language", re.I))
        if primary_section:
            primary_langs = primary_section.find_next("div", class_="text-sluglist").find_all("a", class_="text-slug")
            if primary_langs:
                for lang in primary_langs:
                    lang_text = clean_text(lang.text)
                    primary_languages.add(lang_text)
                    # Use a dictionary with "name" and "is_primary" keys
                    language_data.append({"name": lang_text, "is_primary": True})  # Fixed

        # Spoken languages (non-primary)
        spoken_section = dom.find("h3", string=re.compile(r"Spoken Languages", re.I))
        if spoken_section:
            spoken_langs = spoken_section.find_next("div", class_="text-sluglist").find_all("a", class_="text-slug")
            if spoken_langs:
                for lang in spoken_langs:
                    lang_text = clean_text(lang.text)
                    if lang_text not in primary_languages:
                        language_data.append({"name": lang_text, "is_primary": False})  # Fixed

        # Fallback for generic "Language" field
        if not language_data:
            generic_section = dom.find("h3", string=re.compile(r"Language", re.I))
            if generic_section:
                generic_langs = generic_section.find_next("div", class_="text-sluglist").find_all("a",
                                                                                                  class_="text-slug")
                if generic_langs:
                    is_primary = len(generic_langs) == 1
                    for lang in generic_langs:
                        lang_text = clean_text(lang.text)
                        language_data.append({"name": lang_text, "is_primary": is_primary})  # Fixed

        self.languages = language_data  # Now a list of dictionaries

    async def get_movie_poster(self, script):

        # crop: list=(1500, 1000)
        # .replace('230-0-345', f'{crop[0]}-0-{crop[1]}')
        # crop: list=(1500, 1000)
        # .replace('230-0-345', f'{crop[0]}-0-{crop[1]}')


        if script:
            poster = script['image'] if 'image' in script else None
            original_ref = poster.split('?')[0] if poster else None
            if original_ref:
                original_ref_large = original_ref.replace('-230-0-345', '-2000-0-3000')
                self.image_ref = self.proxify_image_url(original_ref)
                self.image_ref_large = self.proxify_image_url(original_ref_large)

        else:
            self.image_ref = None





    # Actually returns amount of ratings rather than watches
    # Suitable replacement for now
    async def get_total_watches(self, script):

        if script:
            self.total_watches = script.get('aggregateRating', {}).get('ratingCount', None)
        else:
            self.total_watches = 0

    async def get_full_crew(self, dom):
        crew_list = []

        # Find all crew sections
        crew_sections = dom.find_all("h3")

        for section in crew_sections:
            role_elem = section.find("span", class_="crewrole -full")
            if not role_elem:
                continue

            # Find the role's corresponding crew list
            role_container = section.find_next_sibling("div", class_="text-sluglist")
            if role_container:
                for crew_link in role_container.find_all("a", class_="text-slug"):
                    href_parts = crew_link["href"].strip().split("/")
                    if len(href_parts) >= 3:
                        role = href_parts[1].lower()  # Extract role from URL
                        ref = href_parts[-2]  # Extract reference from URL
                        name = crew_link.text.strip()  # Extract displayed name

                        crew_list.append({"role": role, "ref": ref, "name": name})

        self.crew = crew_list

    async def get_cast(self, dom):
        cast_list = []

        # Find the cast container
        cast_container = dom.find("div", class_="cast-list text-sluglist")
        if cast_container:
            for actor_link in cast_container.find_all("a", class_="text-slug tooltip"):
                href_parts = actor_link["href"].strip().split("/")
                if len(href_parts) >= 3:
                    role = "actor"  # Fixed role for all cast members
                    ref = href_parts[-2]  # Extract reference from URL
                    name = actor_link.text.strip()  # Extract displayed name

                    cast_list.append({"role": role, "ref": ref, "name": name})

        self.cast = cast_list

    async def get_release_year(self, dom, script: dict = None):
        elem = dom.find('div', {'class': 'releaseyear'})
        year = elem.text if elem else None
        try:
            year = year if year else (
                script['releasedEvent'][0]['startDate'] if script else None
            )
            self.release_year = int(year)
        except (KeyError, ValueError):
            self.release_year = None

    async def resize_poster(self, poster_ref):
        pass

    async def get_banner(self, dom):
        banner_div = dom.find('div', id='backdrop')
        backdrop = None
        if banner_div:
            backdrop = banner_div.get('data-backdrop2x')
        if backdrop is None:
            backdrop = banner_div.get('data-backdrop')
        self.banner_ref = backdrop

    def proxify_image_url(self, original_url: str) -> str:
        api_base = os.getenv("API_BASE_URL", "http://localhost:5000")  # adjust as needed
        encoded_url = urllib.parse.quote(original_url, safe='')
        return f"{api_base}/api/proxy/image?url={encoded_url}"



if __name__ == "__main__":
    asyncio.run(FilmDetailCollector.enable_shared_session())

    film = FilmDetailCollector('pulp-fiction')
    film2 = FilmDetailCollector('the-rabbis-cat')
    film3 = FilmDetailCollector('hero-2002')
    samples = ['pulp-fiction', 'the-rabbis-cat', 'pokemon-the-movie-2000', 'hero-2002', 'barbie']
    # Note: We need to wait for the asynchronous initialization to complete
    asyncio.run(film.fetch_page())
    asyncio.run(film.extract_details())

    asyncio.run(film2.fetch_page())
    asyncio.run(film2.extract_details())

    asyncio.run(film3.fetch_page())
    asyncio.run(film3.extract_details())

    asyncio.run(FilmDetailCollector.disable_shared_session())

    print(film.image_ref_large)
    print(film2.image_ref)
    print(film3.image_ref)
    print(film.image_ref)
    print(film.release_year)
    print(film.runtime)
    print(film.image_ref_large)
    print(f"Total watches: {film.total_watches}")

