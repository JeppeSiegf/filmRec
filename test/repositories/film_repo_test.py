from datetime import datetime

import pytest
from sqlalchemy.exc import SQLAlchemyError

from api import db
from api.models.film import Film
from api.repositories.film_repository import FilmRepository


def test_get_all_films(test_db, test_film):
    films = FilmRepository.get_all_films()
    assert isinstance(films, list)
    assert len(films) > 0
    assert test_film in films


def test_get_film_by_ref(test_db, test_film):
    film = FilmRepository.get_film_by_ref("test123")
    assert film is not None
    assert film.title == test_film.title


def test_get_film_by_ref_not_found(test_db):
    film = FilmRepository.get_film_by_ref("nonexistent_ref")
    assert film is None


def test_create_film(test_db):
    unique_suffix = datetime.utcnow().timestamp()
    new_film = Film(
        title=f"Test Film Create {unique_suffix}",
        page_ref=f"create_film_{unique_suffix}",
        total_watches=0,
        last_update=datetime.utcnow().date(),
        release_year=2023,
        image_ref=f"poster_{unique_suffix}.jpg",
        image_ref_large=f"poster_large_{unique_suffix}.jpg"
    )
    created_film = FilmRepository.create_film(new_film)

    assert created_film is not None
    assert created_film.title == new_film.title
    assert created_film.page_ref == new_film.page_ref


def test_update_film(test_db, test_film):
    updated_film = FilmRepository.update_film(test_film, {"title": "Updated Title"})
    assert updated_film is not None
    assert updated_film.title == "Updated Title"


def test_update_nonexistent_film(test_db):
    updated_film = FilmRepository.update_film(None, {"title": "Should Not Exist"})
    assert updated_film is None


def test_delete_film(test_db, test_film):
    FilmRepository.delete_film(test_film.page_ref)
    assert FilmRepository.get_film_by_ref(test_film.page_ref) is None


def test_delete_nonexistent_film(test_db):
    FilmRepository.delete_film("nonexistent_ref")
    assert FilmRepository.get_film_by_ref("nonexistent_ref") is None


def test_create_film_db_error(mocker, test_db):
    mocker.patch.object(db.session, "add", side_effect=SQLAlchemyError)
    new_film = Film(title="Error Film", page_ref="error123", last_update=datetime.utcnow().date())
    assert FilmRepository.create_film(new_film) is None


if __name__ == "__main__":
    pytest.main()
