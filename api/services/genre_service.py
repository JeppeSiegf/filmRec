from api.repositories.genre_repository import GenreRepository

class GenreService:

    @staticmethod
    def get_all_genres():
        return GenreRepository.get_all_genres()

    @staticmethod
    def get_genre_by_id(genre_id):
        return GenreRepository.get_genre_by_id(genre_id)
