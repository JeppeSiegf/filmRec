from api.models.user import User
from api import db


class UserRepository:

    @staticmethod
    def get_all_users():
        return User.query.all()

    @staticmethod
    def get_user_by_profile_ref(profile_ref):
        return User.query.filter_by(profile_ref=profile_ref).first()

    @staticmethod
    def create_user(user):
        if not isinstance(user, User):
            raise TypeError("Expected a User instance.")

        if not user.profile_ref:
            raise ValueError("User must have a profile_ref.")

        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user(user):

        if not isinstance(user, User):
            raise TypeError("Expected a User instance.")

        existing_user = User.query.filter_by(profile_ref=user.profile_ref).first()

        if not existing_user:
            return None  # Return if the user with the given profile_ref is not found

        existing_user.username = user.username
        existing_user.last_updated = user.last_updated

        db.session.commit()
        return existing_user

    @staticmethod
    def delete_user(profile_ref):
        user = User.query.filter_by(profile_ref=profile_ref).first()
        if user:
            db.session.delete(user)
            db.session.commit()