import asyncio
from json import loads
import aiohttp
from api.dataCollectors.page_parser import PageParser


class FilmDetailCollector(PageParser):
    def __init__(self, film_ref: str) -> None:
        if not isinstance(film_ref, str):
            raise ValueError(f'Invalid film reference: {film_ref}')

        self.ref = film_ref
        self.url = f"https://letterboxd.com/film/{film_ref}/"

        self.dom = None
        self.script = None


        self.title = ''
        self.release_year = 0
        self.total_watches = 0
        self.image_ref = ''
        self.genre = []

        self.director = {}


    async def fetch_page(self):
        async with aiohttp.ClientSession() as session:
            result = await self.get_parsed_page(session, self.url)
            self.dom = result[0]
            self.script = result[1]


    async def fetch_page_script(self, dom):
        if self.dom is None:
            raise ValueError("DOM is not initialized. Call fetch_page_dom first.")

        script = dom.find("script", type="application/ld+json")
        script = loads(script.text.split('*/')[1].split('/*')[0]) if script else None
        return script

    async def extract_details(self):
        script = await self.fetch_page_script(self.dom)
        if script:
            await asyncio.gather(
                self.get_title(self.dom),
                self.get_release_year(self.dom,script),
                self.get_film_genres(script),
                self.get_movie_poster(script),
                self.get_total_watches(script),
                self.get_director(script)

            )

    async def get_title(self, dom) -> str:
        elem = dom.find("h1", {"class": ["filmtitle"]})
        elem = elem.text if elem else None
        self.title = elem

    async def get_film_genres(self, script):

        if isinstance(script, dict) and 'genre' in script:
            genres = script['genre']
            # Ensure genres is a list of strings
            if isinstance(genres, list):
                for genre in genres:
                    if isinstance(genre, str):
                        # Append the genre to the genres list
                        self.genre.append(genre)

    async def get_movie_poster(self, script):

        # crop: list=(1500, 1000)
        # .replace('230-0-345', f'{crop[0]}-0-{crop[1]}')
        # crop: list=(1500, 1000)
        # .replace('230-0-345', f'{crop[0]}-0-{crop[1]}')
        if script:
            poster = script['image'] if 'image' in script else None
            self.image_ref = poster.split('?')[0] if poster else None
        else:
            self.image_ref = None

    # Actually returns amount of ratings rather than watches
    # Suitable replacement for now
    async def get_total_watches(self, script):

        if script:
            self.total_watches = script.get('aggregateRating', {}).get('ratingCount', None)
        else:
            self.total_watches = 0

    async def get_director(self, script):

        if isinstance(script, dict) and 'director' in script:
            directors = script['director']

            #
            if isinstance(directors, list):
                for director in directors:
                    if '@type' in director and director['@type'] == 'Person':
                        name = director.get('name', None)
                        reference = director.get('sameAs', None)

                        if name and reference:
                            # Add to the dictionary with name as key and reference as value
                            self.director[reference.split("/")[-2]] = name

            # If no director or sameAs values found, set an empty list
        if not self.director:
            self.director = []

    async def get_release_year(self, dom, script: dict = None) -> int:
        elem = dom.find('div', {'class': 'releaseyear'})
        year = elem.text if elem else None
        try:
            year = year if year else (
                script['releasedEvent'][0]['startDate'] if script else None
            )
            self.release_year = int(year)
        except (KeyError, ValueError):
            self.release_year = None


if __name__ == "__main__":
    film = FilmDetailCollector('the-matrix')
    # Note: We need to wait for the asynchronous initialization to complete
    asyncio.run(film.fetch_page())
    asyncio.run(film.extract_details())
    print(film.script)
    print(film.release_year)
    print(f"Total watches: {film.total_watches}")
    print(f"Genres: {film.genre}")
    print(f"Directors: {film.director}")

