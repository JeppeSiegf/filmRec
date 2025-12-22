import random

import pandas as pd

from .. import create_app
from ..repositories.film_repository import FilmRepository
from ..repositories.rating_repository import RatingRepository
from ..services.film_service import FilmService


class RecommendationService:

    def __init__(self):
        # self.rec_engine = ALSRecommender()
        self.film_service = FilmService()
        self.film_repo = FilmRepository()
        self.rating_repo = RatingRepository()

    def get_films_recommendations(self, page_ref, top_k):

        is_in_db = self.film_service.get_film_by_page_ref(page_ref, False)
        if is_in_db is None:
            print('not in db')
            return []

        recs = self.film_repo.get_similar_films(page_ref, top_k)
        random.shuffle(recs)

        return recs

    def get_film_metadata_df(self):

        film_rows = self.film_repo.get_all_film_meta_data()

        rows = []
        for row in film_rows:
            rows.append({
                "page_ref": row["page_ref"],
                "title": row["title"],
                "release_year": row["release_year"],
                "series": row["series_id"],
                "genres": row["genres"] or [],
                "languages": row["languages"] or [],
                "crew_refs": row["crew_refs"] or [],
                "themes": row["themes"] or [],
                "tags": row["tags"] or []
            })
        return pd.DataFrame(rows)

    def get_user_interaction_df(self):

        ratings = self.rating_repo.get_all_ratings()

        ratings_data = [{
            'id': rating.id,
            'user_id': rating.user_id,
            'film_id': rating.film_id,
            'rating': rating.rating,
            'liked': rating.liked,

        } for rating in ratings]

        return pd.DataFrame(ratings_data)

    def update_embeddings(self, embeddings: list[dict]) -> int:

        self.film_repo.clear_column(column='embedding')

        records = []
        for rec in embeddings:
            page_ref = rec.get('page_ref') or rec.get('film_id') or rec.get('id')
            vec = rec.get('embedding') or rec.get('embeddings')
            if not page_ref or vec is None:
                continue
            # convert numpy arrays etc. to plain list[float]
            if hasattr(vec, "tolist"):
                vec = vec.tolist()
            records.append({"page_ref": page_ref, "embedding": [float(x) for x in vec]})

        if not records:
            return 0

        # bulk upsert via repo (bulk method you already have)
        self.film_repo.upsert(records, update_columns=['embedding'])
        return len(records)




