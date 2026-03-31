from bs4 import BeautifulSoup


class PageParser:

    @staticmethod
    async def __fetch_page(session, url):
        try:
            response = await session.get(url)
            return response.text
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