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
    def get_latest_rating_by_user(user_id):
        return RatingRepository.get_latest_rating_by_user(user_id)


    @staticmethod
    def create_rating(rating: Rating):
        if not isinstance(rating, Rating):
            raise TypeError("Expected a Rating instance.")
        return RatingRepository.create_rating(rating)


    @staticmethod
    def upsert_user_ratings(rating_data: list[tuple]) -> list[dict]:

        if not rating_data:
            return []

        # Extract unique user and film refs
        user_refs = {r[0] for r in rating_data}
        film_refs = {r[1] for r in rating_data}

        # Fetch all users and films with one query each
        users = User.query.filter(User.profile_ref.in_(user_refs)).all()
        films = Film.query.filter(Film.page_ref.in_(film_refs)).all()

        user_map = {u.profile_ref: u for u in users}
        film_map = {f.page_ref: f for f in films}

        # Filter ratings that have both a valid user and film
        valid_ratings = [
            r for r in rating_data
            if r[0] in user_map and r[1] in film_map and r[2] is not None
        ]
        if not valid_ratings:
            print("No valid ratings to process.")
            return []

        # Step 4: Create set of (film_id, user_id) pairs for lookup
        film_user_keys = {
            (film_map[r[1]].page_ref, user_map[r[0]].profile_ref) for r in valid_ratings
        }

        # Step 5: Get existing rating map
        existing_map = RatingRepository.get_existing_rating_map_bulk(film_user_keys)

        to_upsert = []

        # Step 6: Build rating objects for upsert
        for user_ref, film_ref, rating_value, liked in valid_ratings:
            user_id = user_map[user_ref].profile_ref
            film_id = film_map[film_ref].page_ref
            key = (film_id, user_id)

            if key in existing_map:
                # Update existing rating
                rating = existing_map[key]
                rating.rating = rating_value
                rating.liked = liked
                rating.rating_date = datetime.utcnow()
                to_upsert.append(rating)
            else:
                # Create new rating
                to_upsert.append({
                    "user_id": user_id,
                    "film_id": film_id,
                    "rating": rating_value,
                    "liked": liked,
                    "rating_date": datetime.utcnow()
                })

        # Step 7: Commit using repository
        try:
            RatingRepository.bulk_upsert_ratings(to_upsert)
            print(f"Upserted {len(to_upsert)} ratings.")
        except Exception as e:
            print(f"Error during bulk rating upsert: {e}")
            raise

        return to_upsert

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
