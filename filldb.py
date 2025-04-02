import asyncio
from datetime import datetime

import pandas as pd

from api import create_app
from api.dataCollectors.member_collector import MemberListCollector
from api.dataCollectors.sort_categories import FilmSorting, RatingSorting
from api.dataCollectors.user_list_collector import UserListCollector
from api.dataCollectors.user_ratings_collector import UserRatingsCollector
from api.dataCollectors.film_list_collector import FilmListCollector
from api.models.rating import Rating
from api.models.user import User
from api.recomendation_engine.ANNS_recommendation import RecommenderSystem
from api.services.film_service import FilmService
from api.services.user_service import UserService
from api.dataCollectors.film_detail_collector import FilmDetailCollector
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine



app = create_app()


# Ad-hoc code for initial manual db populating database oo
async def update_all_films():
    count = 0
    films = ['universal-language']  # Fetch all filmslms()
    print('done')
      # Extract only `page_ref`
    await FilmService.update_multiple_films(films)
    print('done2')


async def add_users():
    collector = UserListCollector()
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


async def ratings_for_films():
    ref = 'parasite-2019'
    collector = MemberListCollector(ref)
    await collector.fetch_film_list()
    ratinglist = collector.members
    # UserService.create_user(newuser)

    for member in ratinglist:
        newuser = User(profile_ref=member[1],
                       username=member[0],
                       last_updated=datetime.date.today()
                       )
        UserService.create_user(newuser)
        newrate = Rating(
            user_id=member[1],
            film_id=ref,
            rating=member[2],
            liked=member[3],
            rating_date=datetime.date.today()

        )
        RatingService.create_rating(newrate)

async def updatemovies():
    collector = FilmListCollector('hershwin','all-the-movies','black-dog-2024')
    await collector.fetch_film_list(order=FilmSorting.LAST_ADDITION)
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


def create_model():
    """
    Creates, trains, and saves the recommendation model.
    """
    start_time = time.time()

    # Fetch ratings data
    try:
        df = RatingService.convert_ratings_to_dataframe(RatingService.get_all_ratings())
        print(f"✅ Retrieved {len(df)} ratings in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"🚫 Failed to fetch ratings: {str(e)}")
        return

    # Initialize and train the recommender
    try:
        recommender = RecommenderSystem(df, "user_id", "film_id", "rating")
        # recommender.train()
        print(f"✅ Model trained in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"🚫 Failed to train model: {str(e)}")
        return

    # Compute similarity matrix
    try:
        # recommender.compute_item_similarity()
        print(f"✅ Similarity matrix computed in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"🚫 Failed to compute similarity matrix: {str(e)}")
        return

    # Save the model
    try:
        # recommender.save_model()
        print(f"✅ Model saved in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"🚫 Failed to save model: {str(e)}")
        return

    print(f"✅ Total time: {time.time() - start_time:.2f} seconds")


def get_recommendations(film_id, top_n=5):
    """
    Retrieves film recommendations.
    """
    start_time = time.time()

    # Load the recommender
    try:
        recommender = RecommenderSystem(None, None, None, None)  # Initialize without data

        print(f"✅ Model loaded in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"🚫 Failed to load model: {str(e)}")
        return []

    # Generate recommendations
    try:
        recommendations = recommender.get_similar_movies(film_id, top_n=top_n)
        print(f"✅ Recommendations generated in {time.time() - start_time:.2f} seconds")
        return recommendations
    except Exception as e:
        print(f"🚫 Failed to generate recommendations: {str(e)}")
        return []


if __name__ == "__main__":
    with app.app_context():
        # asyncio.run(create_model())
        asyncio.run(proxytest())
