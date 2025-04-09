from api.repositories.user_repository import UserRepository

from api.repositories.user_repository import UserRepository
from api.models.user import User


class UserService:

    @staticmethod
    def get_all_users():
        return UserRepository.get_all_users()

    @staticmethod
    def get_user_by_profile_ref(profile_ref):
        return UserRepository.get_user_by_profile_ref(profile_ref)


    @staticmethod
    def create_user(user: User):
        if not isinstance(user, User):
            raise TypeError("Expected a User instance.")

        existing_film = UserRepository.get_user_by_profile_ref(user.profile_ref)
        if existing_film:
            print('already in db')
            return None  # Raise an exception if the film does not exist

        return UserRepository.create_user(user)

    @staticmethod
    async def create_multiple_users(user_tuple):

        if not isinstance(user_tuple, list):
            raise TypeError("Expected a list of tuples.")

        user_data = [User.map(user_tuple) for user_tuple in user_tuple]

        # Filter out None values (invalid mappings)
        user_data = [user for user in user_data if user is not None]

        if not user_data:
            print("No valid films to insert.")
            return []

        inserted_films = UserRepository.bulk_insert(user_data)

        return inserted_films

    @staticmethod
    def update_user(user: User):
        if not isinstance(user, User):
            raise TypeError("Expected a User instance.")
        return UserRepository.update_user(user.profile_ref, user)
    @staticmethod
    async def update_multiple_user(users):

        for user in users:
            await UserRepository.update_user(user.profile_ref, users)

    @staticmethod
    def delete_user(user_id):
        return UserRepository.delete_user(user_id)
