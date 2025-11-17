import asyncio
import re
from typing import List
from datetime import datetime

from dataCollectors.utils.paginate_collector import PaginateCollector
from dataCollectors.utils.sort_categories import ReleaseDateFilter, GenreFilter, RatingSorting


class RatingsCollector(PaginateCollector):
    def __init__(self, user: str, stop_film_ref: str = None,) -> None:
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
        poster_grid = page.find("div", {"class": "poster-grid"})
        if not poster_grid:
            return []

        poster_items = poster_grid.find_all("li", {"class": "griditem"})
        if not poster_items:
            return []

        watched_list = []

        for item in poster_items:
            film_div = item.find("div", {"class": "react-component"})
            if not film_div:
                continue

            film_slug = film_div.get("data-item-slug", "")

            rating = 0
            liked = False

            rating_info = item.find("p", {"class": "poster-viewingdata"})
            if rating_info:
                # Find first rating span with "rated-X"
                rating_span = rating_info.find("span", class_=lambda x: x and x.startswith("rated-"))
                if rating_span:
                    try:
                        rating = int([c for c in rating_span["class"] if c.startswith("rated-")][0].split("-")[1])
                    except Exception:
                        rating = 0

                # Check for liked
                liked = bool(rating_info.find("span", class_=lambda x: x and "liked-micro" in x))

            if film_slug == self.stop_film:
                return watched_list

            watched_list.append({
                "user_id": self.user,
                "film_id": film_slug,
                "rating": rating,
                "liked": liked,
                "rating_date": datetime.utcnow().isoformat()
            })

        return watched_list


# Example usage
async def main():
    collector = RatingsCollector('thejoshl')
    await collector.fetch_ratings_list()
    users_list = collector.items
    print(f"Found {len(users_list)} :")
    print(users_list)


if __name__ == "__main__":
    asyncio.run(main())

