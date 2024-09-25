from api.models.rating import Rating
from api.models.user import User
from api.models.film import Film
from api import db


class RatingRepository:

    @staticmethod
    def get_all_ratings():
        return Rating.query.all()

    @staticmethod
    def get_rating_by_user_and_film(user_id, film_id):
        return Rating.query.filter_by(user_id=user_id, film_id=film_id).first()

    @staticmethod
    def create_rating(user_id, film_id, rating, liked, rating_date):
        # Check if user exists, if not, create a new user
        user = User.query.filter_by(profile_ref=user_id).first()
        if not user:
            user = User(profile_ref=user_id)  # Create with minimal fields
            db.session.add(user)

        # Check if film exists, if not, create a new film
        film = Film.query.filter_by(page_ref=film_id).first()
        if not film:
            film = Film(page_ref=film_id)  # Create with minimal fields
            db.session.add(film)

        if rating is not None and (rating < 0 or rating > 10):
            raise ValueError("Rating must be between 0 and 5.")

        # Check if a rating already exists for this user and film
        existing_rating = Rating.query.filter_by(user_id=user_id, film_id=film_id).first()
        if existing_rating:
            return None  # Or you might want to update the existing rating instead

        # Create and add new rating
        new_rating = Rating(
            user_id=user_id,
            film_id=film_id,
            rating=rating,
            liked=liked,
            rating_date=rating_date
        )

        db.session.add(new_rating)
        db.session.commit()
        return new_rating

    @staticmethod
    def update_rating(rating):
        """
        Update an existing rating instance.
        """
        if not isinstance(rating, Rating):
            raise TypeError("Expected a Rating instance.")

        existing_rating = Rating.query.get(rating.id)

        if not existing_rating:
            return None  # Return if the rating does not exist

        if rating.rating is not None:
            if rating.rating < 0 or rating.rating > 5:
                raise ValueError("Rating must be between 0 and 5.")
            existing_rating.rating = rating.rating


        if rating.liked is not None:
            existing_rating.liked = rating.liked
        if rating.rating_date is not None:
            existing_rating.rating_date = rating.rating_date

        db.session.commit()
        return existing_rating

    @staticmethod
    def delete_rating(rating_id):
        rating = Rating.query.get(rating_id)
        if rating:
            db.session.delete(rating)
            db.session.commit()
