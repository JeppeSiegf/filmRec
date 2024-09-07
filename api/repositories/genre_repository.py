from api.models.genre import Genre
from api import db


class GenreRepository:

    @staticmethod
    def get_all_genres():
        return Genre.query.all()

    @staticmethod
    def get_genre_by_id(genre_id):
        return Genre.query.get(genre_id)

    @staticmethod
    def create_genre(genre):
        if not isinstance(genre, Genre):
            raise TypeError("Expected a Genre instance.")

        if not genre.genre:
            raise ValueError("Genre must have a name.")

        db.session.add(genre)
        db.session.commit()
        return genre

    @staticmethod
    def update_genre(genre):
        """
        Instance method to update an existing genre instance.
        """
        if not isinstance(genre, Genre):
            raise TypeError("Expected a Genre instance.")

        existing_genre = Genre.query.get(genre.id)

        if not existing_genre:
            return None  # Return if the genre with the given ID is not found

        existing_genre.genre = genre.genre

        db.session.commit()
        return existing_genre

    @staticmethod
    def delete_genre(genre_id):
        genre = Genre.query.get(genre_id)
        if genre:
            db.session.delete(genre)
            db.session.commit()
