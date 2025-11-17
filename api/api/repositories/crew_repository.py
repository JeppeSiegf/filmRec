from ..models import Credit
from ..models import Role
from ..repositories.utils.bulk_persisting import BulkPersistence


class CrewRepository(BulkPersistence):

    def __init__(self):

        super().__init__()


    def get_credits_by_crew_ref(self, crew_ref: str) -> list[str]:
        return Credit.query.filter_by(crew_id=crew_ref).all()

    def get_role_ref_by_name(self, role_title: str):
        return Role.query.filter_by(role=role_title).first()

    def get_all_roles(self):
        return Role.query.all()


