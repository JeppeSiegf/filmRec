from api.models.rating import Rating
from api import db

class RatingRepository:

    @staticmethod
    def get_all_ratings():
        return Rating.query.all()

    @staticmethod
    def get_ratings_by_user(user_id):
        return Rating.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_ratings_for_film(film_id):
        return Rating.query.filter_by(film_id=film_id).all()

    @staticmethod
    def get_rating_by_id(rating_id):
        return Rating.query.get(rating_id)

    @staticmethod
    def create_rating(rating, like, film_id, user_id):
        rating = Rating(rating=rating, like=like, film_id=film_id, user_id=user_id)
        db.session.add(rating)
        db.session.commit()
        return rating

    @staticmethod
    def update_rating(rating_id, rating=None, like=None):
        rating_record = Rating.query.get(rating_id)
        if rating is not None:
            rating_record.rating = rating
        if like is not None:
            rating_record.like = like
        db.session.commit()
        return rating_record

    @staticmethod
    def delete_rating(rating_id):
        rating_record = Rating.query.get(rating_id)
        db.session.delete(rating_record)
        db.session.commit()