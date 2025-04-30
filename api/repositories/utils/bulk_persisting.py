from abc import ABC

from sqlalchemy import and_, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from api import db


class BulkPersistence(ABC):

    def __init__(self):
        # Initialize the table, conflict columns, and update columns as None or default
        self.cls_table = None
        self.conflict_columns = None
        self.update_columns = None

    def insert(self, data, cls_table=None, conflict_columns=None):

        if not data:
            print("No data provided.")
            return []

        cls_table = cls_table if cls_table is not None else self.cls_table
        conflict_columns = conflict_columns if conflict_columns is not None else self.conflict_columns

        stmt = insert(cls_table).values(data)
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns)

        try:
            db.session.execute(stmt)
            db.session.commit()
            print("Inserted records (duplicates were skipped).")
            return data
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error during bulk insert: {e}")
            return []

    def upsert(self, data, cls_table=None, conflict_columns=None, update_columns=None):

        if not data:
            print("No data provided.")
            return []

        cls_table = cls_table if cls_table is not None else self.cls_table
        table = cls_table.__table__ if hasattr(cls_table, '__table__') else cls_table

        conflict_columns = conflict_columns if conflict_columns is not None else self.conflict_columns
        update_columns = update_columns if update_columns is not None else self.update_columns

        stmt = insert(table).values(data)
        set_values = {col: stmt.excluded[col] for col in update_columns}

        conditions = [
            table.c[col].is_distinct_from(stmt.excluded[col])
            for col in update_columns
        ]

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_=set_values,
            where=or_(*conditions)
        )
        try:
            db.session.execute(stmt)
            db.session.commit()
            print(f"Upserted {len(data)} entries.")
            return data
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error during bulk upsert: {e}")
            return []

