from  api.services.rating_service import RatingService
from api.services.film_service import FilmRepository
from api.repositories.film_rec_repository import RecommendationRepository

class Film_Rec_Service:

    @staticmethod
    def get_films_reccomendations(film_ref):

        is_in_db = FilmRepository.get_film_by_ref(film_ref)
        if is_in_db is None:
            print('not in db')
            return None

        film_recs = []
        # topfilms = FilmRepository.get_similar_movies_based_on_distribution(film_ref)'
        topfilms = RecommendationRepository.get_similar_films(film_ref)
        for film in topfilms:
            print(film)

            rec = FilmRepository.get_film_by_ref(film)
            film_recs.append(rec)

        return film_recs
