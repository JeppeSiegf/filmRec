import os
import urllib.parse


class ImageProxy:
    API_BASE = os.getenv("API_BASE_URL", "http://localhost:5000")
    ENDPOINT = "/api/proxy/image"

    @classmethod
    def get_proxified_url(cls, raw_url: str) -> str:
        if not raw_url:
            return raw_url

        encoded_url = urllib.parse.quote(raw_url, safe='')
        return f"{cls.API_BASE}{cls.ENDPOINT}?url={encoded_url}"
