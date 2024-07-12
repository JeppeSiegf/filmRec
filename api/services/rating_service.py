from api.repositories.rating_repository import RatingRepository

class RatingService:

    @staticmethod
    def get_all_ratings():
        return RatingRepository.get_all_ratings()

    @staticmethod
    def get_ratings_by_user(user_id):
        return RatingRepository.get_ratings_by_user(user_id)

    @staticmethod
    def get_ratings_for_film(film_id):
        return RatingRepository.get_ratings_for_film(film_id)

    @staticmethod
    def get_rating_by_id(rating_id):
        return RatingRepository.get_rating_by_id(rating_id)

    @staticmethod
    def create_rating(rating, like, film_id, user_id):
        return RatingRepository.create_rating(rating, like, film_id, user_id)

    @staticmethod
    def update_rating(rating_id, rating=None, like=None):
        return RatingRepository.update_rating(rating_id, rating, like)

    @staticmethod
    def delete_rating(rating_id):
        return RatingRepository.delete_rating(rating_id)
