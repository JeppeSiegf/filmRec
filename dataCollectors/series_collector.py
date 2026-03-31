import asyncio

from dataCollectors.film_series_collector import FilmSeriesCollector
from dataCollectors.utils.paginate_collector import PaginateCollector


class SeriesCollector(PaginateCollector):
    def __init__(self) -> None:
        super().__init__()
        self.url = f"https://letterboxd.com/collections/"
        self.entries_per_page = 72

    async def fetch_series_list(self):

        await self.fetch_list()

    async def fetch_page_data(self, session, page_url):
        collection_metadata = []
        film_tasks = []
        slugs_to_index_map = {}

        page = await self.get_parsed_page(session, page_url)
        collections = page.find_all("div", {"class": "list -stacked -trilogy"})

        if not collections:
            return []

        # First pass: extract metadata and create tasks
        for idx, collection in enumerate(collections):
            # Extract collection slug from URL
            link = collection.find("a", {"class": "list-link"})
            if link:
                href = link.get("href", "")
                slug_parts = href.split('/')
                collection_slug = slug_parts[3] if len(slug_parts) > 3 else href
            else:
                collection_slug = "unknown-collection"

            # Extract collection title
            title_tag = collection.find("h3", {"class": "title-3 prettify"})
            collection_title = title_tag.find("a").text.strip() if title_tag and title_tag.find(
                "a") else "Unknown Collection"

            # Save metadata with placeholders for film data
            collection_metadata.append((
                collection_slug,
                collection_title,
                0,
                []
            ))

            # Create task for this collection
            film_collector = FilmSeriesCollector(collection_slug)
            task = film_collector.fetch_xhr_data()
            film_tasks.append(task)

            # Map the task index to the collection index
            slugs_to_index_map[len(film_tasks) - 1] = idx

        # Run all tasks in parallel
        if film_tasks:
            film_results = await asyncio.gather(*film_tasks)

            # Update metadata with results
            for task_idx, film_slugs in enumerate(film_results):
                collection_idx = slugs_to_index_map[task_idx]

                # Update the placeholder tuple with actual data
                slug, title, _, _ = collection_metadata[collection_idx]
                collection_metadata[collection_idx] = (
                    slug,
                    title,
                    len(film_slugs),  # Film count
                    film_slugs  # List of film slugs
                )

        return collection_metadata


async def main():
    collector = SeriesCollector()
    await collector.fetch_series_list()
    movielist = collector.items
    print(movielist)


# Run the main function to start the async process
if __name__ == "__main__":
    asyncio.run(main())
