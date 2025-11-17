import pytest

from dataCollectors.member_collector import MemberPaginateParser  # Adjust the import based on your structure

TEST_CASES = [
    {
        "film_ref": "maya-deren-take-zero",  # Use a valid film reference here
        "expected_status": "success",
        "expected_user_count": 128,  # Adjust based on the actual expected count
        "expected_rating_count": 128,  # Ensure this matches the expected length
        "page_no": 6,
    },
    {
        "film_ref": "nonexistent-film-ref",  # Invalid reference to trigger failure
        "expected_status": "fail",
        "expected_user_count": 0,
        "expected_rating_count": 0,
        "page_no": 1,
    }
]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", TEST_CASES)
async def test_member_list_collector(test_case):
    pages_fetched = []

    # Instantiate the collector with the film_ref from the test_case
    collector = MemberPaginateParser(test_case["film_ref"])

    # Override the fetch_page_data method to track pages fetched
    original_fetch = collector.fetch_page_data

    async def tracked_fetch(session, page_url):
        data = await original_fetch(session, page_url)
        if data:
            page_num = int(page_url.split('/')[-2]) if 'page' in page_url else 1
            pages_fetched.append((page_num, len(data)))  # Track page number and number of items fetched
        return data

    # Replace the original fetch_page_data method with the tracked version
    collector.fetch_page_data = tracked_fetch

    # Fetch the member list
    await collector.fetch_series_list()

    # Validate the expected behavior based on test_case
    if test_case["expected_status"] == "success":
        # Calculate the expected number of pages (25 members per page)
        min_page = collector.filmCount // 25
        max_page = min_page + (1 if collector.filmCount % 25 != 0 else 0)

        # Ensure that at least one page was fetched
        assert len(pages_fetched) > 0, "Should fetch at least one page"

        # Ensure that the number of pages fetched is within the expected range based on 25 members per page
        assert min_page <= len(pages_fetched) <= max_page, \
            f"Pages fetched {len(pages_fetched)} is not in expected range ({min_page}, {max_page})"

        # Check the structure and validity of each member
        for user, user_url, rating, like in collector.members:
            # Validate user info
            assert isinstance(user, str) and user, f"Invalid user name {user}"
            assert isinstance(user_url, str) and user_url, f"Invalid user URL {user_url}"
            # Validate rating is an integer or None
            assert isinstance(rating, (int, type(None))), f"Invalid rating {rating} for user {user}"
            # Validate like status is a boolean
            assert isinstance(like, bool), f"Invalid like status for user {user}"
