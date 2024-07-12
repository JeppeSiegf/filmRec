from datetime import datetime
from api import db


class User(db.Model):
    class User(db.Model):
        __tablename__ = 'user'

        id = db.Column(db.Integer, primary_key=True)
        profile_ref = db.Column(db.String(100), nullable=False)
        username = db.Column(db.String(250))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'last_update': self.last_update.isoformat()
        }