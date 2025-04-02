import asyncio
from typing import Union, Tuple

import aiohttp
from api.dataCollectors.list_collector import ListCollector
from api.dataCollectors.sort_categories import RatingRangeFilter, SingleRatingFilter, UserSorting


# Member is term used for a user who have logged a movie on the site -
# Used here a way to gather both user and rating data in a convenient location
# Also help to ensure that only data tied to existing film gets added to the db

class MemberListCollector(ListCollector):
    def __init__(self, film_ref: str) -> None:
        super().__init__()
        self.url = f"https://letterboxd.com/film/{film_ref}/members/"
        self.entries_per_page = 25
        self.users = []
        self.ratings = []

    async def fetch_member_list(self, ratings: Union[SingleRatingFilter,
                                Tuple[RatingRangeFilter, RatingRangeFilter]] = None,
                                order: UserSorting = None):

        if ratings is not None:
            if isinstance(ratings, tuple):
                self.url = RatingRangeFilter.filter(self.url, ratings)
            elif isinstance(ratings, SingleRatingFilter):
                self.url = SingleRatingFilter.filter(self.url, ratings)
        if order is not None:
            self.url = UserSorting.sort(self.url, order)
        await self.fetch_list()

    async def fetch_page_data(self, session, page_url):

        dom = await self.get_parsed_page(session, page_url)
        user_rows = dom.find_all("td", {"class": "table-person"})

        member_list = []

        for user_row in user_rows:
            user_summary = user_row.find("div", {"class": "person-summary"})

            user_name_tag = user_summary.find("a", {"class": "name"})
            user_name = user_name_tag.text.strip() if user_name_tag else "Unknown"

            user_ref = user_summary.find("a", {"class": "avatar"})
            user_url = user_ref['href'] if user_ref else "Unknown"
            user_url.strip('/')

            # Extract the rating information
            rating = await self.__extract_rating(user_row)
            like = await self.__extract_like(user_row)

            member_list.append([user_name, user_url.strip('/'), rating, like])
        return member_list

    async def __extract_rating(self, user_row) -> int:

        rating = 0
        rating_td = user_row.find_next_sibling("td")  # Assuming the rating is in the second <td>
        if rating_td:
            rating_span = rating_td.find("span", {"class": lambda x: x and x.startswith('rating rated-')})
            if rating_span:
                rating_classes = rating_span.get('class', [])
                for cls in rating_classes:
                    if cls.startswith('rated-'):
                        try:
                            rating = int(cls.split('-')[-1])  # Extract the last segment which is the rating
                            break
                        except ValueError:
                            rating = 0

        return rating

    async def __extract_like(self, user_row) -> bool:
        like = False
        like_icon_td = user_row.find_next_sibling("td")

        while like_icon_td:
            like_span = like_icon_td.find("span", {"class": "has-icon icon-16 icon-liked"})
            if like_span:
                like = True
                break
            like_icon_td = like_icon_td.find_next_sibling("td")

        return like

    def __split_member_list(self, member_list):
        self.users = [member[0:2] for member in member_list]
        self.ratings = [member[1:4] for member in member_list]


async def main():
    collector = MemberListCollector('maya-deren-take-zero')
    await collector.fetch_member_list(ratings=SingleRatingFilter.NO_STARS, order=UserSorting.ALPHABETIC)
    print(collector.items)
    print(len(collector.items))


if __name__ == "__main__":
    asyncio.run(main())
