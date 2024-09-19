import asyncio
import aiohttp
from bs4 import BeautifulSoup
import page_parser as parser


class UserRatingsCollector:
    def __init__(self, user) -> None:
        if not user.isalnum():
            raise Exception("Invalid author")

        self.url = f"https://letterboxd.com/{user}/films/"

        self.user = user
        self.filmCount = None
        self.movies = []


    async def fetch_ratings(self, session, page_url):

        page = await parser.get_parsed_page(session, page_url)

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

    async def fetch_ratings_list(self):

        page = 1
        movie_list = []
        concurrency = 100  # Adjust as per your system's capability
        semaphore = asyncio.Semaphore(concurrency)

        async with aiohttp.ClientSession() as session:
            while True:
                page_url = f"{self.url}page/{page}/"
                async with semaphore:
                    movies = await self.fetch_ratings(session, page_url)

                # If no new movies are found, break the loop
                if not movies:
                    break

                movie_list.extend(movies)
                page += 1

        self.filmCount = len(movie_list)
        self.movies = movie_list

        if self.filmCount == 0:
            raise Exception("No list exists")


async def main():
    collector = UserRatingsCollector('brendonyu668')
    await collector.fetch_ratings_list()
    movielist = collector.movies
    print(movielist)


if __name__ == "__main__":
    asyncio.run(main())

