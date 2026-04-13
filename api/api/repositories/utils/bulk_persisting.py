from abc import ABC

from sqlalchemy import exists, and_, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from api import db

class BulkPersistence(ABC):

    def __init__(self):
        self.cls_table = None
        self.conflict_columns = None
        self.update_columns = None
        self.own_filter = False
        self.fk_filter = None

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

 

    def upsert(self, data, cls_table=None, conflict_columns=None, update_columns=None,
               own_filter=None, fk_filter=None):
        if not data:
            return []

        table = cls_table if cls_table is not None else self.cls_table
        table = table.__table__ if hasattr(table, '__table__') else table
        conflict_columns = conflict_columns or self.conflict_columns
        update_columns = update_columns or self.update_columns
        own_filter = own_filter if own_filter is not None else self.own_filter
        fk_filter = fk_filter or self.fk_filter

        allowed = set(list(conflict_columns) + list(update_columns))
        rows = [{k: v for k, v in row.items() if k in allowed} for row in data]

        stmt = insert(table).values(rows)
        set_ = {col: stmt.excluded[col] for col in update_columns if any(col in row for row in rows)}

        where_clauses = []
        if own_filter:
            where_clauses.append(
                exists().where(and_(*[table.c[col] == stmt.excluded[col] for col in conflict_columns]))
            )
        if fk_filter:
            for col, (fk_table, fk_col) in fk_filter.items():
                where_clauses.append(text(f"EXISTS (SELECT 1 FROM {fk_table} WHERE {fk_col} = excluded.{col})"))

        if set_:
            stmt = stmt.on_conflict_do_update(
                index_elements=conflict_columns,
                set_=set_,
                where=and_(*where_clauses) if where_clauses else None
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns)

        try:
            db.session.execute(stmt)
            db.session.commit()
            return data
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e