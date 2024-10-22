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
        page_content = await PageParser.__fetch_page(session, url)  # Fixed the method call
        try:
            dom = BeautifulSoup(page_content, parser)
        except Exception as e:
            raise RuntimeError(f"Error parsing response from {url}: {e}")
        return dom

    @staticmethod
    async def fetch_page_script(dom):
        if dom is None:
            raise ValueError("DOM is not initialized. Call fetch_page_dom first.")
        script = dom.find("script", type="application/ld+json")
        script = loads(script.text.split('*/')[1].split('/*')[0]) if script else None
        return script

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
                    print(data_list)
                except Exception as e:
                    print(f"Error fetching data from {page_url}: {e}")
                    break

            prev_length = curr_length
            curr_length = len(data_list)
            page += 1

        return data_list

    @staticmethod
    async def get_cookies():

        cj = browser_cookie3.firefox(domain_name='letterboxd.com')
        cookie_dict = {cookie.name: cookie.value for cookie in cj}
        print(cookie_dict)
        return cookie_dict

