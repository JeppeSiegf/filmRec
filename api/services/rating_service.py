from api.repositories.rating_repository import RatingRepository
from api.models.rating import Rating
from api.models.user import User
from api.models.film import Film

class RatingService:

    @staticmethod
    def get_all_ratings():
        return RatingRepository.get_all_ratings()

    @staticmethod
    def get_rating_by_user_and_film(user_id, film_id):
        return RatingRepository.get_rating_by_user_and_film(user_id, film_id)

    @staticmethod
    def get_for_ratings_film(film_ref, rating=10):
        return RatingRepository.get_for_ratings_film(film_ref, rating)

    @staticmethod
    def get_films_rated_by_users(users, rating=10):
        return RatingRepository.get_films_rated_by_users(users, rating)

    @staticmethod
    def create_rating(rating: Rating):
        if not isinstance(rating, Rating):
            raise TypeError("Expected a Rating instance.")
        return RatingRepository.create_rating(rating.user_id, rating.film_id, rating.rating, rating.liked, rating.rating_date)

    @staticmethod
    def update_rating(rating: Rating):
        if not isinstance(rating, Rating):
            raise TypeError("Expected a Rating instance.")
        return RatingRepository.update_rating(rating)

    @staticmethod
    def delete_rating(rating_id):
        return RatingRepository.delete_rating(rating_id)
