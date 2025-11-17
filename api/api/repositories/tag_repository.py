from ..models import Tag, Film_Tag
from sqlalchemy.exc import SQLAlchemyError
from ..repositories.utils.bulk_persisting import BulkPersistence


class TagRepository(BulkPersistence):

    def __init__(self):
        super().__init__()
        self.cls_table = Tag
        self.conflict_columns = ['tag_ref']

        self.assoc_table = Film_Tag
        self.assoc_conflicts_columns = ['film_id', 'tag_id']

    def get_all_tags(self):
        try:
            return Tag.query.all()
        except SQLAlchemyError as e:
            print(f"Database error in get_all_tags: {e}")
            return None

    def get_tag_by_id(self, tag_id):
        try:
            return Tag.query.get(tag_id)
        except SQLAlchemyError as e:
            print(f"Database error in get_tag_by_id: {e}")
            return None
