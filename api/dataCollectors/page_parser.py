import asyncio

import aiohttp
from bs4 import BeautifulSoup

class PageParser:
    @staticmethod
    async def __fetch_page(session, url):
        headers = {
            "referer": "https://letterboxd.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        try:
            async with session.get(url, headers=headers) as response:
                return await response.text()
        except Exception as e:
            raise RuntimeError(f"Error connecting to {url}: {e}")

    @staticmethod
    async def get_parsed_page(session, url: str, parser: str = "lxml") -> BeautifulSoup:
        page_content = await PageParser.__fetch_page(session, url)  # Fixed the method call
        try:
            dom = BeautifulSoup(page_content, parser)
        except Exception as e:
            raise RuntimeError(f"Error parsing response from {url}: {e}")
        return dom

    @staticmethod
    async def fetch_data(fetch_method, base_url, session):
        page = 1
        data_list = []
        prev_length = 0
        curr_length = 1
        concurrency = 100  # Adjust based on system's capacity
        semaphore = asyncio.Semaphore(concurrency)

        while prev_length != curr_length:
            page_url = f"{base_url}page/{page}/"
            print(f"Fetching: {page_url}")

            async with semaphore:
                try:
                    data = await fetch_method(session, page_url)
                    if not data:
                        break  # Stop if no more data

                    data_list.extend(data)
                except Exception as e:
                    print(f"Error fetching data from {page_url}: {e}")
                    break

            prev_length = curr_length
            curr_length = len(data_list)
            page += 1

        return data_list
