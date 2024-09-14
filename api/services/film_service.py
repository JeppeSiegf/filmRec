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

        existing_film = FilmRepository.get_film_by_ref(film.page_ref)
        if existing_film:
            raise ValueError(f'{film.title}({film.title}) already exists.')

        return FilmRepository.create_film(film)

    @staticmethod
    def update_film(film: Film):
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")
        return FilmRepository.update_film(film)

    @staticmethod
    def delete_film(film_id):
        return FilmRepository.delete_film(film_id)


    @staticmethod
    def search_films(query: str):
        return FilmRepository.search_films(query)