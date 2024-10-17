from  api.services.rating_service import RatingService
from api.services.film_service import FilmService

class Film_Rec_Service:

    @staticmethod
    def get_films_reccomendations(film_ref, rating = 10):

        subquery_users = RatingService.get_for_ratings_film(film_ref)
        # Step 2: Count the number of 5-star ratings for films rated by those users
        film_ratings_count = RatingService.get_films_rated_by_users(subquery_users)

        # Step 3: Get the top 10 films based on 5-star ratings
        top_films = FilmService.get_films_recs(film_ratings_count, limit=10)

        return top_films
