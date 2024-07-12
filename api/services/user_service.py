from api.repositories.user_repository import UserRepository

class UserService:

    @staticmethod
    def get_all_users():
        return UserRepository.get_all_users()

    @staticmethod
    def get_user_by_id(user_id):
        return UserRepository.get_user_by_id(user_id)

    @staticmethod
    def create_user(username):
        return UserRepository.create_user(username)

    @staticmethod
    def update_user(user_id, username=None):
        return UserRepository.update_user(user_id, username)

    @staticmethod
    def delete_user(user_id):
        return UserRepository.delete_user(user_id)
