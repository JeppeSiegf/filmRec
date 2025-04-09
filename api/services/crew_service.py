from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from api.models import Role
from api.models.credit import Credit
from api.repositories.crew_repository import CrewRepository
from api.models.crew import Crew


class CrewService:


    @staticmethod
    def get_credits_by_crew_ref(crew_ref):
        return CrewRepository.get_credits_by_crew_ref(crew_ref)

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

            if crew_mappings:
                CrewRepository.bulk_create_crew(crew_mappings)

            credits_mappings = [
                {
                    "film_id": film_ref,
                    "crew_id": member["ref"],  # Using crew.ref as the identifier
                    "role_id": CrewRepository.get_role_ref_by_name(member["role"]).id,  # Get role ID based on role name
                    "rank": member["rank"]
                }
                for member in crew_data
            ]

            # Call the helper method to upsert the credits into the database
            CrewRepository.upsert_credits(credits_mappings)

            print(f"Credits upserted: {len(crew_data)} created, {len(crew_data)} updated.")

        except Exception as e:
            print(f"Error during credit upsert: {e}")
            raise




