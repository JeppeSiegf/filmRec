import asyncio
from datetime import datetime

from .. import create_app
#from dataCollectors.ratings_collector import RatingsCollector
from ..repositories.rating_repository import RatingRepository
from ..services.film_service import FilmService
from ..services.user_service import UserService


class RatingService:

    def __init__(self):

        self.repo = RatingRepository()
        self.user_service = UserService()
        self.film_service = FilmService()

    def get_all_ratings(self):
        return self.repo.get_all_ratings()

    def get_latest_rating_by_user(self, user_id):
        return self.repo.get_latest_rating_by_user(user_id)

    def get_latest_rating_by_all_users(self):
        return self.repo.get_latest_ratings_for_all_users()


    def upsert_user_ratings(self, rating_data: list[dict]) -> list[dict]:
        """Upsert user ratings from JSON format data."""

        if not rating_data:
            return []
        # Validate input format
        if not isinstance(rating_data, list) or not all(isinstance(r, dict) for r in rating_data):
            raise TypeError("Expected a list of dictionaries.")

        # Extract unique user and film refs from JSON objects
        user_refs = {r.get('user_id') for r in rating_data if r.get('user_id')}
        film_refs = {r.get('film_id') for r in rating_data if r.get('film_id')}

        if not user_refs or not film_refs:
            print("No valid user_id or film_id found in rating data.")
            return []

        # Fetch all users and films with one query each
        valid_users = self.user_service.get_user_by_profile_refs(user_refs)
        valid_films = self.film_service.get_films_by_refs(film_refs)

        user_map = {u.profile_ref: u for u in valid_users}
        film_map = {f.page_ref: f for f in valid_films}

        # Filter and process ratings that have both a valid user and film
        valid_ratings = []
        for rating in rating_data:
            user_id = rating.get('user_id')
            film_id = rating.get('film_id')
            rating_value = rating.get('rating')

            # Skip if missing required fields or invalid references
            if (user_id in user_map and
                    film_id in film_map and
                    rating_value is not None):
                valid_ratings.append(rating)

        if not valid_ratings:
            print("No valid ratings to process.")
            return []

        # Convert to database format
        to_upsert = []
        for r in valid_ratings:
            rating_dict = {
                'user_id': r['user_id'],  # Keep as profile_ref
                'film_id': r['film_id'],  # Keep as page_ref
                'rating': int(r['rating']) if r.get('rating') is not None else None,
                'liked': r.get('liked', int(r['rating']) >= 7 if r.get('rating') else False),
                'rating_date': datetime.fromisoformat(r['rating_date']) if isinstance(r.get('rating_date'), str) else r.get(
                    'rating_date', datetime.utcnow())
            }
            to_upsert.append(rating_dict)

        try:
            self.repo.upsert(to_upsert)
            print(f"Upserted {len(to_upsert)} ratings.")
        except Exception as e:
            print(f"Error during bulk rating upsert: {e}")
            raise

        return to_upsert


if __name__ == '__main__':

    app = create_app()
    with app.app_context():
        pass
        # coll = RatingsCollector('se7en')
        # rates = asyncio.run(coll.fetch_ratings_list())
        # service = RatingService()
        # obj = service.upsert_user_ratings(coll.items)
        # print(obj)

