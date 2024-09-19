import requests
from bs4 import BeautifulSoup
from json import loads

class FilmDetailCollector:
    def __init__(self, film_ref: str) -> None:
        if not isinstance(film_ref, str):
            raise ValueError(f'Invalid film reference: {film_ref}')

        self.ref = film_ref

        self.domain = 'https://letterboxd.com'
        self.headers = {
            "Referer": self.domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.builder = "lxml"
        self.url = f"https://letterboxd.com/film/{film_ref}/"
        self.dom = self.get_parsed_page(self.url)



        self.total_watches = 0
        self.image_ref = None
        self.genre = []

    def get_parsed_page(self, url: str) -> BeautifulSoup:
        print(f"Fetching URL: {url}")
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.RequestException as e:
            raise RuntimeError(f"Error connecting to {url}: {e}")

        try:
            dom = BeautifulSoup(response.text, self.builder)
        except Exception as e:
            raise RuntimeError(f"Error parsing response from {url}: {e}")

        return dom

    # Example method to extract details (fill in with actual logic)
    def extract_details(self):
        # Placeholder for actual extraction logic
        self.get_movie_genres(self.dom)
        self.get_movie_poster(self.dom)

    def get_movie_genres(self, dom) -> list:

        genres_section  = dom.find(attrs={"id": ["tab-genres"]})
        genres_header = genres_section.find("h3", string="Genres")
        genre_div = genres_header.find_next_sibling("div", class_="text-sluglist")
        genre_links = genre_div.find_all("a", class_="text-slug")

        genres = []
        for item in genre_links:
            genres.append(item.text)

        self.genre = genres

    def get_movie_poster(self, dom) -> str:

        script = dom.find("script", type="application/ld+json")
        print(script)
        script = loads(script.text.split('*/')[1].split('/*')[0]) if script else None

        # crop: list=(1500, 1000)
        # .replace('230-0-345', f'{crop[0]}-0-{crop[1]}')
        # crop: list=(1500, 1000)
        # .replace('230-0-345', f'{crop[0]}-0-{crop[1]}')
        if script:
            poster = script['image'] if 'image' in script else None
            self.img_ref = poster.split('?')[0] if poster else None
        else:
            self.img_ref = None


    # Actually returns amount of ratings rather than watches
    # Suitable replacement for now
    def get_total_watches(self, dom) -> str:

        script = dom.find("script", type="application/ld+json")
        print(script)
        script = loads(script.text.split('*/')[1].split('/*')[0]) if script else None

        if script:
            self.total_watches = script.get('aggregateRating', {}).get('ratingCount', None)
        else:
            self.total_watches = 0



if __name__ == "__main__":
    film = FilmDetailCollector('pulp-fiction')
    film.get_total_watches(film.dom)
    print(film.total_watches)
