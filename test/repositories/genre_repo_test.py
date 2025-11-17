from sqlalchemy.exc import SQLAlchemyError

from api import db
from api import Genre
from api import GenreRepository


class TestGenreRepository:
    def test_get_all_genres(self, test_db, test_genre):
        genres = GenreRepository.get_all_genres()
        assert isinstance(genres, list)
        assert len(genres) > 0
        assert test_genre in genres

    def test_get_genre_by_id(self, test_db, test_genre):
        genre = GenreRepository.get_genre_by_id(test_genre.id)
        assert genre is not None
        assert genre.genre == test_genre.genre

    def test_create_genre(self, test_db):
        new_genre = Genre(genre="New Genre")
        created_genre = GenreRepository.create_genre(new_genre.genre)
        assert created_genre is not None
        assert created_genre.genre == "New Genre"

        # Clean up the created genre
        if created_genre and created_genre.id:
            test_db.session.delete(created_genre)
            test_db.session.commit()

    def test_update_genre(self, test_db, test_genre):
        original_genre_name = test_genre.genre
        updated_genre = GenreRepository.update_genre(test_genre.id, {"genre": "Updated Genre"})
        assert updated_genre is not None
        assert updated_genre.genre == "Updated Genre"

        # Restore the original genre name for subsequent tests
        test_genre.genre = original_genre_name
        test_db.session.commit()

    def test_delete_genre(self, test_db, test_genre):
        # Create a temporary genre for deletion
        temp_genre = Genre(genre="Temporary Genre for Deletion")
        test_db.session.add(temp_genre)
        test_db.session.commit()

        genre_id = temp_genre.id

        assert GenreRepository.delete_genre(genre_id) is True
        assert GenreRepository.get_genre_by_id(genre_id) is None

    def test_create_genre_db_error(self, mocker, test_db):
        mocker.patch.object(db.session, "add", side_effect=SQLAlchemyError)
        assert GenreRepository.create_genre("Error Genre") is None
