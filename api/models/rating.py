from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import relationship
from api import db


class Rating(db.Model):
    __tablename__ = 'user_rating'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(250), nullable=False)
    film_id = Column(String(500), nullable=False)
    rating = Column(Integer, nullable=True)
    liked = Column(Boolean, nullable=False)
    rating_date = Column(Date, nullable=False)

    # Define relationships
    user = relationship('User', foreign_keys=[user_id], backref='ratings')
    film = relationship('Film', foreign_keys=[film_id], backref='ratings')

    def __repr__(self):
        return f'<UserRating user={self.user_id}, film={self.film_id}, rating={self.rating}, liked={self.liked}>'

