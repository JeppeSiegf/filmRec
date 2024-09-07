from api.repositories.film_repository import FilmRepository
from api.models.film import Film

class FilmService:

    @staticmethod
    def get_all_films():
        return FilmRepository.get_all_films()

    @staticmethod
    def get_film_by_page_ref(page_ref):
        return FilmRepository.get_film_by_ref(page_ref)

    @staticmethod
    def create_film(film: Film):
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")
        return FilmRepository.create_film(film)

    @staticmethod
    def update_film(film: Film):
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")
        return FilmRepository.update_film(film)

    @staticmethod
    def delete_film(film_id):
        return FilmRepository.delete_film(film_id)
