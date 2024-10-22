import asyncio
import enum

import aiohttp
from api.dataCollectors.page_parser import PageParser


# TODO move to parser
class ListTimeFilter(enum.Enum):
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'
    ALL = 'all-time'


class UserListCollector(PageParser):
    def __init__(self, timescope: ListTimeFilter = ListTimeFilter.WEEK) -> None:

        self.url = f"https://letterboxd.com/members/popular/with/friends/this/{timescope.value}/"
        self.userCount = None
        self.users = []

    async def fetch_user_list(self):
        cookies = await PageParser.get_cookies()
        async with aiohttp.ClientSession(cookies=cookies) as session:
            self.users = await self.fetch_data(self.get_users, self.url, session)
            self.userCount = len(self.users)

        if self.userCount == 0:
            raise Exception("No list exists")

    async def get_users(self, session, page_url):
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

    collector = UserListCollector(ListTimeFilter.WEEK)
    await collector.fetch_user_list()
    users_list = collector.users
    print(users_list)


if __name__ == "__main__":
    asyncio.run(main())
