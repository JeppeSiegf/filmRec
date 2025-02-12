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
    def __init__(self,) -> None:

        self.userCount = None
        self.users = []

    async def fetch_user_list(self, url):

        try:
            #cookies = await PageParser.get_cookies()
            async with aiohttp.ClientSession(cookies=cookies) as session:
                self.users = await PageParser.fetch_data(url, session, self.fetch_page_data)

            self.userCount = len(self.users)

            if self.userCount == 0:
                raise Exception(f"No users found for URL: {url}")

        except Exception as e:
            print(f"Error fetching user list from {url}: {e}")
            raise  # Re-raise the exception to propagate it

    @staticmethod
    async def fetch_page_data(session, page_url):
        dom = await PageParser.get_parsed_page(session, page_url)


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

    collector = UserListCollector()
    await collector.fetch_user_list('https://letterboxd.com/mscorsese/following/')

    users_list = collector.users
    print(users_list)


if __name__ == "__main__":
    asyncio.run(main())
