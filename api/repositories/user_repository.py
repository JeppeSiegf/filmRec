from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from api import db
from api.models import User
from api.repositories.utils.bulk_persisting import BulkPersistence


class UserRepository(BulkPersistence):
    def __init__(self):
        super().__init__()
        self.cls_table = User
        self.conflict_columns = ["profile_ref"]
        self.update_columns = ['username', 'last_updated']

    def get_user_by_profile_ref(self, profile_ref):
        return db.session.query(User).filter_by(profile_ref=profile_ref).first()

    def get_user_by_profile_refs(self, profile_refs):
        return db.session.query(User).filter(User.profile_ref.in_(profile_refs)).all()

    def get_all_users(self):
        return db.session.query(User).all()
