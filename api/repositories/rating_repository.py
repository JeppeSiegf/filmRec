from sqlalchemy import func

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
    def get_for_ratings_film(film_ref,rating = 10):
        return (
            Rating.query
            .filter_by(film_id=film_ref, rating=rating)
            .with_entities(Rating.user_id)
            .subquery()  # Call subquery() on the entire query
        )


    @staticmethod
    def get_films_rated_by_users(users, rating=10, limit=10):
        top_films = (
            Rating.query
            .join(Film, Rating.film_id == Film.page_ref)
            .with_entities(
                Film.page_ref,
                Film.title,
                func.count(Rating.user_id).label('five_star_count')  # Add five_star_count here
            )
            .filter(Rating.rating == 10)
            .group_by(Film.page_ref, Film.title)
            .order_by(func.count(Rating.user_id).desc())
            .limit(limit)
            .subquery()  # Create a subquery from this
        )
        return top_films



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

        # Check if a rating already exists for this user and film
        existing_rating = Rating.query.filter_by(user_id=rating.user_id, film_id=rating.film_id).first()
        if existing_rating:
            print('already there')
            return None  # Or you might want to update the existing rating instead

        # Create and add new rating

        db.session.add(rating)
        db.session.commit()
        return rating

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
