import asyncio


from dataCollectors.utils.paginate_collector import PaginateCollector
from dataCollectors.utils.sort_categories import TimePeriodSort, UserSorting


class UserListCollector(PaginateCollector):
    def __init__(self, user: str = None) -> None:
        super().__init__()
        self.entries_per_page = 25
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

        if not dom:
            return []

        # TODO check for login or something
        logged_in = True

        user_rows = dom.find_all("td", {"class": "table-person"})

        user_list = []

        for user_row in user_rows:
            user_summary = user_row.find("div", {"class": "person-summary"})

            if not user_summary:
                continue

            user_name_tag = user_summary.find("a", {"class": "name"})
            user_name = user_name_tag.text.strip() if user_name_tag else "Unknown"

            user_ref = user_summary.find("a", {"class": "avatar"})
            if not user_ref:
                # Fallback to name link if avatar link doesn't exist
                user_ref = user_name_tag

            if user_ref and user_ref.get('href'):
                user_url = user_ref['href'].strip('/')
            else:
                user_url = "Unknown"


            user_data = {
                'profile_ref': user_url,  # Primary key - the user's profile reference
                'username': user_name,  # Username

            }

            user_list.append(user_data)

        return user_list


if __name__ == '__main__':

        pass
