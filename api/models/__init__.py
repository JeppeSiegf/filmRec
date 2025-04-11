# api/models/__init__.py

from .credit import Credit
from .crew import Crew
# Import all models here to avoid circular dependencies
from .film import Film
from .genre import Genre
from .role import Role
from .user import User

__all__ = ['Film', 'Crew', 'Role', 'Genre', 'Credit', 'User']
