from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from api.models.credit import Credit
from api.models.role import Role
from api.models.crew import Crew
from api import db


class CrewRepository:

    @staticmethod
    def get_film_crew(film_ref: str, role_id: int = None, crew_id: int = None):
        query = Credit.query.filter_by(film_id=film_ref)

        # Apply additional filters if parameters are provided
        if role_id is not None:
            query = query.filter_by(role_id=role_id)

        if crew_id is not None:
            query = query.filter_by(crew_id=crew_id)

        return query.all()

    @staticmethod
    def get_credits_by_crew_ref(crew_ref: str) -> list[str]:
        return Credit.query.filter_by(crew_id=crew_ref).all()

    def get_crew_by_ref(crew_ref):
        return Crew.query.filter_by(page_ref=crew_ref).first()

    @staticmethod
    def get_role_ref_by_name(role_title: str):
        return Role.query.filter_by(role=role_title).first()


    @staticmethod
    def get_role_name_by_ref(role_ref: str):

        return Role.query.filter_by(id=role_ref).first()

    @staticmethod
    def get_credit(film_ref, crew_ref, role_id):
        return Credit.query.filter_by(film_id=film_ref, crew_id=crew_ref, role_id=role_id).first()

    @staticmethod
    def get_film_director(film_ref):
        return [c.name for c in Crew.query.join(Credit).join(Role).filter(
            Credit.film_id == film_ref, Role.role == "director", Credit.role_id == Role.id
        ).all()]

    @staticmethod
    def create_crew_member(crew):
        if not isinstance(crew, Crew):
            raise TypeError("Expected a Crew instance.")

        if not crew.name:
            raise ValueError("Crew must have a name.")

        db.session.add(crew)
        db.session.commit()
        return crew

    @staticmethod
    def update_film_roles(roles):
        try:

            existing_roles = {r.role: r for r in Role.query.filter(Role.role.in_(roles)).all()}
            missing_roles = [role_name for role_name in roles if role_name not in existing_roles]

            new_role_objs = []
            for role_name in missing_roles:
                new_role = Role(role=role_name)
                db.session.add(new_role)
                new_role_objs.append(new_role)

            if new_role_objs:
                db.session.flush()
                for r in new_role_objs:
                    existing_roles[r.role] = r

            result_roles = [existing_roles[role_name] for role_name in roles]

            db.session.commit()
            return result_roles

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None

    @staticmethod
    def add_film_credit(credit):
        if not isinstance(credit, Credit):
            raise TypeError("Expected a Credit instance.")

        if not credit.film_id:
            raise ValueError("Credit must have a name.")

        db.session.add(credit)
        db.session.commit()
        return credit

    @staticmethod
    def update_crew(crew):

        if not isinstance(crew, crew):
            raise TypeError("Expected a Genre instance.")

        existing_crew = Crew.query.get(crew.page_ref)

        if not existing_crew:
            return None  # Return if the genre with the given ID is not found

        existing_crew.name = crew.name

        db.session.commit()
        return existing_crew

    @staticmethod
    def delete_crew(crew_id):
        crew = Crew.query.get(crew_id)
        if crew:
            db.session.delete(crew)
            db.session.commit()


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
    def bulk_create_roles(roles_data):
        """Bulk inserts new roles, ignoring duplicates using ON CONFLICT DO NOTHING."""
        if roles_data:
            stmt = insert(Role).values(roles_data)
            # Assuming 'role' is defined as UNIQUE in Role.
            stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
            try:
                db.session.execute(stmt)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                raise e

    @staticmethod
    def bulk_create_credits(credits_data):
        """Bulk inserts new credits, ensuring no duplicates using ON CONFLICT DO NOTHING."""
        if credits_data:
            stmt = insert(Credit).values(credits_data)
            # Assuming the combination of (film_id, crew_id, role_id) is UNIQUE in Credit.
            stmt = stmt.on_conflict_do_nothing(index_elements=["film_id", "crew_id", "role_id"])
            try:
                db.session.execute(stmt)
                db.session.commit()

            except SQLAlchemyError as e:
                (print('credit'))
                db.session.rollback()
                raise e

    @staticmethod
    def get_existing_crew(crew_refs):
        """Fetches existing crew members by page_ref."""
        return Crew.query.filter(Crew.page_ref.in_(crew_refs)).all()

    @staticmethod
    def get_existing_roles(role_names):
        """Fetches existing roles by name."""
        return Role.query.filter(Role.role.in_(role_names)).all()

    @staticmethod
    def get_existing_credits(film_id, crew_ids, role_ids):
        """Fetches existing film credits to prevent duplicates."""
        return Credit.query.filter(
            Credit.film_id == film_id,
            Credit.crew_id.in_(crew_ids),
            Credit.role_id.in_(role_ids)
        ).all()
