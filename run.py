import asyncio
import datetime

from api import create_app
from api.models.rating import Rating
from api.models.user import User
from api.services.rating_service import RatingService
from api.dataCollectors.member_collector import MemberListCollector

from api.services.user_service import UserService

app = create_app()


if __name__ == "__main__":

    app.run(debug=True, use_reloader=False, threaded=True)