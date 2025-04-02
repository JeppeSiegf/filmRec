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
    def update_user(user: User):
        if not isinstance(user, User):
            raise TypeError("Expected a User instance.")
        return UserRepository.update_user(user)

    @staticmethod
    def delete_user(user_id):
        return UserRepository.delete_user(user_id)
