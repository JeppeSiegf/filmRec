from api.models import Crew, Credit, Role
from api.repositories.crew_repository import CrewRepository


class CrewService:

    def __init__(self):
        self.repo = CrewRepository()



    def get_credits_by_crew_ref(self, crew_ref):
        return self.repo.get_credits_by_crew_ref(crew_ref)

    def add_film_credits_bulk(self, credits: list[tuple[str, list[dict]]]):
        try:

            all_roles = []
            for _, crew_data in credits:
                for member in crew_data:
                    all_roles.append(member["role"])

            # Step 2: Update all roles in bulk
            self.repo.insert(all_roles, Role, self.role_conflicts)  # Ensure roles are up-to-date

            # Step 3: Prepare crew data for insertion
            all_crew_mappings = []
            all_credits_mappings = []

            for film_ref, crew_data in credits:
                crew_mappings = [
                    {
                        "page_ref": member["ref"],
                        "name": member["name"]
                    }
                    for member in crew_data
                ]
                all_crew_mappings.extend(crew_mappings)

                credits_mappings = [
                    {
                        "film_id": film_ref,
                        "crew_id": member["ref"],
                        "role_id": self.repo.get_role_ref_by_name(member["role"]).id,
                        "rank": member["rank"]
                    }
                    for member in crew_data
                ]
                all_credits_mappings.extend(credits_mappings)

            # Step 4: Bulk insert crew members
            if all_crew_mappings:
                self.repo.insert(all_crew_mappings, Crew, self.crew_conflicts)

            # Step 5: Upsert all credits in bulk
            if all_credits_mappings:
                self.repo.upsert(all_credits_mappings, Credit, self.credit_conflicts, self.credit_updates)

            print(f"Credits upserted: {len(all_credits_mappings)} created, {len(all_credits_mappings)} updated.")

        except Exception as e:
            print(f"Error during credit upsert: {e}")
            raise
