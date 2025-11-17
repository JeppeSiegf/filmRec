import asyncio

from .. import create_app

from ..repositories.user_repository import UserRepository


class UserService:

    def __init__(self):
        self.repo = UserRepository()

    def get_all_users(self):
        return self.repo.get_all_users()

    def get_user_by_profile_ref(self, profile_ref):
        return self.repo.get_user_by_profile_ref(profile_ref)

    def get_user_by_profile_refs(self, user_refs):
        return self.repo.get_user_by_profile_refs(user_refs)

    def create_multiple_users(self, user_data_list):
        """Create multiple users from JSON format data."""

        if not isinstance(user_data_list, list):
            raise TypeError("Expected a list of dictionaries.")

        # Filter out any None or invalid entries
        valid_user_data = [user for user in user_data_list if user is not None and isinstance(user, dict)]

        if not valid_user_data:
            print("No valid users to insert.")
            return []

        # Validate that each user has required fields (at minimum profile_ref)
        processed_users = []
        for user_data in valid_user_data:
            if 'profile_ref' in user_data:
                processed_users.append(user_data)
            else:
                print(f"Skipping user data missing required fields: {user_data}")

        if not processed_users:
            print("No users with required fields found.")
            return []

        inserted_users = self.repo.insert(processed_users)

        return inserted_users


if __name__ == '__main__':

    app = create_app()
    with app.app_context():
        pass
        # # coll = UserListCollector('ootoo')
        # users = asyncio.run(coll.fetch_users_list())
        # service = UserService()
        # obj = service.create_multiple_users(coll.items)
