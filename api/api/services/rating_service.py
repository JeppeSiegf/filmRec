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
        
        if not rating_data:
            return []
        if not isinstance(rating_data, list) or not all(isinstance(r, dict) for r in rating_data):
            raise TypeError("Expected a list of dictionaries.")

        to_upsert = [
            {
                'user_id': r['user_id'],
                'film_id': r['film_id'],
                'rating': int(r['rating']),
                'liked': r.get('liked', int(r['rating']) >= 7),
                'rating_date': datetime.fromisoformat(r['rating_date']) if isinstance(r.get('rating_date'), str) else r.get('rating_date', datetime.utcnow())
            }
            for r in rating_data if r.get('user_id') and r.get('film_id') and r.get('rating') is not None
        ]

        self.repo.upsert(to_upsert)
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

