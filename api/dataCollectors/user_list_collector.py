import asyncio

from api.dataCollectors.utils.paginate_parser import PaginateParser
from api.dataCollectors.utils.sort_categories import TimePeriodSort, UserSorting


class UserListCollector(PaginateParser):
    def __init__(self, user: str = None) -> None:
        super().__init__()
        self.entries_per_page = 30
        if user is None:
            self.url = 'https://letterboxd.com/members/popular/'
            self.user = None
        else:
            self.url = f"https://letterboxd.com/{user}/following/"
            self.user = user

    async def fetch_users_list(self, timespan: TimePeriodSort = None, order: UserSorting = None):
        if self.user is None:
            if timespan is not None:
                self.url = TimePeriodSort.sort(self.url, timespan)
        else:
            if order is not None:
                self.url = UserSorting.sort(self.url, order)
        await self.fetch_list()

    async def fetch_page_data(self, session, page_url):
        dom = await self.get_parsed_page(session, page_url)

        # TODO check for login or something
        logged_in = True

        user_rows = dom.find_all("td", {"class": "table-person"})

        user_list = []

        for user_row in user_rows:
            user_summary = user_row.find("div", {"class": "person-summary"})

            user_name_tag = user_summary.find("a", {"class": "name"})
            user_name = user_name_tag.text.strip() if user_name_tag else "Unknown"

            user_ref = user_summary.find("a", {"class": "avatar"})
            user_url = user_ref['href'] if user_ref else "Unknown"
            user_url.strip('/')

            user_list.append([user_name, user_url.strip('/')])
        return user_list


async def main():
    collector = UserListCollector('dtf')

    await collector.fetch_users_list(timespan=TimePeriodSort.WEEK)

    users_list = collector.items
    print(users_list)


if __name__ == "__main__":
    asyncio.run(main())
