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
    def get_crew_by_ref(crew_ref):
        return Crew.query.filter_by(page_ref=crew_ref).first()

    @staticmethod
    def get_role_ref_by_name(role_title: str):
        role = Role.query.filter_by(role=role_title).first()
        return role.id

    @staticmethod
    def get_credit(film_ref, crew_ref, role_id):
        return Credit.query.filter_by(film_id=film_ref, crew_id=crew_ref, role_id=role_id).first()
    @staticmethod
    def get_film_director(film_ref):
        # Fetch the director role
        director_role = Role.query.filter_by(role="director").first()

        if not director_role:
            return None  # Return None if the 'Director' role is not found

        # Query the Credit table to filter by film_id and role_id for 'Director'
        credits = Credit.query.filter_by(film_id=film_ref, role_id=director_role.id).all()

        # Get the director IDs from the credits
        director_ids = [credit.crew_id for credit in credits]

        if not director_ids:
            return []  # Return an empty list if no directors are found

        # Query the Crew table to get director names by their IDs
        directors = Crew.query.filter(Crew.id.in_(director_ids)).all()

        # Return the director names
        return [director.name for director in directors]



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

        existing_crew = Crew.query.get(crew.id)

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
