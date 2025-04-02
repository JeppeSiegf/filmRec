from api.services.rating_service import RatingService
from api.services.film_service import FilmRepository
from api.recomendation_engine.ANNS_recommendation import RecommenderSystem


class Film_Rec_Service:

    @staticmethod
    def get_films_reccommendations(page_ref):

        is_in_db = FilmRepository.get_film_by_ref(page_ref)
        if is_in_db is None:
            print('not in db')
            return []

        recommender = RecommenderSystem(None, None, None, None)  # Initialize without data
        rec_IDs = recommender.get_similar_movies(page_ref, 12)

        film_recs = []

        for id in rec_IDs:
            film = FilmRepository.get_film_by_ref(id[0])
            film_recs.append(film)

        return film_recs
