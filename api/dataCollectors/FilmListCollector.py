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
    def __init__(self, user: str, title: str) -> None:
        if not user.isalnum():
            raise Exception("Invalid user")

        self.url = f"https://letterboxd.com/{user}/list/{title}/detail/"
        print(self.url)
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
        for title_item, year_item in zip(titles, years):
            movie_url = title_item.parent.get('data-film-slug', '')
            # movie_id = title_item.parent.get('data-film-id', '')
            movie_title = title_item.get('alt', '')
            movie_year = year_item.find('a').text.strip() if year_item.find('a') else "Unknown"

            movie_list.append((movie_title, movie_url, movie_year))
        print(movie_list)
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

# Run the asynchronous film count method
async def main():
    collector = FilmListCollector('brthrash', 'directors')
    await collector.film_count()
    movielist = collector.movies
    print(movielist)

if __name__ == "__main__":
    asyncio.run(main())
