import asyncio
from typing import List, Union, Tuple
from datetime import datetime

from dataCollectors.utils.paginate_collector import PaginateCollector
from dataCollectors.utils.sort_categories import (
    SingleRatingFilter, RatingRangeFilter, UserSorting
)


class MemberListCollector(PaginateCollector):
    def __init__(self, film_ref: str, stop_page = 9999, stop_user = None):
        super().__init__()
        self.film_ref = film_ref
        self.stop_user = stop_user
        self.url = f"https://letterboxd.com/film/{film_ref}/members/"
        self.entries_per_page = 25
        self.max_page = stop_page
        self.users: List[str] = []
        self.ratings: List[dict] = []
        self.items: List[dict] = []

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

        await self.fetch_list()  # populate self.items via fetch_page_data
        # keep convenience copies
        self.__split_member_list(self.items)

    async def fetch_page_data(self, session, page_url):

        dom = await self.get_parsed_page(session, page_url)
        user_rows = dom.find_all("td", {"class": "table-person"})

        member_list = []

        for user_row in user_rows:
            user_summary = user_row.find("div", {"class": "person-summary"})
            if not user_summary:
                continue

            # user name (kept for possible use)
            user_name_tag = user_summary.find("a", {"class": "name"})
            user_name = user_name_tag.text.strip() if user_name_tag else None

            # user href / ref (avatar link)
            user_ref = user_summary.find("a", {"class": "avatar"})
            user_url = user_ref['href'].strip('/') if user_ref and user_ref.get('href') else None

            # Extract rating and liked using your existing methods
            rating = await self.__extract_rating(user_row)
            # treat 0 as "no rating"
            if rating == None:
                rating = 0

            liked = await self.__extract_like(user_row)

            # rating_date: current UTC timestamp as ISO string
            rating_date = datetime.utcnow().isoformat()

            # Build JSON-ready dict matching Rating model (no extra None fields required)
            rating_obj = {
                "user_id": user_url,         # must be non-null when possible
                "film_id": self.film_ref,
                "rating": rating,            # int or None
                "liked": bool(liked),
                "rating_date": rating_date   # ISO string for transport
            }

            # Append only if user_url exists; else skip (or keep depending on your policy)
            if rating_obj["user_id"]:
                member_list.append(rating_obj)

            if self.stop_user == user_url:
                return member_list

        return member_list

    async def __extract_rating(self, user_row) -> int:

        rating = 0
        rating_td = user_row.find_next_sibling("td")
        if not rating_td:
            return 0

        for span in rating_td.find_all("span"):
            classes = span.get("class", []) or []
            for cls in classes:
                if isinstance(cls, str) and cls.startswith("rated-"):
                    try:
                        rating = int(cls.split("-")[-1])
                        return rating
                    except ValueError:
                        continue

        return rating

    async def __extract_like(self, user_row) -> bool:

        td = user_row.find_next_sibling("td")
        checks = 0
        while td and checks < 6:
            for span in td.find_all("span"):
                classes = span.get("class", []) or []
                for cls in classes:
                    if isinstance(cls, str) and ("icon-liked" in cls or cls == "liked"):
                        return True
            td = td.find_next_sibling("td")
            checks += 1

        return False

    def __split_member_list(self, member_list: List[dict]):
        # users: list of user_ids for convenience
        self.users = [m["user_id"] for m in member_list]
        # ratings: keep the rating dicts intact (useful for bulk DB insert)
        self.ratings = member_list.copy()


# usage example
async def main():
    collector = MemberListCollector('maya-deren-take-zero', 3, 'becomingsam')
    await collector.fetch_member_list()
    # collector.items is a list of rating dicts returned by fetch_page_data for all pages
    print("users:", collector.users)
    print("ratings ", collector.ratings)

if __name__ == "__main__":
    asyncio.run(main())
