from api.models.credit import Credit
from api.repositories.crew_repository import CrewRepository
from api.models.crew import Crew

class CrewService:

    @staticmethod
    def get_film_crews(film_ref):
        return CrewRepository.get_film_crew(film_ref)

    @staticmethod
    def get_film_director(film_ref):

        directors = []

        director_ref = CrewRepository.get_role_ref_by_name('director')
        credit = CrewRepository.get_film_crew(film_ref, director_ref)

        director_refs = [credit.crew_id for credit in credit]
        if director_refs:
            for ref in director_refs:
                director = CrewRepository.get_crew_by_ref(ref)
                directors.append(director.name)
        else:
            return []

        return  directors


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
    def add_director_credit(film_ref, director_name, director_ref):        # Step 1: Check if the director exists
        existing_director = CrewService.get_crew_by_ref(director_ref)

        # If the director does not exist, add them
        if not existing_director:

            new_crew = Crew(page_ref=director_ref, name=director_name)
            CrewRepository.create_crew_member(new_crew)

        # Get the role ID for 'Director'
        director_role = CrewRepository.get_role_ref_by_name("director")

        if not director_role:
            raise ValueError("Role 'Director' not found")

        existing_credit = CrewRepository.get_credit(film_ref,director_ref,director_role)

        # If the credit does not exist, add it
        if not existing_credit:
            new_credit = Credit(
                film_id=film_ref,
                crew_id=director_ref,
                role_id=director_role
            )
            CrewRepository.add_film_credit(new_credit)
