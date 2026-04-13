from ..models import Credit, Role, Crew
from ..repositories.crew_repository import CrewRepository

class CrewService:
    def __init__(self):
        self.repo = CrewRepository()

    def get_credits_by_crew_ref(self, crew_ref):
        return self.repo.get_credits_by_crew_ref(crew_ref)

    def add_film_credits_bulk(self, credits: list[tuple[str, list[dict]]]):
        try:
            unique_roles = {member["role"] for _, crew_data in credits for member in crew_data}
            self.repo.insert([{"role": r} for r in unique_roles], Role, self.repo.role_conflicts)

            role_lookup = {r.role: r.id for r in self.repo.get_all_roles()}

            all_crew, all_credits = [], []
            for film_ref, crew_data in credits:
                all_crew.extend({"page_ref": m["ref"], "name": m["name"]} for m in crew_data)
                all_credits.extend({
                    "film_id": film_ref,
                    "crew_id": m["ref"],
                    "role_id": role_lookup.get(m["role"]),
                    "rank": m["rank"]
                } for m in crew_data)

            if all_crew:
                self.repo.insert(all_crew, Crew, self.repo.crew_conflicts)
            if all_credits:
                self.repo.upsert(all_credits, Credit, self.repo.credit_conflicts, 
                                 self.repo.credit_updates, fk_filter=self.repo.credit_fk_filter)

        except Exception as e:
            print(f"Error during credit upsert: {e}")
            raise