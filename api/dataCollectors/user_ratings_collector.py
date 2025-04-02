import asyncio
from typing import List

from api.dataCollectors.list_collector import ListCollector
from api.dataCollectors.sort_categories import ReleaseDateFilter, GenreFilter, RatingSorting
import time


class UserRatingsCollector(ListCollector):
    def __init__(self, user: str, stop_film_ref: str = None) -> None:
        super().__init__()
        self.stop_film = stop_film_ref
        self.url = f"https://letterboxd.com/{user}/films/"
        self.entries_per_page = 72
        self.user = user

    async def fetch_ratings_list(self, decade: ReleaseDateFilter = None,
                                 genres: List[GenreFilter] = [],
                                 order: RatingSorting = None,
                                 stop_ref=None):
        if decade is not None:
            self.url = ReleaseDateFilter.filter(self.url, decade)
        if len(genres) > 0:
            self.url = GenreFilter.filter(self.url, genres)
        if order is not None:
            self.url = RatingSorting.sort(self.url, order)
        await self.fetch_list()

    async def fetch_page_data(self, session, page_url):

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
            rating = 0
            liked = False

            if rating_info.span:
                for span in rating_info.find_all("span"):
                    if 'rating' in span['class']:
                        rating = int(rating_info.span['class'][-1].split('-')[-1])
                    elif 'like' in span['class']:
                        liked = True

            if film_slug == self.stop_film:
                return watched_list

            watched_list.append([self.user, film_slug, rating, liked])


        return watched_list


async def main():
    start_time = time.perf_counter()
    collector = UserRatingsCollector('samiser', 'the-purge')
    await collector.fetch_ratings_list(None, [], RatingSorting.LAST_ADDITION)
    elapsed_time = time.perf_counter() - start_time  # End timer
    print(f"Total execution time: {elapsed_time:.2f}s")
    movielist = collector.items
    print(movielist)


if __name__ == "__main__":
    asyncio.run(main())
