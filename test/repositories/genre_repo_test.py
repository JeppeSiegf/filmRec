import pytest
from api import db
from api.models.genre import Genre
from api.repositories.genre_repository import GenreRepository
from sqlalchemy.exc import SQLAlchemyError

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

    def test_update_genre(self, test_db, test_genre):
        updated_genre = GenreRepository.update_genre(test_genre.id, {"genre": "Updated Genre"})
        assert updated_genre is not None
        assert updated_genre.genre == "Updated Genre"

    def test_delete_genre(self, test_db, test_genre):
        assert GenreRepository.delete_genre(test_genre.id) is True
        assert GenreRepository.get_genre_by_id(test_genre.id) is None

    def test_create_genre_db_error(self, mocker, test_db):

        mocker.patch.object(db.session, "add", side_effect=SQLAlchemyError)
        assert GenreRepository.create_genre("Error Genre") is None
