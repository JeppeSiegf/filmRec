from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .. import db


class Rating(db.Model):
    __tablename__ = 'user_rating'

    __table_args__ = (
        UniqueConstraint('user_id', 'film_id', name='rating_unique'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)  # Primary key
    user_id = Column(String(250), ForeignKey('user.profile_ref'), nullable=False)  # User ID with ForeignKey
    film_id = Column(String(500), ForeignKey('film.page_ref'), nullable=False)  # Film ID with ForeignKey
    rating = Column(Integer, nullable=True)  # Rating (can be NULL)
    liked = Column(Boolean, nullable=False)  # Liked status
    rating_date = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Date of the rating

    # Relationships
    user = relationship('User', backref='ratings', foreign_keys=[user_id])  # Ensure this matches the user_id
    film = relationship('Film', backref='ratings', foreign_keys=[film_id])  # Relationship to Film

    @staticmethod
    def map(rating_tuple, user_map: dict, film_map: dict):

        if not isinstance(rating_tuple, (list, tuple)):
            raise ValueError("Expected a tuple or list.")

        user_ref = rating_tuple[0] if len(rating_tuple) > 0 else None
        film_ref = rating_tuple[1] if len(rating_tuple) > 1 else None
        rating = rating_tuple[2] if len(rating_tuple) > 2 else None
        liked = rating_tuple[3] if len(rating_tuple) > 3 else None

        try:
            rating = int(rating) if rating is not None else None
        except (ValueError, TypeError):
            rating = None

        liked = bool(liked) if liked is not None else (rating is not None and rating >= 7)

        return {
            'user_id': user_map[user_ref].id,
            'film_id': film_map[film_ref].id,
            'rating': rating,
            'liked': liked,
            'rating_date': datetime.utcnow()
        }

    def __repr__(self):
        return f'<UserRating user={self.user_id}, film={self.film_id}, rating={self.rating}, liked={self.liked}>'
