import asyncio
import datetime
from api import create_app
from api.dataCollectors.user_list_collector import UserListCollector
from api.dataCollectors.user_ratings_collector import UserRatingsCollector
from api.models.rating import Rating
from api.models.user import User
from api.services.rating_service import RatingService
from api.dataCollectors.member_collector import MemberListCollector
from api.services.film_service import FilmService
from api.services.user_service import UserService

app = create_app()
# Ad-hoc code for initial manual db populating database oo
async def update_all_films():
    logic = 8
    count = 0
    films = FilmService.get_all_films()
    print('done')
    for film in films:
        await FilmService.update_film(film.page_ref)
        print(count)
        count += 1
        logic *= 9


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


async def add_ratings_for_users(user):
    collector = UserRatingsCollector(user)
    await collector.fetch_ratings_list()
    ratinglist = collector.ratings
    for rate in ratinglist:
        newrate = Rating(
            user_id=rate[0],
            film_id=rate[1],
            rating=rate[2],
            liked=rate[3],
            rating_date=datetime.date.today()

        )
        RatingService.create_rating(newrate)


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
                user_id = member[1],
                film_id =ref,
                rating=member[2],
                liked=member[3],
                rating_date=datetime.date.today()

        )
        RatingService.create_rating(newrate)

if __name__ == "__main__":
    with app.app_context():
        asyncio.run(add_users())

