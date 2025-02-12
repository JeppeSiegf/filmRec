from sqlalchemy.exc import SQLAlchemyError
from api import db
from api.models import User


class UserRepository:
    @classmethod
    def create_user(cls, user):
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except SQLAlchemyError:
            db.session.rollback()
            return None

    @classmethod
    def update_user(cls, profile_ref, update_data):
        try:
            user = cls.get_user_by_profile_ref(profile_ref)
            if not user:
                return None

            for key, value in update_data.items():
                setattr(user, key, value)

            db.session.commit()
            return user
        except SQLAlchemyError:
            db.session.rollback()
            return None

    @classmethod
    def delete_user(cls, profile_ref):
        try:
            user = cls.get_user_by_profile_ref(profile_ref)
            if not user:
                return False

            db.session.delete(user)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    @classmethod
    def get_user_by_profile_ref(cls, profile_ref):
        return db.session.query(User).filter_by(profile_ref=profile_ref).first()

    @classmethod
    def get_all_users(cls):
        return db.session.query(User).all()