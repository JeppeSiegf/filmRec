from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from api import db
from api.models.series import Series

class SeriesRepository:

    @staticmethod
    def get_all():

        try:
            return Series.query.all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_by_ref(series_ref):
        try:
            return Series.query.filter_by(page_ref=series_ref).first()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def bulk_upsert(series_data: list[dict[str, str | list[str]]]):
        """
        Bulk upsert series using provided data.
        Each item in series_data should be a dict with keys: page_ref, name, film_refs.
        Returns a mapping from series_ref to associated film_refs.
        """
        if not series_data:
            return {}

        try:
            insert_data = [{'page_ref': d['page_ref'], 'name': d['name']} for d in series_data]

            stmt = insert(Series).values(insert_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['page_ref'],
                set_={'name': stmt.excluded.name}
            )

            db.session.execute(stmt)
            db.session.commit()

        except SQLAlchemyError as e:
            print('Error during bulk upsert for Series:', e)
            db.session.rollback()
            raise e

        # Return map of series_ref -> film_refs
        return {d['page_ref']: d['film_refs'] for d in series_data}
