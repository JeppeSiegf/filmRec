from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models import Genre, film_genre
from ..repositories.utils.bulk_persisting import BulkPersistence


class GenreRepository(BulkPersistence):

    def __init__(self):

        super().__init__()
        self.cls_table = Genre
        self.conflict_columns = ['genre']

        self.assoc_table = film_genre
        self.assoc_conflicts_columns = ['film_id', 'genre_id']

    def get_all_genres(self):

        try:
            return Genre.query.all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    def get_genre_by_id(genre_id):

        try:
            return Genre.query.get(genre_id)
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None


