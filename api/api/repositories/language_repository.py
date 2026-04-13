from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models import Language, Film_Language
from ..repositories.utils.bulk_persisting import BulkPersistence


class LanguageRepository(BulkPersistence):

    def __init__(self):

        super().__init__()
        self.cls_table = Language
        self.conflict_columns = ['language']

        self.assoc_table = Film_Language
        self.assoc_conflicts_columns = ['film_id', 'language_id']
        self.assoc_update_columns = ['is_primary']
        self.assoc_fk_filter = {
            'film_id': ('film', 'page_ref'),
        }


    def get_all_languages(self):

        try:
            return Language.query.all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    def get_by_languages_name(self, names):
        try:
            return Language.query.filter(Language.language.in_(names)).all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None


