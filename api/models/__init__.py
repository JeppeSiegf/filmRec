# api/models/__init__.py
from api import db

# Import all models here to avoid circular dependencies
from .film import Film
from .crew import Crew
from .role import Role
from .genre import Genre
from .credit import Credit
from .user import User

__all__ = ['Film', 'Crew', 'Role', 'Genre', 'Credit', 'User']
