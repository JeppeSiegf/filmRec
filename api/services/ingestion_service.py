import asyncio

from api import create_app
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.dataCollectors.film_list_collector import FilmListCollector
from api.dataCollectors.series_collector import SeriesCollector
from api.dataCollectors.member_collector import MemberListCollector
from api.dataCollectors.ratings_collector import RatingsCollector
from api.dataCollectors.user_list_collector import UserListCollector

from api.services.film_service import FilmService
from api.services.rating_service import RatingService
from api.services.series_service import SeriesService
from api.services.user_service import UserService


class DataIngestionService:

    @classmethod
    async def ingest_film(cls, film_ref):
        collector = FilmDetailCollector(film_ref)
        await collector.fetch_page()
        await collector.extract_details()

        await FilmService.update_film(film_ref)

        return True

    @classmethod
    async def ingest_film_list(cls, username, list_title):
        collector = FilmListCollector(username, list_title)

        await collector.fetch_film_list()

        films = collector.items

        await FilmService.create_multiple_films(films)

    @classmethod
    async def ingest_user_list(cls, username):
        collector = UserListCollector(username)

        await collector.fetch_users_list()

        users = collector.items

        await UserService.create_multiple_users(users)

    @classmethod
    async def ingest_member_list(cls, film_ref):
        collector = MemberListCollector(film_ref)

        await collector.fetch_member_list()

        users = collector.users
        ratings = collector.ratings

        await UserService.create_multiple_users(users)
        await RatingService.upsert_user_ratings(ratings)

    @classmethod
    async def ingest_ratings_list(cls, username):
        collector = RatingsCollector(username)

        await collector.fetch_ratings_list()

        ratings = collector.items

        await RatingService.upsert_user_ratings(ratings)

    @classmethod
    async def ingest_series_list(cls):
        # TODO implement service and db
        collector = SeriesCollector()

        await collector.fetch_series_list()

        series = collector.items

        await SeriesService.upsertFilmSeries(series)


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        asyncio.run(DataIngestionService.ingest_series_list())

