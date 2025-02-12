from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('dbAddress')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    TESTING = True
