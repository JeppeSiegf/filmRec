import random

from api.services.rating_service import RatingService
from api.services.film_service import FilmRepository, FilmService
from api.recomendation_engine.ALS_recommendation import ALSRecommender


class Film_Rec_Service:

    @staticmethod
    def get_films_recommendations(page_ref, len):

        is_in_db = FilmService.get_film_by_page_ref(page_ref,False)
        if is_in_db is None:
            print('not in db')
            return []
        # TODO remove once model handles metadata
        top_k = len + 1

        recommender = ALSRecommender()
        recs = recommender.get_similar_items(page_ref, top_k)

        film_recs = FilmService.get_films_by_refs(recs,True)
        # TODO remove once model handles metadata
        film_recs.pop(0)
        random.shuffle(film_recs)

        return film_recs
