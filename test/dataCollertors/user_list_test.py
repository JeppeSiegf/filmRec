import pytest
from api.dataCollectors.user_list_collector import UserListCollector

TEST_CASES = [
    {
        "url": "https://letterboxd.com/mscorsese/following/",
        "expected_status": "success",
        "user_list_len": 1,  # Adjust this based on expected number of users
        "page_no": 1
    },
    {
        "url": "https://letterboxd.com/not/real/",
        "expected_status": "fail"
    }
]

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", TEST_CASES)
async def test_user_list_collector(test_case):

    collector = UserListCollector()

    try:
        # Fetch the data
        await collector.fetch_user_list(test_case["url"])

        if test_case["expected_status"] == "success":
            assert collector.userCount > 0, "User list should not be empty"

            assert collector.userCount >= test_case["user_list_len"], \
                f"Expected at least {test_case['user_list_len']} users, but got {collector.userCount}"

            # Check the content of the users list
            for user in collector.users:
                user_name, user_url = user
                assert isinstance(user_name, str) and user_name, "User name should be a non-empty string"
                assert isinstance(user_url, str) and user_url


        elif test_case["expected_status"] == "fail":
            # If no users were found, an exception is raised, and we want to ensure the failure
            assert collector.userCount == 0, "Should not have fetched any users for a non-existent list"


    except Exception as e:
        if test_case["expected_status"] == "fail":
            # Ensure the exception raised is due to no users found
            assert "No users found for URL" in str(e)
        else:
            raise  # Re-raise the exception if it wasn't the expected failure
