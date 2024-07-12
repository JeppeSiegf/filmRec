from api.repositories.film_repository import FilmRepository

class FilmService:

    @staticmethod
    def get_all_films():
        return FilmRepository.get_all_films()

    @staticmethod
    def get_film_by_id(film_id):
        return FilmRepository.get_film_by_id(film_id)

    @staticmethod
    def create_film(title, year, total_watches, ref, img_reg, genres):
        return FilmRepository.create_film(title, year, total_watches, ref, img_reg, genres)

    @staticmethod
    def update_film(film_id, title=None, year=None, total_watches=None, ref=None, img_reg=None, genres=None):
        return FilmRepository.update_film(film_id, title, year, total_watches, ref, img_reg, genres)

    @staticmethod
    def delete_film(film_id):
        return FilmRepository.delete_film(film_id)