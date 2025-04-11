import random

from api.recomendation_engine.ALS_recommendation import ALSRecommender
from api.services.film_service import FilmService


class FilmRecService:

    def __init__(self):
        self.rec_engine = ALSRecommender()
        self.film_service = FilmService()

    def get_films_recommendations(self, page_ref, len):

        is_in_db = FilmService.get_film_by_page_ref(page_ref, False)
        if is_in_db is None:
            print('not in db')
            return []
        # TODO remove once model handles metadata

        top_k = len + 1

        recs = self.rec_engine.get_similar_items(page_ref, top_k)

        film_recs = FilmService.get_films_by_refs(recs, True)

        # TODO remove once model handles metadata. Move shuffle to front-end
        film_recs.pop(0)
        random.shuffle(film_recs)

        film_proxies = []

        for film in film_recs:
            film_proxy = self.film_service.get_image_proxies(film)
            film_proxies.append(film_proxy)

        return film_proxies

    # TODO to be done
    def retrain_model(self):
        pass
