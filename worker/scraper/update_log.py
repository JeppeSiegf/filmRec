
import redis
import json
from datetime import datetime
from typing import Any, Optional, Dict

class UpdateLog:
    def __init__(self, url: str, decode_responses=True):

        self.r = redis.Redis.from_url(url=url, decode_responses=decode_responses)
        self._ns = None

    def _k(self, object_id: str) -> str:

        return str(object_id)

    def log(self, object_id: str, update_type: str, update_data: Any) -> bool:
        if object_id is None:
            raise ValueError("Object is None value")

        try:
            key = self._k(object_id)
            value = {
                "type": update_type,
                "film": update_data,
            }

            payload = json.dumps(value, default=str)
            result = self.r.set(key, payload)


        except Exception as e:
            print(f"Error in log method: {e}")
            return False

    def get(self, object_id: str) -> Optional[Dict]:

        key = self._k(object_id)
        raw = self.r.get(key)
        if raw is None:
            return None
        try:
            obj = json.loads(raw)
            return obj.get('film')
        except json.JSONDecodeError:
            return None

    def get_all(self, update_type: str) -> Dict[str, Dict]:
        results = {}

        pipe = self.r.pipeline()
        keys = []
        for key in self.r.scan_iter(match="*", count=100):  # Batch scan 100 keys at a time
            keys.append(key)
            pipe.get(key)  # Queue the GET command

        all_values = pipe.execute()

        for key, raw in zip(keys, all_values):
            if raw:
                try:
                    obj = json.loads(raw)
                    if obj.get('type') == update_type:
                        film_data = obj.get('film')
                        if film_data:
                            results[key] = film_data
                except json.JSONDecodeError:
                    continue

        return results

    def delete(self, object_id: str) -> int:
        return self.r.delete(self._k(object_id))

    def exists(self, object_id: str) -> bool:
        return self.r.exists(self._k(object_id)) == 1




