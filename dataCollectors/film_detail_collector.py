import asyncio
import re
from json import loads

import aiohttp
import unicodedata

from dataCollectors.utils.page_collector import PageCollector
from dataCollectors.utils.session_manager import SessionManager


class FilmDetailCollector(PageCollector, SessionManager):

    def __init__(self, film_ref: str) -> None:
        super().__init__(film_ref)
        if not isinstance(film_ref, str):
            raise ValueError(f'Invalid film reference: {film_ref}')

        self.ref = film_ref
        self.url = f"https://letterboxd.com/film/{film_ref}/"

        self.dom = None
        self.script = None

        # Initialize the data object with the schema structure
        self.data = {
            'page_ref': film_ref,
            'title': None,
            'title_original': None,
            'description': None,
            'image_ref': None,
            'image_ref_large': None,
            'banner_ref': None,
            'release_year': None,
            'runtime': None,
            'total_watches': None,
            'genres': [],
            'languages': [],
            'series_id': None,
            'crew': [],
            'cast': [],
            'imdb_ref': None,
            'avg_rating': None
        }


    async def fetch_page(self, session: aiohttp.ClientSession = None):
        if session is None:
            async with aiohttp.ClientSession() as temp_session:
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
                self.get_imdb_ref(self.dom),
                self.get_avg_rating(self.dom),
                self.get_series(self.dom),
            )

        # Update last_update timestamp after extraction


        self.dom = None
        self.script = None

    async def get_title(self, dom):
        h1_elem = dom.find("h1", {"class": "headline-1 primaryname"})
        if h1_elem:
            span_elem = h1_elem.find("span", {"class": "name js-widont prettify"})
            self.data['title'] = span_elem.text if span_elem else None

    async def get_title_original(self, dom):
        elem = dom.find("h2", {"class": ["originalname"]})
        self.data['title_original'] = elem.text if elem else None

    async def get_description(self, dom):
        elem = dom.find("div", {"class": ["truncate"]})
        self.data['description'] = elem.text.strip() if elem else None

    async def get_runtime(self, dom):
        elem = dom.find("p", {"class": ["text-link", "text-footer"]})
        if elem:
            text = elem.get_text(strip=True)
            runtime_match = re.search(r"(\d+)\s*mins", text)
            self.data['runtime'] = int(runtime_match.group(1)) if runtime_match else None
        else:
            self.data['runtime'] = None

    async def get_film_genres(self, script):
        if isinstance(script, dict) and 'genre' in script:
            genres = script['genre']
            if isinstance(genres, list):
                for genre in genres:
                    if isinstance(genre, str):
                        self.data['genres'].append(genre)

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
                    language_data.append({"name": lang_text, "is_primary": True})

        # Spoken languages (non-primary)
        spoken_section = dom.find("h3", string=re.compile(r"Spoken Languages", re.I))
        if spoken_section:
            spoken_langs = spoken_section.find_next("div", class_="text-sluglist").find_all("a", class_="text-slug")
            if spoken_langs:
                for lang in spoken_langs:
                    lang_text = clean_text(lang.text)
                    if lang_text not in primary_languages:
                        language_data.append({"name": lang_text, "is_primary": False})

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
                        language_data.append({"name": lang_text, "is_primary": is_primary})

        self.data['languages'] = language_data

    async def get_movie_poster(self, script):
        if script:
            poster = script['image'] if 'image' in script else None
            original_ref = poster.split('?')[0] if poster else None
            if original_ref:
                original_ref_large = original_ref.replace('-230-0-345', '-2000-0-3000')
                self.data['image_ref'] = original_ref
                self.data['image_ref_large'] = original_ref_large
        else:
            self.data['image_ref'] = None

    async def get_total_watches(self, script):
        if script:
            self.data['total_watches'] = script.get('aggregateRating', {}).get('ratingCount', 0)
        else:
            self.data['total_watches'] = 0

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

            current_role = None
            count = 1
            if role_container:
                for crew_link in role_container.find_all("a", class_="text-slug"):
                    href_parts = crew_link["href"].strip().split("/")
                    if len(href_parts) >= 3:
                        role = href_parts[1].lower()
                        if role == current_role:
                            count += 1
                            rank = count
                        else:
                            current_role = role
                            count = 1
                            rank = count

                        ref = href_parts[-2]
                        name = crew_link.text.strip()

                        crew_list.append({"role": role, "ref": ref, "name": name, "rank": rank})

        self.data['crew'] = crew_list

    async def get_cast(self, dom):
        cast_list = []

        # Find the cast container
        cast_container = dom.find("div", class_="cast-list text-sluglist")
        if cast_container:
            count = 1
            for actor_link in cast_container.find_all("a", class_="text-slug tooltip"):
                href_parts = actor_link["href"].strip().split("/")
                if len(href_parts) >= 3:
                    role = "actor"
                    ref = href_parts[-2]
                    name = actor_link.text.strip()
                    rank = count
                    count += 1

                    cast_list.append({"role": role, "ref": ref, "name": name, "rank": rank})

        self.data['cast'] = cast_list

    async def get_release_year(self, dom, script: dict = None):
        elem = dom.find('div', {'class': 'releaseyear'})
        year = elem.text if elem else None
        try:
            year = year if year else (
                script['releasedEvent'][0]['startDate'] if script else None
            )
            self.data['release_year'] = int(year)
        except (KeyError, ValueError):
            self.data['release_year'] = None

    async def get_banner(self, dom):
        banner_div = dom.find('div', id='backdrop')
        backdrop = None
        if banner_div:
            backdrop = banner_div.get('data-backdrop2x')
        if backdrop is None:
            backdrop = banner_div.get('data-backdrop')
        self.data['banner_ref'] = backdrop

    async def get_imdb_ref(self, dom):
        imdb_link = dom.find('a', href=re.compile(r'imdb\.com/title/tt\d+'))
        imdb_id = None
        if imdb_link:
            match = re.search(r'(tt\d+)', imdb_link.get('href'))
            if match:
                imdb_id = match.group(1)
        self.data['imdb_ref'] = imdb_id

    async def get_avg_rating(self, dom):
        rating_meta = dom.find('meta', attrs={'name': 'twitter:data2'})
        avg_rating = None
        if rating_meta:
            content = rating_meta.get('content')
            match = re.search(r'([\d.]+)', content)
            if match:
                avg_rating = float(match.group(1))
        self.data['avg_rating'] = avg_rating

    async def get_series(self, dom):
        series_section = dom.find('section', id='related')
        series_slug = None
        if series_section:
            heading_link = series_section.find('h2', class_='section-heading')
            if heading_link:
                a_tag = heading_link.find('a', href=True)
                if a_tag:
                    match = re.search(r'/films/in/([^/]+)/', a_tag['href'])
                    if match:
                        series_slug = match.group(1)
        self.data['series_id'] = series_slug

    def get_data(self):
        """Return the collected data as a dictionary"""
        return self.data.copy()


if __name__ == "__main__":
    asyncio.run(FilmDetailCollector.enable_shared_session())

    film = FilmDetailCollector('regeneration-1923')
    film2 = FilmDetailCollector('pulp')
    film3 = FilmDetailCollector('hero-2002')
    samples = ['pulp-fiction', 'the-rabbis-cat', 'pokemon-the-movie-2000', 'hero-2002', 'barbie']

    asyncio.run(film.fetch_page())
    asyncio.run(film.extract_details())

    asyncio.run(film2.fetch_page())
    asyncio.run(film2.extract_details())

    asyncio.run(film3.fetch_page())
    asyncio.run(film3.extract_details())

    asyncio.run(FilmDetailCollector.disable_shared_session())

    print(f"Film data: {film2.data}")