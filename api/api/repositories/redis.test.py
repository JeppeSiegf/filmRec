from typing import List

import redis
import json
from datetime import datetime

from redis import Redis

from .. import create_app
from ..services import RatingService


class Redistest:

    def __init__(self, host='localhost', port=6379, db=1):
        self.r = redis.Redis(host=host, port=port, db=db)

    def log_update(self, object_id: str, update_type: str, update_data: str):
        key = f"update:{object_id}"
        value = {
            "type": update_type,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Store as JSON string
        self.r.set(key, json.dumps(value))

    def upload_user_ratings_to_redis(self, ratings: List):
        for ur in ratings:
            key = ur.user_id
            value = {
                "type": "user",
                "film": ur.film_id
            }
            self.r.set(key, json.dumps(value))

    def dump_redis(self):
        result = {}
        for key in self.r.scan_iter("*"):
            value = self.r.get(key)
            try:
                value = json.loads(value)
            except Exception:
                value = value.decode()  # fallback to string
            result[key.decode()] = value
        return result

if __name__ == '__main__':

    app = create_app()
    with app.app_context():
        service = RatingService()
        obj = service.get_latest_rating_by_all_users()
        redis = Redistest()
        redis.upload_user_ratings_to_redis(obj)
        dump = redis.dump_redis()
        print(dump)
