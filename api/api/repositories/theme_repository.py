from .. import db
from ..models import Theme, Film_Theme
from sqlalchemy.exc import SQLAlchemyError
from ..repositories.utils.bulk_persisting import BulkPersistence


class ThemeRepository(BulkPersistence):

    def __init__(self):
        super().__init__()
        self.cls_table = Theme
        self.conflict_columns = ['theme_ref']

        self.assoc_table = Film_Theme
        self.assoc_conflicts_columns = ['film_id', 'theme_id']

    def get_all_themes(self):
        try:
            return Theme.query.all()
        except SQLAlchemyError as e:
            print(f"Database error in get_all_themes: {e}")
            return None

    def get_theme_by_id(self, theme_id):
        try:
            return Theme.query.get(theme_id)
        except SQLAlchemyError as e:
            print(f"Database error in get_theme_by_id: {e}")
            return None
