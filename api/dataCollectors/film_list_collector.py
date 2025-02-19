import asyncio
from typing import List

import aiohttp
from api.dataCollectors.list_collector import ListCollector
from api.dataCollectors.sort_categories import ReleaseDateFilter,GenreFilter,FilmSorting


class FilmListCollector(ListCollector):
    def __init__(self, user: str, title: str) -> None:
        super().__init__()
        self.url = f"https://letterboxd.com/{user}/list/{title}/detail/"

    async def fetch_film_list(self, decade: ReleaseDateFilter = None,
                                genres: List[GenreFilter] = [],
                                 order: FilmSorting = None):
        if decade is not None:
            ReleaseDateFilter.filter(self.url, decade)
        if len(genres) > 0:
            GenreFilter.filter(self.url, genres)
        if order is not None:
            self.url = FilmSorting.sort(self.url, order)
        await self.fetch_list()

    async def fetch_page_data(self,session, page_url,):

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

# Usage example
async def main():
    collector = FilmListCollector('brthrash', 'directors')
    await collector.fetch_film_list(order=FilmSorting.RELEASE_DATE)
    movielist = collector.url
    print(movielist)

# Run the main function to start the async process
if __name__ == "__main__":
    asyncio.run(main())