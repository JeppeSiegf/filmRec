from datetime import datetime

import pandas as pd

from api.models.film import Film
from api.models.rating import Rating
from api.models.user import User
from api.repositories.rating_repository import RatingRepository
from api.services.film_service import FilmService
from api.services.user_service import UserService


class RatingService:

    def __init__(self):

        self.repo = RatingRepository()
        self.user_service = UserService()
        self.film_service = FilmService()


    def get_all_ratings(self):
        return self.repo.get_all_ratings()

    def get_latest_rating_by_user(self, user_id):
        return self.repo.get_latest_rating_by_user(user_id)

    def upsert_user_ratings(self, rating_data: list[tuple]) -> list[dict]:

        if not rating_data:
            return []

        # Extract unique user and film refs
        user_refs = {r[0] for r in rating_data}
        film_refs = {r[1] for r in rating_data}

        # Fetch all users and films with one query each

        valid_users = self.user_service.get_user_by_profile_refs(user_refs)

        valid_films = self.film_service.get_films_by_refs(film_refs, False)

        user_map = {u.profile_ref: u for u in valid_users}
        film_map = {f.page_ref: f for f in valid_films}

        # Filter ratings that have both a valid user and film
        valid_ratings = [
            r for r in rating_data
            if r[0] in user_map and r[1] in film_map and r[2] is not None
        ]
        if not valid_ratings:
            print("No valid ratings to process.")
            return []

        to_upsert = [
            {
                'user_id': user_map[r[0]].profile_ref,
                'film_id': film_map[r[1]].page_ref,
                'rating': int(r[2]) if r[2] is not None else None,
                'liked': bool(r[3]) if len(r) > 3 else (int(r[2]) >= 7 if r[2] is not None else False),
                'rating_date': datetime.utcnow()
            }
            for r in valid_ratings
        ]


        # Step 7: Commit using the bulk_upsert_ratings method
        try:
            self.repo.upsert(to_upsert)
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
