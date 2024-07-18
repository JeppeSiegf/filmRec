import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup


async def fetch_page(session, url):
    headers = {
        "referer": "https://letterboxd.com",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    async with session.get(url, headers=headers) as response:
        return await response.text()


class UserRatingsCollector:
    def __init__(self, author) -> None:
        if not author.isalnum():
            raise Exception("Invalid author")
        self.user = author
        self.url = f"https://letterboxd.com/{self.user}/films/"
        self.filmCount = None
        self.movies = []

    async def get_parsed_page(self, session, url: str) -> BeautifulSoup:
        page_content = await fetch_page(session, url)
        return BeautifulSoup(page_content, 'html.parser')

    async def fetch_movie_info(self, session, page_url):

        page = await self.get_parsed_page(session, page_url)

        poster_containers = page.find_all("li", {"class": ["poster-container"], })
        if not poster_containers:

            return []

        watched_list = []

        for poster_container in poster_containers:
            poster = poster_container.div
            film_data = poster_container.find("img", {"class": "image"})
            film_slug = film_data.parent.get('data-film-slug', '')
            poster_viewingdata = poster_container.find("p", {"class": "poster-viewingdata"})
            print(poster_viewingdata)
            rating = None
            liked = False

            if poster_viewingdata.span:
                for span in poster_viewingdata.find_all("span"):
                    if 'rating' in span['class']:
                        rating = int(poster_viewingdata.span['class'][-1].split('-')[-1])
                        print(rating)
                    elif 'like' in span['class']:
                        liked = True

            watched_list.append([self.user, film_slug, rating, liked])

        return  watched_list


    async def film_count(self):
        page = 1
        movie_list = []
        prev, curr = 0, 1
        concurrency = 100  # Adjust as per your system's capability
        semaphore = asyncio.Semaphore(concurrency)

        async with aiohttp.ClientSession() as session:
            while prev != curr:
                page_url = f"{self.url}page/{page}/"
                print(page_url)
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


