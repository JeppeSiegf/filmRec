from sqlalchemy import Column, Integer, String, Date
from api import db

class User(db.Model):
    __tablename__ = 'user'  # Remove quotes

    profile_ref = Column(String(250), primary_key=True, nullable=False)  # Primary key
    id = Column(Integer, default=db.func.nextval('id_seq'), nullable=False)  # Auto-incrementing ID
    username = Column(String(500))  # Username (can be NULL)
    last_updated = Column(Date, nullable=False)  # Last update date



    def __repr__(self):
        return f'<User {self.username} (profile_ref={self.profile_ref})>'