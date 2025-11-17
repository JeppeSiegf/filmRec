from datetime import datetime

from sqlalchemy import Column, Integer, String

from .. import db


class User(db.Model):
    __tablename__ = 'user'

    profile_ref = Column(String(250), primary_key=True, nullable=False)  # Primary key
    id = Column(Integer, default=db.func.nextval('id_seq'), nullable=False)  # Auto-incrementing ID
    username = Column(String(500))  # Username (can be NULL)
    last_updated = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last update date

    @staticmethod
    def map(user_tuple):
        if not isinstance(user_tuple, (list, tuple)):
            raise ValueError("Expected a tuple or list.")

        name = user_tuple[0] if len(user_tuple) > 0 else None
        profile_ref = user_tuple[1] if len(user_tuple) > 1 else None

        return {
            'profile_ref': profile_ref,
            'username': name,
            'last_updated': datetime.utcnow()
        }

    def __repr__(self):
        return f'<User {self.username} (profile_ref={self.profile_ref})>'
