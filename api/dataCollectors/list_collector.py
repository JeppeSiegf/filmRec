import asyncio
import abc
from enum import Enum

import aiohttp

from api.dataCollectors.page_parser import PageParser


class ListCollector(PageParser):
    def __init__(self):
        self.entries_per_page = 0
        self.url = ''
        self.items = []
        self.itemCount = 0

    async def fetch_list(self,):

        try:
            async with aiohttp.ClientSession() as session:

                self.items = await self.fetch_data(self.url, session)
                self.itemCount = len(self.items)

        except Exception as e:
            print(f"Error fetching list from {self.url}: {e}")
            raise  # Re-raise the exception to propagate it

    async def fetch_data(self, base_url, session):

        page = 1
        all_pages_data = []
        semaphore = asyncio.Semaphore(100)

        while True:
            page_url = f"{base_url}page/{page}/"
            print(f"Fetching: {page_url}")

            async with semaphore:
                try:
                    data = await self.fetch_page_data(session, page_url)
                    if not data:
                        break
                    if len(data) != self.entries_per_page:
                        all_pages_data.append(data)

                        break  #
                    all_pages_data.append(data)


                    print(f"Fetched page {page}, total items: {len(all_pages_data)}")
                except Exception as e:
                    print(f"Error fetching {page_url}: {e}")
                    break

            page += 1

        #all_pages_data.reverse()
        data_list = [item for page in all_pages_data for item in page]

        return data_list

    @abc.abstractmethod
    async def fetch_page_data(self, session, page_url):
        pass
