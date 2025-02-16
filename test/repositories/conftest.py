from datetime import datetime
import pytest
from sqlalchemy.exc import SQLAlchemyError
from api import db, create_app
from api.models import User
from api.models.film import Film
from api.models.genre import Genre
from config import TestConfig


@pytest.fixture(scope="session")
def test_app():
    # Use the TestConfig class directly, which already has the test database URI
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="function")
def test_db(test_app):
    with test_app.app_context():
        db.session.begin_nested()
        yield db
        db.session.rollback()


@pytest.fixture
def test_film(test_db):
    film = Film(
        title="Test Film",
        page_ref="test123",
        total_watches=0,
        last_update=datetime.utcnow().date(),
        release_year=2023,
        image_ref="poster.jpg",
        image_ref_large="poster_large.jpg"
    )
    test_db.session.add(film)
    test_db.session.commit()

    yield film  # Provide the test film

    # Cleanup after test
    test_db.session.delete(film)
    test_db.session.commit()


@pytest.fixture
def test_genre(test_db):
    """Provides a test genre and ensures cleanup after each test."""
    genre = Genre(genre="Test Genre")
    test_db.session.add(genre)
    test_db.session.commit()
    yield genre

    test_db.session.delete(genre)
    test_db.session.commit()


@pytest.fixture
def test_user(test_db):
    """Provides a test user and ensures cleanup after each test."""
    user = User(
        username=f"TestUser_{datetime.utcnow().timestamp()}",
        profile_ref=f"test_user_{datetime.utcnow().timestamp()}",
        last_updated=datetime.utcnow().date()
    )
    test_db.session.add(user)
    test_db.session.commit()
    yield user

    try:
        test_db.session.delete(user)
        test_db.session.commit()
    except:
        test_db.session.rollback()


@pytest.fixture
def mock_db_session(mocker):
    session_mock = mocker.patch.object(db, "session")

    session_mock.add.side_effect = SQLAlchemyError("Mocked DB error")
    session_mock.commit.side_effect = SQLAlchemyError("Mocked DB error")
    session_mock.rollback.return_value = None
    session_mock.delete.side_effect = SQLAlchemyError("Mocked DB error")

    return session_mock