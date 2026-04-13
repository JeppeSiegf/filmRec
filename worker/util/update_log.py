
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
        try:
            for key in self.r.scan_iter(match='*'):  # Get all keys
                raw = self.r.get(key)
                if raw:
                    try:
                        obj = json.loads(raw)
                        if obj.get('type') == update_type:
                            results[key] = obj
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error in get_all method: {e}")

        return results
