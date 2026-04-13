from .. import db
from ..models import Rating
from ..repositories.utils.bulk_persisting import BulkPersistence


class RatingRepository(BulkPersistence):
    def __init__(self):
        super().__init__()
        self.cls_table = Rating
        self.conflict_columns = ['user_id', 'film_id']
        self.update_columns = ['rating', 'liked', 'rating_date']
        self.fk_filter = {
            'user_id': ('user', 'profile_ref'),
            'film_id': ('film', 'page_ref'),
}

    def get_all_ratings(self):
        return Rating.query.all()

    def get_latest_rating_by_user(self, user_id):
        return (
            Rating.query
            .filter_by(user_id=user_id)
            .order_by(Rating.rating_date.desc())
            .first()
        )

    def get_latest_ratings_for_all_users(self):
        return (
            Rating.query
            .order_by(Rating.user_id, Rating.rating_date.desc())
            .distinct(Rating.user_id)
            .all()
        )

    @staticmethod
    def get_existing_rating_map(user_id: str, film_refs: list[str]):

        ratings = db.session.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.film_id.in_(film_refs)
        ).all()
        return {(r.film_id, r.user_id): r for r in ratings}


