from datetime import datetime

import pandas as pd

from api import db
from api.repositories.rating_repository import RatingRepository
from api.models.rating import Rating
from api.models.user import User
from api.models.film import Film
from api.services.film_service import FilmService
from api.services.user_service import UserService


class RatingService:

    @staticmethod
    def get_all_ratings():
        return RatingRepository.get_all_ratings()

    @staticmethod
    def get_rating_by_user_and_film(user_id, film_id):
        return RatingRepository.get_rating_by_user_and_film(user_id, film_id)

    @staticmethod
    def get_latest_rating_by_user(user_id):
        return RatingRepository.get_latest_rating_by_user(user_id)

    @staticmethod
    def get_for_ratings_film(film_ref, rating=10):
        return RatingRepository.get_for_ratings_film(film_ref, rating)

    @staticmethod
    def get_films_rated_by_users(users, rating=10):
        return RatingRepository.get_films_rated_by_users(users, rating)

    @staticmethod
    def create_rating(rating: Rating):
        if not isinstance(rating, Rating):
            raise TypeError("Expected a Rating instance.")
        return RatingRepository.create_rating(rating)

    @staticmethod
    def update_rating(rating: Rating):
        if not isinstance(rating, Rating):
            raise TypeError("Expected a Rating instance.")
        return RatingRepository.update_rating(rating)

    @staticmethod
    def upsert_user_ratings(rating_data):
        if not rating_data:
            return []

        user_ref = rating_data[0][0]
        user = User.query.filter_by(profile_ref=user_ref).first()
        if not user:
            print(f"User '{user_ref}' not found. Aborting.")
            return []

        # Get film refs from input
        film_refs = [r[1] for r in rating_data]
        films = Film.query.filter(Film.page_ref.in_(film_refs)).all()
        # Map film page_ref to film.page_ref (both strings)
        film_ref_to_id = {f.page_ref: f.page_ref for f in films}

        # Validate only ratings that have a matching film and non-null rating
        valid_data = [r for r in rating_data if r[1] in film_ref_to_id and r[2] is not None]

        if not valid_data:
            print("No valid ratings to process.")
            return []

        # Use film page_refs for existing rating lookup (all strings now)
        valid_film_refs = [film_ref_to_id[r[1]] for r in valid_data]
        existing_map = RatingRepository.get_existing_rating_map(user.profile_ref, valid_film_refs)
        existing = []
        print("Existing ratings (in input order):")
        for user_ref, film_ref, _, _ in valid_data:
            film_id = film_ref_to_id[film_ref]
            rating = existing_map.get((film_id, user.profile_ref))
            if rating:
                print(f"Key: ({film_id}, {user.profile_ref}) -> {rating}")
                existing.append(((film_id, user.profile_ref), rating))
        to_create, to_update = [], []

        first_rating_object = None

        for user_ref, film_ref, rating_value, liked in valid_data:
            film_id = film_ref_to_id[film_ref]
            existing_rating = existing_map.get((film_id, user.profile_ref))
            if existing_rating:
                # Update the existing rating
                existing_rating.rating = rating_value
                existing_rating.liked = liked
                existing_rating.rating_date = datetime.utcnow()
                to_update.append(existing_rating)
                # Capture the first processed rating if not already set
                if first_rating_object is None:
                    first_rating_object = existing_rating
            else:
                # Create a new rating
                new_rating = Rating(
                    user_id=user.profile_ref,
                    film_id=film_id,
                    rating=rating_value,
                    liked=liked,
                    rating_date=datetime.utcnow()
                )
                to_create.append(new_rating)
                if first_rating_object is None:
                    first_rating_object = new_rating



        try:

            RatingRepository.bulk_update_ratings(to_update)
            RatingRepository.bulk_insert_ratings(to_create)
            if first_rating_object:
                # Call update_rating on the first rating object (whether updated or newly created)
                RatingRepository.update_rating(first_rating_object)
            print(f"Ratings upserted: {len(to_create)} created, {len(to_update)} updated.")
        except Exception as e:
            print(f"Error during rating upsert: {e}")
            raise

        return to_create + to_update

    @staticmethod
    def convert_ratings_to_dataframe(ratings):

        ratings_data = [{
            'id': rating.id,
            'user_id': rating.user_id,
            'film_id': rating.film_id,
            'rating': rating.rating,
            'liked': rating.liked,
            'rating_date': rating.rating_date
        } for rating in ratings]

        return pd.DataFrame(ratings_data)
