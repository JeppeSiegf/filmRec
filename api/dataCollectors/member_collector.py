import asyncio
import aiohttp
from api.dataCollectors.page_parser import PageParser


# Member is term used for a user who have logged a movie on the site -
# Used here a way to gather both user and rating data in a convenient location
# Also help to ensure that only data tied to existing film gets added to the db

class MemberListCollector(PageParser):
    def __init__(self, film_ref: str) -> None:
        # look into better validation
        if not film_ref.isascii():
            raise Exception("Invalid reference")

        self.url = f"https://letterboxd.com/film/{film_ref}/members/by/popular/"

        self.film_ref = film_ref



        self.filmCount = None
        self.members = []

        self.users = []
        self.ratings = []

    async def fetch_film_list(self):
        async with aiohttp.ClientSession() as session:
            self.members = await self.fetch_data(self.url, session, self.fetch_page_data)
            self.filmCount = len(self.members)
            self.__split_member_list(self.members)

    async def fetch_page_data(self,session, page_url):

        dom = await PageParser.get_parsed_page(session, page_url)
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
                # Extract the last segment from the class name 'rated-X'
                rating_classes = rating_span.get('class', [])
                for cls in rating_classes:
                    if cls.startswith('rated-'):
                        try:
                            rating = int(cls.split('-')[-1])  # Extract the last segment which is the rating
                            break
                        except ValueError:
                            rating = 0  # Default to zero if conversion fails
            else:
                rating = 0  # Default to zero if no rating found
        else:
            rating = 0  # Default to zero if no rating <td> found

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
    await collector.fetch_film_list()
    print(collector.url)


if __name__ == "__main__":
    asyncio.run(main())
