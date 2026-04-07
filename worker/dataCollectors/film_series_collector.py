import asyncio
import re

from dataCollectors.utils.request_interceptor import ReqeustInterceptor

class FilmSeriesCollector(ReqeustInterceptor):

    def __init__(self, collection):
        super().__init__()
        self.base_url = f"https://letterboxd.com/films/in/{collection}/"

    async def format_data(self, raw_data):

        film_data = []
        poster_pattern = re.compile(r'/ajax/poster/film/([^/]+)/std/')

        for item in raw_data:
            url = item["url"]

            poster_match = poster_pattern.search(url)
            if poster_match:
                film_ref = poster_match.group(1)
                film_data.append(film_ref)

        return film_data


async def main():
    collector = FilmSeriesCollector('harry-potter-collection')
    results = await collector.fetch_xhr_data()

    print(results)


# Run the main function to start the async process
if __name__ == "__main__":
    asyncio.run(main())
