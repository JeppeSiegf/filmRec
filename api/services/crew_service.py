from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from api.models import Role
from api.models.credit import Credit
from api.repositories.crew_repository import CrewRepository
from api.models.crew import Crew


class CrewService:

    @staticmethod
    def get_film_crews(film_ref):
        return CrewRepository.get_film_crew(film_ref)

    @staticmethod
    def get_credits_by_crew_ref(crew_ref):
        return CrewRepository.get_credits_by_crew_ref(crew_ref)

    @staticmethod
    def get_crew_by_ref(crew_ref):
        return CrewRepository.get_crew_by_ref(crew_ref)

    @staticmethod
    def create_crew(crew: Crew):
        if not isinstance(crew, Crew):
            raise TypeError("Expected a Crew instance.")
        return CrewRepository.create_crew_member(crew)

    @staticmethod
    def update_crew(crew: Crew):
        if not isinstance(crew, Crew):
            raise TypeError("Expected a Crew instance.")
        return CrewRepository.update_crew(crew)

    @staticmethod
    def delete_crew(crew_id):
        return CrewRepository.delete_crew(crew_id)

    @staticmethod
    def get_role_title_by_id(role_id):
        return CrewRepository.get_role_name_by_ref(role_id)

    @staticmethod
    def add_film_credit(film_ref, crew_name, crew_ref, role_name):
        try:
            # Step 1: Check if the crew member exists
            existing_crew = CrewService.get_crew_by_ref(crew_ref)

            if not existing_crew:
                new_crew = Crew(page_ref=crew_ref, name=crew_name)
                CrewRepository.create_crew_member(new_crew)

            # Step 2: Check if the role exists, create if necessary
            role = CrewRepository.get_role_ref_by_name(role_name)

            if not role:
                new_role = Role(role=role_name)
                CrewRepository.create_crew_role(new_role)
                role = new_role  # Retrieve the newly created role

            # Step 3: Check if the credit already exists
            existing_credit = CrewRepository.get_credit(film_ref, crew_ref, role.id)

            new_credit = None
            if not existing_credit:
                new_credit = Credit(
                    film_id=film_ref,
                    crew_id=crew_ref,
                    role_id=role.id
                )
                CrewRepository.add_film_credit(new_credit)

            return new_credit

        except SQLAlchemyError as e:
            print(f"Database error: {e}")

    @staticmethod
    def add_film_credits_bulk(film_ref, crew_data):
        try:
            # Extract role names as strings (not dictionaries)
            role_names = [member["role"] for member in crew_data]  # e.g., ['actor', 'director']
            CrewRepository.update_film_roles(role_names)

            # Map crew and credits data
            crew_mappings = [
                {"page_ref": member["ref"], "name": member["name"]}
                for member in crew_data
            ]

            credits_mappings = [
                {
                    "film_id": film_ref,
                    "crew_id": member["ref"],  # Use crew.ref as the ID (if needed)
                    "role_id": CrewRepository.get_role_ref_by_name(member["role"]).id  # Get role ID
                }
                for member in crew_data
            ]

            # Bulk insert crew and credits
            CrewRepository.bulk_create_crew(crew_mappings)
            CrewRepository.bulk_create_credits(credits_mappings)
            print("Inserted credits (duplicates skipped).")

        except Exception as e:
            print(f"Error: {e}")



