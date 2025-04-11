import asyncio
from typing import List

from api.dataCollectors.utils.paginate_parser import PaginateParser
from api.dataCollectors.utils.sort_categories import ReleaseDateFilter, GenreFilter, FilmSorting


class FilmListCollector(PaginateParser):
    def __init__(self, user: str, title: str, stop_title: str = None) -> None:
        super().__init__()

        self.url = f"https://letterboxd.com/{user}/list/{title}/detail/"
        self.entries_per_page = 100
        self.stop_ref = stop_title

    async def fetch_film_list(self, decade: ReleaseDateFilter = None,
                              genres: List[GenreFilter] = None,
                              order: FilmSorting = None, ):
        if decade is not None:
            ReleaseDateFilter.filter(self.url, decade)
        if genres is not None:
            GenreFilter.filter(self.url, genres)
        if order is not None:
            self.url = FilmSorting.sort(self.url, order)
        await self.fetch_list()

    async def fetch_page_data(self, session, page_url, ):

        film_list = []

        page = await self.get_parsed_page(session, page_url)
        img = page.find("ul", {"class": ["js-list-entries", "poster-list", "-p125", "-grid", "film-list"]})

        if not img:
            return []

        titles = img.find_all("img", {"class": ["image"]})
        years = img.find_all('small', {"class": ["metadata"]})

        for title_item, year_item in zip(titles, years):
            movie_url = title_item.parent.get('data-film-slug', '')
            movie_title = title_item.get('alt', '')
            movie_year = year_item.find('a').text.strip() if year_item.find('a') else "Unknown"

            # Stop when the film slug matches the stop value
            if movie_url == self.stop_ref:
                return film_list  # Stop and return collected films

            film_list.append((movie_title, movie_url, movie_year))

        return film_list


# Usage example
async def main():
    collector = FilmListCollector('fcbarcelona', 'movies-everyone-should-watch-at-least-once', 'the-shining')
    await collector.fetch_film_list(order=FilmSorting.LAST_ADDITION)
    movielist = collector.items
    print(movielist)


# Run the main function to start the async process
if __name__ == "__main__":
    asyncio.run(main())
