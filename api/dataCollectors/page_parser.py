import asyncio
from json import loads
import browser_cookie3
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
    async def get_parsed_page(session, url: str, parser: str = "lxml"):
        page_content = await PageParser.__fetch_page(session, url)
        try:
            dom = BeautifulSoup(page_content, parser)
        except Exception as e:
            raise RuntimeError(f"Error parsing response from {url}: {e}")
        return dom

    @staticmethod
    async def fetch_data(base_url, session, fetch_page_data):
        """Fetches data across paginated URLs using a specified page data extraction method."""
        page = 1
        data_list = []
        prev_length = 0
        curr_length = 1
        concurrency = 100  # Adjust based on system's capacity
        semaphore = asyncio.Semaphore(concurrency)

        while True:
            page_url = f"{base_url}page/{page}/"
            async with semaphore:
                try:
                    data = await fetch_page_data(session, page_url)  # Use the provided method
                    if not data:
                        break  # Stop if no more data is returned (end of pagination)
                    data_list.extend(data)
                    print(f"Fetched page {page} with {len(data)} items.")
                except Exception as e:
                    print(f"Error fetching data from {page_url}: {e}")
                    break

            prev_length = curr_length
            curr_length = len(data_list)
            if curr_length == prev_length:
                break  # No new data, stop pagination
            page += 1

        return data_list



    @staticmethod
    async def get_cookies():
        cj = browser_cookie3.firefox(domain_name='letterboxd.com')
        cookie_dict = {cookie.name: cookie.value for cookie in cj}
        return cookie_dict