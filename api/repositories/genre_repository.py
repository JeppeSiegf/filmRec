from sqlalchemy.exc import SQLAlchemyError
from api import db
from api.models.genre import Genre
from api.models.film import Film


class GenreRepository:
    @staticmethod
    def get_all_genres():
        """Fetch all genres."""
        try:
            return Genre.query.all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    @staticmethod
    def get_genre_by_id(genre_id):
        """Fetch a genre by its ID."""
        try:
            return Genre.query.get(genre_id)
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    @staticmethod
    def create_genre(name):
        """Create a new genre and save it to the database."""
        if not name:
            raise ValueError("Genre must have a name.")

        genre = Genre(genre=name)
        try:
            db.session.add(genre)
            db.session.commit()
            return genre
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None

    @staticmethod
    def update_genre(genre_id, updates):
        """Update an existing genre by applying changes from a dictionary."""
        try:
            genre = Genre.query.get(genre_id)
            if not genre:
                return None  # Gracefully handle missing genre

            for key, value in updates.items():
                setattr(genre, key, value)

            db.session.commit()
            return genre
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None

    @staticmethod
    def delete_genre(genre_id):
        """Delete a genre by its ID."""
        try:
            genre = Genre.query.get(genre_id)
            if genre:
                db.session.delete(genre)
                db.session.commit()
                return True
            return False  # Genre not found
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None
