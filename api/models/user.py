from datetime import datetime
from api import db

class User(db.Model):
    __tablename__ = 'user'

    # Reflecting the exact schema provided
    profile_ref = db.Column(db.String(250), primary_key=True, nullable=False)  # Primary key
    id = db.Column(db.Integer, default=db.func.nextval('id_seq'), nullable=False)  # Auto-incrementing ID using PostgreSQL sequence
    username = db.Column(db.String(500))  # Username (can be NULL)
    last_updated = db.Column(db.Date, nullable=False)  # Last update date

    # Optional: relationships if needed
    # ratings = db.relationship('Rating', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username} (profile_ref={self.profile_ref})>'