# service.py
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import repository as repo
from recommendationEngine import tables


class DataService:

    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.environ.get("DATABASE_URL", "postgres://postgres:A5BE1fROr3kXvlvfWkIPb~Wn38k.Wha0@yamanote.proxy.rlwy.net:37220/film")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)


    def get_film_metadata_df(self):
        with self.Session() as session:
            film_rows = repo.get_all_film_meta_data(session)

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
        with self.Session() as session:
            ratings = repo.get_all_ratings(session)
            # repo.get_all_ratings returns mapping rows (dict-like); adapt accordingly
            ratings_data = [{
                'id': r['id'],
                'user_id': r['user_id'],
                'film_id': r['film_id'],
                'rating': r['rating'],
                'liked': r['liked'],
            } for r in ratings]

            return pd.DataFrame(ratings_data)

    def update_embeddings(self, embeddings: list[dict]) -> int:
        with self.Session() as session:

            repo.clear_column(session, 'embedding')

            records = []
            for rec in embeddings:
                page_ref = rec.get('page_ref') or rec.get('film_id') or rec.get('id')
                vec = rec.get('embedding') or rec.get('embeddings')
                if not page_ref or vec is None:
                    continue
                if hasattr(vec, "tolist"):
                    vec = vec.tolist()
                records.append({"page_ref": page_ref, "embedding": [float(x) for x in vec]})

            if not records:
                return 0

            res = repo.update_embeddings(session, records)
            return len(res) if res else 0



if __name__ == "__main__":

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", 100)  # or None for all rows

    service = DataService()
    data = service.get_user_interaction_df()

    # page_refs_to_show = ["pulp", "pulp-fiction"]
    # filtered_films = films[films["page_ref"].isin(page_refs_to_show)]

    print(data.head)