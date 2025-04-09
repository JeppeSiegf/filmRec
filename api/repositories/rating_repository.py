from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from api.models.rating import Rating
from api.models.user import User
from api.models.film import Film
from api import db


class RatingRepository:

    @staticmethod
    def get_all_ratings():
        return Rating.query.all()


    @staticmethod
    def get_latest_rating_by_user(user_id):
        return (
            Rating.query
            .filter_by(user_id=user_id)
            .order_by(Rating.rating_date.desc())
            .first()
        )


    @staticmethod
    def create_rating(rating: Rating):
        # Check if user exists, if not, create a new user
        user = User.query.filter_by(profile_ref=rating.user_id).first()

        if not user:
            print('no user')
            return None

        # Check if film exists, if not, create a new film
        film = Film.query.filter_by(page_ref=rating.film_id).first()

        if not film:
            print('no film')
            return None

        if rating.rating is not None and (rating.rating < 0 or rating.rating > 10):
            raise ValueError("Rating must be between 0 and 5.")

        # Chreeck if a rating already exists for this user and film
        existing_rating = Rating.query.filter_by(user_id=rating.user_id, film_id=rating.film_id).first()
        if existing_rating:
            print('already there')
            return None  # Or you might want to update the existing rating instead

        # Create and add new rating

        db.session.add(rating)
        db.session.commit()
        return rating

    @staticmethod
    def delete_rating(rating_id):
        rating = Rating.query.get(rating_id)
        if rating:
            db.session.delete(rating)
            db.session.commit()

    @staticmethod
    def get_existing_rating_map(user_id: str, film_refs: list[str]):

        ratings = db.session.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.film_id.in_(film_refs)
        ).all()
        return {(r.film_id, r.user_id): r for r in ratings}

    @staticmethod
    def bulk_update_ratings(ratings: list[Rating]):
        if not ratings:
            return
        for rating in ratings:
            db.session.merge(rating)  # or just update fields manually
        db.session.commit()  # Commit only the update portion

    @staticmethod
    def bulk_insert_ratings(ratings: list[Rating]):
        if not ratings:
            return
        db.session.bulk_save_objects(ratings)
        db.session.commit()  # Commit only the insert portion
