import asyncio
from timeit import Timer

from api import create_app
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.dataCollectors.film_list_collector import FilmListCollector
from api.dataCollectors.member_collector import MemberListCollector
from api.dataCollectors.ratings_collector import RatingsCollector
from api.dataCollectors.series_collector import SeriesCollector
from api.dataCollectors.user_list_collector import UserListCollector
from api.services.film_service import FilmService
from api.services.rating_service import RatingService
from api.services.series_service import SeriesService
from api.services.user_service import UserService


class DataIngestionService:


    def ingest_film(self, film_refs):

        service = FilmService()
        updated_films = []

        #for film_ref in film_refs:
         #   collector = FilmDetailCollector(film_ref)
          #  asyncio.run(collector.fetch_page())
           # asyncio.run(collector.extract_details())

            # Assuming the collector object now has all the necessary fields
            # and can be passed directly to update_multiple_films
            #updated_films.append(collector)

        asyncio.run(service.update_multiple_films(film_refs))

    def ingest_film_list(self, username, list_title):
        collector = FilmListCollector(username, list_title)
        service = FilmService()

        asyncio.run(collector.fetch_film_list())

        films = collector.items

        service.create_multiple_films(films)


    def ingest_user_list(self, username):

        collector = UserListCollector(username)
        service = UserService()

        asyncio.run(collector.fetch_users_list())

        users = collector.items

        service.create_multiple_users(users)


    def ingest_member_list(self, film_ref):
        collector = MemberListCollector(film_ref)
        user_service = UserService()
        rating_service = RatingService()

        asyncio.run(collector.fetch_member_list())

        users = collector.users
        ratings = collector.ratings

        user_service.create_multiple_users(users)
        rating_service.upsert_user_ratings(ratings)


    def ingest_ratings_list(self, username):
        collector = RatingsCollector(username)
        service = RatingService()

        asyncio.run(collector.fetch_ratings_list())

        ratings = collector.items

        service.upsert_user_ratings(ratings)

    def ingest_series_list(self):
        # TODO implement service and db
        collector = SeriesCollector()
        service = SeriesService()

        asyncio.run(collector.fetch_series_list())

        series = collector.items

        service.upsertFilmSeries(series)


if __name__ == "__main__":
    app = create_app()
    with app.app_context():

        filmserv = FilmService()
        films = filmserv.get_all_films()
        print('gottem')
        service = DataIngestionService()
        service.ingest_film([f.page_ref for f in films])

