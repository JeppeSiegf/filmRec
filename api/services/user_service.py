from api.models.user import User
from api.repositories.user_repository import UserRepository


class UserService:

    def __init__(self):
        self.repo = UserRepository()

    def get_all_users(self):
        return self.repo.get_all_users()

    def get_user_by_profile_ref(self, profile_ref):
        return self.repo.get_user_by_profile_ref(profile_ref)

    def get_user_by_profile_refs(self, user_refs):
        return self.repo.get_user_by_profile_refs(user_refs)

    async def create_multiple_users(self, user_tuple):

        if not isinstance(user_tuple, list):
            raise TypeError("Expected a list of tuples.")

        user_data = [User.map(user_tuple) for user_tuple in user_tuple]

        # Filter out None values (invalid mappings)
        user_data = [user for user in user_data if user is not None]

        if not user_data:
            print("No valid films to insert.")
            return []

        inserted_films = self.repo.insert(user_data)

        return inserted_films
