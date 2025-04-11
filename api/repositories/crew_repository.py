from api.models.credit import Credit
from api.models.role import Role
from api.repositories.utils.bulk_persisting import BulkPersistence


class CrewRepository(BulkPersistence):

    def __init__(self):

        super().__init__()
        self.role_conflicts = ['role']

        self.crew_conflicts = ['page_ref']

        self.credit_conflicts = ['film_id', 'crew_id', 'role_id']
        self.credit_updates = ['rank']

    def get_credits_by_crew_ref(self, crew_ref: str) -> list[str]:
        return Credit.query.filter_by(crew_id=crew_ref).all()

    def get_role_ref_by_name(self, role_title: str):
        return Role.query.filter_by(role=role_title).first()


