from datetime import datetime
import testing.postgresql
import psycopg2
from faker import Faker
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from config import TestConfig
from api import db, create_app
from api.models import User
from api.models.film import Film
from api.models.genre import Genre

@pytest.fixture(scope="session")
def postgresql():
    with testing.postgresql.Postgresql() as postgresql:
        yield postgresql

@pytest.fixture(scope="session")
def test_app(postgresql):
    test_config = TestConfig()
    test_config.SQLALCHEMY_DATABASE_URI = postgresql.url()

    app = create_app(test_config)

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
    db.session.add(film)
    db.session.commit()

    yield film  # Provide the test film

    # Cleanup after test
    db.session.delete(film)
    db.session.commit()

@pytest.fixture
def test_genre(test_db):
    """Provides a test genre and ensures cleanup after each test."""
    genre = Genre(genre="Test Genre")
    db.session.add(genre)
    db.session.commit()
    yield genre

    db.session.delete(genre)
    db.session.commit()



@pytest.fixture
def test_user(test_db):
    """Provides a test user and ensures cleanup after each test."""
    user = User(
        username=f"TestUser_{datetime.utcnow().timestamp()}",
        profile_ref=f"test_user_{datetime.utcnow().timestamp()}",
        last_updated=datetime.utcnow().date()
    )
    db.session.add(user)
    db.session.commit()
    yield user

    try:
        db.session.delete(user)
        db.session.commit()
    except:
        db.session.rollback()



@pytest.fixture
def mock_db_session(mocker):

    session_mock = mocker.patch.object(db, "session")

    session_mock.add.side_effect = SQLAlchemyError("Mocked DB error")
    session_mock.commit.side_effect = SQLAlchemyError("Mocked DB error")
    session_mock.rollback.return_value = None
    session_mock.delete.side_effect = SQLAlchemyError("Mocked DB error")

    return session_mock


