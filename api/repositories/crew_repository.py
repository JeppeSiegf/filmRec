from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from api.models.credit import Credit
from api.models.role import Role
from api.models.crew import Crew
from api import db


class CrewRepository:



    @staticmethod
    def get_credits_by_crew_ref(crew_ref: str) -> list[str]:
        return Credit.query.filter_by(crew_id=crew_ref).all()


    @staticmethod
    def get_role_ref_by_name(role_title: str):
        return Role.query.filter_by(role=role_title).first()

    @staticmethod
    def bulk_create_crew(crew_data):
        """Bulk inserts new crew members, ignoring duplicates using ON CONFLICT DO NOTHING."""
        if crew_data:
            stmt = insert(Crew).values(crew_data)
            # Assuming 'page_ref' is defined as UNIQUE in Crew.
            stmt = stmt.on_conflict_do_nothing(index_elements=['page_ref'])
            try:
                db.session.execute(stmt)
                db.session.commit()
            except SQLAlchemyError as e:
                (print('crew'))
                db.session.rollback()
                raise e


    @staticmethod
    def update_film_roles(roles: list[str]):

        if not roles:
            return []

        try:
            # Insert all roles, skipping existing ones
            stmt = insert(Role).values([{'role': r} for r in roles])
            stmt = stmt.on_conflict_do_nothing(index_elements=['role'])
            db.session.execute(stmt)
            db.session.flush()

            # Fetch and return roles in input order
            role_map = {r.role: r for r in Role.query.filter(Role.role.in_(roles)).all()}
            return [role_map[r] for r in roles if r in role_map]

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None


    @staticmethod
    def upsert_credits(credits_mappings: list[dict]):

        stmt = insert(Credit).values(credits_mappings)
        stmt = stmt.on_conflict_do_update(
            index_elements=['film_id', 'crew_id', 'role_id'],  # Unique constraint keys
            set_={'rank': stmt.excluded.rank}  # Update rank if there's a conflict
        )
        db.session.execute(stmt)
        db.session.commit()



