import os

from dotenv import load_dotenv

load_dotenv()  # Only load the .env.docker if running in Docker


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    load_dotenv(".env.test", override=True)

    TESTING = True

    # Use a separate test database - fall back to SQLite if not specified
    SQLALCHEMY_DATABASE_URI = os.getenv('testDbAddress')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

    # Ensures each test starts with a clean database
    CREATE_TEST_DATABASE = True
