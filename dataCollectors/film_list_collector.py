import asyncio
from typing import List

from dataCollectors.utils.paginate_collector import PaginateCollector
from dataCollectors.utils.sort_categories import ReleaseDateFilter, GenreFilter, FilmSorting


class FilmListCollector(PaginateCollector):
    def __init__(self, user: str, title: str, stop_title: str = None) -> None:
        super().__init__()

        self.url = f"https://letterboxd.com/{user}/list/{title}/detail/"
        self.entries_per_page = 100
        self.stop_ref = stop_title
        self.max_page = 9999

    async def fetch_film_list(self, decade: ReleaseDateFilter = None,
                              genres: List[GenreFilter] = [],
                              order: FilmSorting = None, ):
        if decade is not None:
            ReleaseDateFilter.filter(self.url, decade)
        if len(genres) > 0:
            GenreFilter.filter(self.url, genres)
        if order is not None:
            self.url = FilmSorting.sort(self.url, order)

        await self.fetch_list()

        return self.items

    async def fetch_page_data(self, session, page_url):
        film_list = []

        page = await self.get_parsed_page(session, page_url)
        items = page.find_all("div", {"class": "listitem js-listitem"})

        for item in items:
            article = item.find("article", {"class": "list-detailed-entry"})
            if not article:
                continue

            # Film data is stored in the "react-component" with data attributes
            poster_div = article.find("div", {"class": "react-component"})
            if not poster_div:
                continue

            film_obj = {}

            # Extract film slug (page_ref)
            film_slug = poster_div.get("data-item-slug")
            if film_slug:
                film_obj["page_ref"] = film_slug

            # Extract title from <img alt="..."> tag
            img = poster_div.find("img", {"class": "image"})
            if img:
                alt = img.get("alt")
                if alt:
                    film_obj["title"] = alt

            # Stop parsing if we reach the stop reference
            if film_slug == self.stop_ref:
                return film_list

            if film_obj:
                film_list.append(film_obj)

        return film_list


# Usage example
async def main():
    collector = FilmListCollector('jack', 'official-top-250-films-with-the-most-fans', )
    await collector.fetch_film_list(order=FilmSorting.LAST_ADDITION)
    movielist = collector.items
    print(movielist)


# Run the main function to start the async process
if __name__ == "__main__":
    asyncio.run(main())
