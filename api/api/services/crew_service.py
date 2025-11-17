from ..models import Crew, Credit, Role
from ..repositories.crew_repository import CrewRepository


class CrewService:

    def __init__(self):
        self.repo = CrewRepository()

        self.role_conflicts = ['role']
        self.crew_conflicts = ['page_ref']
        self.credit_conflicts = ['film_id', 'crew_id', 'role_id']
        self.credit_updates = ['rank']


    def get_credits_by_crew_ref(self, crew_ref):
        return self.repo.get_credits_by_crew_ref(crew_ref)

    def add_film_credits_bulk(self, credits: list[tuple[str, list[dict]]]):
        try:

            unique_roles = set()
            for _, crew_data in credits:
                for member in crew_data:
                    unique_roles.add(member["role"])

            # Step 2: Insert all roles (skip duplicates)
            role_records = [{"role": r} for r in unique_roles]
            self.repo.insert(role_records, Role, self.role_conflicts)

            # Fetch role objects to map role name -> ID
            role_objs = self.repo.get_all_roles()
            role_lookup = {r.role: r.id for r in role_objs}

            # Prepare crew data for insertion
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
                        "role_id": role_lookup.get(member["role"]),
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
