from api.repositories.genre_repository import GenreRepository
from api.models.genre import Genre

class GenreService:

    @staticmethod
    def get_all_genres():
        return GenreRepository.get_all_genres()


    @staticmethod
    def get_genre_by_id(genre_id):
        return GenreRepository.get_genre_by_id(genre_id)

    @staticmethod
    def create_genre(genre: Genre):
        if not isinstance(genre, Genre):
            raise TypeError("Expected a Genre instance.")
        return GenreRepository.create_genre(genre)

    @staticmethod
    def update_genre(genre: Genre):
        if not isinstance(genre, Genre):
            raise TypeError("Expected a Genre instance.")
        return GenreRepository.update_genre(genre)

    @staticmethod
    def delete_genre(genre_id):
        return GenreRepository.delete_genre(genre_id)
