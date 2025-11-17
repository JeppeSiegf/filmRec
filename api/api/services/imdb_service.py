import requests

class IMDBService:

    BASE_URL = "https://api.imdbapi.dev/titles"
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    def get_rating(self, imdb_id: str) -> float | None:
        url = f"{self.BASE_URL}/{imdb_id}"
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            rating_data = data.get("rating")
            if rating_data and "aggregateRating" in rating_data:
                return rating_data["aggregateRating"]

            # fallback to older fields if API differs
            return data.get("imdbRating") or data.get("score")

        except requests.RequestException as e:
            print(f"Error fetching IMDb data for {imdb_id}: {e}")
            return None
