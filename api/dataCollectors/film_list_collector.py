import asyncio
import aiohttp
from api.dataCollectors.page_parser import PageParser


class FilmListCollector(PageParser):  # Inherit from PageParser
    def __init__(self, user: str, title: str) -> None:
        if not user.isalnum():
            raise Exception("Invalid user")

        self.url = f"https://letterboxd.com/{user}/list/{title}/detail/"
        self.filmCount = None
        self.movies = []

    async def fetch_film_list(self):
        async with aiohttp.ClientSession() as session:
            self.movies = await self.fetch_data(self.get_basic_film_info, self.url, session)
            self.filmCount = len(self.movies)

        if self.filmCount == 0:
            raise Exception("No list exists")

    async def get_basic_film_info(self, session, page_url):
        page = await self.get_parsed_page(session, page_url)
        img = page.find("ul", {"class": ["js-list-entries", "poster-list", "-p125", "-grid", "film-list"]})
        if not img:
            return []

        titles = img.find_all("img", {"class": ["image"]})
        years = img.find_all('small', {"class": ["metadata"]})

        movie_list = []

        for title_item, year_item in zip(titles, years):
            movie_url = title_item.parent.get('data-film-slug', '')
            movie_title = title_item.get('alt', '')
            movie_year = year_item.find('a').text.strip() if year_item.find('a') else "Unknown"

            movie_list.append((movie_title, movie_url, movie_year))

        return movie_list


async def main():
    collector = FilmListCollector('brthrash', 'directors')
    await collector.fetch_film_list()
    movielist = collector.movies
    print(movielist)


if __name__ == "__main__":
    asyncio.run(main())