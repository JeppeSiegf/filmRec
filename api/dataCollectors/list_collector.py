import asyncio
import abc
from enum import Enum

import aiohttp

from api.dataCollectors.page_parser import PageParser



class ListCollector(PageParser):
    def __init__(self):
        self.url = ''
        self.items = []
        self.itemCount = 0

    async def fetch_list(self):
        """General method to fetch data, URL will be determined by the subclass."""
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch data using the common method
                self.items = await self.fetch_data(self.url, session)
                self.itemCount = len(self.items)



        except Exception as e:
            print(f"Error fetching list from {self.url}: {e}")
            raise  # Re-raise the exception to propagate it

    async def fetch_data(self, base_url, session):

        page = 1
        data_list = []
        semaphore = asyncio.Semaphore(100)

        while True:
            page_url = f"{base_url}page/{page}/"
            print(f"Fetching: {page_url}")

            async with semaphore:
                try:
                    data = await self.fetch_page_data(session, page_url)
                    if not data:
                        break  # Stop if no more data is returned
                    data_list.extend(data)
                    print(f"Fetched page {page}, total items: {len(data_list)}")
                except Exception as e:
                    print(f"Error fetching {page_url}: {e}")
                    break

            page += 1

        return data_list

    @abc.abstractmethod
    async def fetch_page_data(self, session, page_url):

        pass

