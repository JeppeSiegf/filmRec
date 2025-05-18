import asyncio
from datetime import datetime

import pandas as pd

from api import create_app
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.dataCollectors.utils.sort_categories import FilmSorting, RatingSorting
from api.models.user import User
from api.services.film_service import FilmService
from api.services.user_service import UserService

app = create_app()
film_service = FilmService()


# Ad-hoc code for initial manual db populating database oo
async def update_all_films():

    films = film_service.get_all_films()
    refs = [f[0] for f in films]
    await film_service.update_multiple_films(refs)
    print('done2')


async def add_users():
    collector = UserPaginateParser()
    await collector.fetch_user_list()
    userlist = collector.users
    for user in userlist:
        newuser = User(profile_ref=user[1],
                       username=user[0],
                       last_updated=datetime.date.today()
                       )
        UserService.create_user(newuser)
        await add_ratings_for_users(newuser.profile_ref)


async def add_ratings_for_users():
    users = UserService.get_all_users()
    for user in users:
        stoppoint = RatingService.get_latest_rating_by_user(user.profile_ref)
        collector = UserRatingsCollector(user.profile_ref, stoppoint.film_id)
        await collector.fetch_ratings_list(order=RatingSorting.LAST_ADDITION)
        ratings = collector.items
        print(ratings)
        RatingService.upsert_user_ratings(ratings)





# TODO move to worker
async def updatemovies():
    collector = FilmPaginateParser('hershwin', 'all-the-movies', 'black-dog-2024')
    await collector.fetch_series_list(order=FilmSorting.LAST_ADDITION)
    newfils = collector.items
    print(newfils[0])
    await FilmService.create_multiple_films(newfils)
    await FilmService.update_multiple_films([t[1] for t in newfils])


async def proxytest():
    collector = FilmDetailCollector('pulp-fiction')
    await collector.fetch_page()
    await collector.extract_details()
    newfils = collector.image_ref
    print(newfils)


async def allrates():
    start_time = time.time()  # Start the timer
    rates = RatingService.get_all_ratings()
    end_time = time.time()  # End the timer
    ratedf = RatingService.convert_ratings_to_dataframe(rates)
    print(f"Retrieved ratings in {end_time - start_time:.2f} seconds")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 1000)  # Show all columns
    pd.set_option('display.width', None)  #
    print(ratedf.tail)
    df_head_1000 = ratedf.head(1000)

    print(df_head_1000)  # Index 1 corresponds to the second row

    # Count the occurrences of each value in the row


from api.services.rating_service import RatingService
import time






if __name__ == "__main__":
    with app.app_context():
        # asyncio.run(create_model())
        asyncio.run(update_all_films())
