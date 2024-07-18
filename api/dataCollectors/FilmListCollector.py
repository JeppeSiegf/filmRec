import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def fetch_page(session, url):
    headers = {
        "referer": "https://letterboxd.com",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    async with session.get(url, headers=headers) as response:
        return await response.text()


class FilmListCollector:
    def __init__(self, author: str, title: str) -> None:
        if not author.isalnum():
            raise Exception("Invalid author")

        self.filmCount = None
        self.movies = []

    async def get_parsed_page(self, session, url: str) -> BeautifulSoup:
        page_content = await fetch_page(session, url)
        return BeautifulSoup(page_content, 'html.parser')

    async def fetch_movie_info(self, session, page_url):

        page = await self.get_parsed_page(session, page_url)

        img = page.find("ul", {"class": ["js-list-entries", "poster-list", "-p125", "-grid", "film-list"]})
        if not img:
            return []

        titles = img.find_all("img", {"class": ["image"]})
        years = img.find_all('small', {"class": ["metadata"]})

        movie_list = []
        for item in titles:
            movie_url = item.parent.get('data-film-slug', '')
            movie_id = item.parent.get('data-film-id', '')
            movie_list.append((item.get('alt', ''), movie_url, movie_id))

        year_list = []
        for item in years:
            movie_year = item.find('a').text.strip()
            year_list.append(movie_year)

        for i in range(len(movie_list)):
            movie_list[i] = movie_list[i] + (year_list[i],)

        return movie_list

    async def film_count(self):
        page = 1
        movie_list = []
        prev, curr = 0, 1
        concurrency = 100  # Adjust as per your system's capability
        semaphore = asyncio.Semaphore(concurrency)

        async with aiohttp.ClientSession() as session:
            while prev != curr:
                page_url = f"{self.url}page/{page}/"
                async with semaphore:
                    movies = await self.fetch_movie_info(session, page_url)
                    movie_list.extend(movies)

                prev = curr
                curr = len(movie_list)
                page += 1

        self.filmCount = len(movie_list)
        self.movies = movie_list

        if self.filmCount == 0:
            raise Exception("No list exists")
