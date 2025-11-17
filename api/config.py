import os
from dotenv import load_dotenv


class Config:

    def __init__(self):

        dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
        load_dotenv(dotenv_path, override=True)

        # Get database URL - ensure it's not None
        database_url = os.environ.get("DATABASE_URL")

        if not database_url:
            raise RuntimeError("DATABASE_URL not found in .env.docker file")

        # Handle PostgreSQL URL format
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.SQLALCHEMY_DATABASE_URI = database_url
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    def __init__(self):
        # Load test environment variables with override
        load_dotenv("../.env.test", override=True)

        self.TESTING = True
        # Use test database or fall back to SQLite
        self.SQLALCHEMY_DATABASE_URI = os.getenv('testDbAddress') or 'sqlite:///test.db'
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ECHO = True
        self.CREATE_TEST_DATABASE = True