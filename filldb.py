import asyncio
import datetime

from api import create_app
from api.models.rating import Rating
from api.models.user import User
from api.services.rating_service import RatingService
from api.dataCollectors.member_collector import MemberListCollector

from api.services.user_service import UserService

app = create_app()

async def member():
    ref = 'parasite-2019'
    collector = MemberListCollector(ref)
    await collector.fetch_film_list()
    ratinglist = collector.members


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
        asyncio.run(member())

