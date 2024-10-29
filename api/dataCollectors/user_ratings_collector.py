import asyncio
import aiohttp
from api.dataCollectors.page_parser import PageParser


class UserRatingsCollector(PageParser):
    def __init__(self, user: str) -> None:

        self.url = f"https://letterboxd.com/{user}/films/"

        self.user = user
        self.filmCount = None
        self.ratings = []

    async def fetch_ratings_list(self):
        async with aiohttp.ClientSession() as session:
            self.ratings = await self.fetch_data(self.extract_ratings, self.url, session)
            self.filmCount = len(self.ratings)

        if self.filmCount == 0:
            raise Exception("No list exists")

    async def extract_ratings(self, session, page_url):

        page = await self.get_parsed_page(session, page_url)

        poster_containers = page.find_all("li", {"class": ["poster-container"], })
        if not poster_containers:
            return []

        watched_list = []

        for poster_container in poster_containers:
            poster = poster_container.div
            film_data = poster_container.find("img", {"class": "image"})
            film_slug = film_data.parent.get('data-film-slug', '')
            rating_info = poster_container.find("p", {"class": "poster-viewingdata"})
            rating = None
            liked = False

            if rating_info.span:
                for span in rating_info.find_all("span"):
                    if 'rating' in span['class']:
                        rating = int(rating_info.span['class'][-1].split('-')[-1])
                    elif 'like' in span['class']:
                        liked = True

            watched_list.append([self.user, film_slug, rating, liked])

        return watched_list


async def main():
    collector = UserRatingsCollector('filipe_furtado')
    await collector.fetch_ratings_list()
    movielist = collector.ratings
    print(movielist)


if __name__ == "__main__":
    asyncio.run(main())
