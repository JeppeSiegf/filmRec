import pytest
import asyncio

from api.dataCollectors.film_list_collector import FilmListCollector

TEST_CASES = [
    {
        "url": "https://letterboxd.com/dave/list/official-top-250-narrative-feature-films/",
        "user": "dave",
        "list": "official-top-250-narrative-feature-films",
        "expected_status": "success",
        "list_len": 250,  # Should have at least 200 movies
        "page_no": 3
    },
    {
        "url": "https://letterboxd.com/crew/list/most-fans-on-letterboxd-2022/",
        "user": "crew",
        "list": "most-fans-on-letterboxd-2022",
        "expected_status": "success",
        "list_len": 100,
        "page_no": 1  # Should have at least 10 movies
    },

    {
        "url": "https://letterboxd.com/crew/list/edgar-wrights-1000-favorite-movies/",
        "user": "crew",
        "list": "edgar-wrights-1000-favorite-movies",
        "expected_status": "success",
        "list_len": 1000,  # Should have at least 200 movies
        "page_no": 10
    }, {
        "user": "nonexistentuser123456",
        "list": "fakelist",
        "expected_status": "fail"
    }

]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", TEST_CASES)
async def test_film_list_collector(test_case):
    """Integration test for FilmListCollector with pagination tracking"""
    try:
        # Track pagination data
        pages_fetched = []

        collector = FilmListCollector(test_case["user"], test_case["list"])

        # Override fetch_page_data to track pages
        original_fetch = collector.fetch_page_data

        async def tracked_fetch(session, page_url):
            data = await original_fetch(session, page_url)
            if data:
                page_num = int(page_url.split('/')[-2]) if 'page' in page_url else 1
                pages_fetched.append((page_num, len(data)))
            return data

        collector.fetch_page_data = tracked_fetch

        # Fetch the data
        await collector.fetch_film_list()

        if test_case["expected_status"] == "success":

            min_page = collector.filmCount // 100
            max_page = min_page + (1 if collector.filmCount % 100 != 0 else 0)
            assert len(pages_fetched) > 0, "Should fetch at least one page"
            assert min_page <= len(pages_fetched) <= max_page

            # Verify total count
            assert collector.filmCount >= test_case.get("min_count", 1)
            assert collector.filmCount == test_case.get("list_len")
            print(f"Total movies: {collector.filmCount}")

            # Verify content of movies
            assert len(collector.movies) == collector.filmCount

            # Check first and last movie format
            for movie in [collector.movies[0], collector.movies[-1]]:
                title, url, year = movie
                assert isinstance(title, str) and title
                assert isinstance(url, str) and url
                assert isinstance(year, str) and year

    except ValueError as e:
        if "Invalid user" in str(e):
            assert test_case["expected_status"] == "fail"
            print(f"Expected failure for invalid user: {e}")
        else:
            raise

    except Exception as e:
        if test_case["expected_status"] == "fail":
            print(f"Expected failure: {e}")
        else:
            raise


if __name__ == '__main__':
    pytest.main(['-v'])
