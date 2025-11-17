import os

import numpy as np
from implicit.als import AlternatingLeastSquares
from implicit.evaluation import csr_matrix
from recomendation_engine.recommendation_base import BaseRecommender
from api.services.rating_service import RatingService


class ALSRecommender(BaseRecommender):
    def __init__(self, n_components=100, n_trees=100,
                 n_epochs=20, reg_all=0.02, random_state=42):
        super().__init__(n_components, n_trees)
        self.folder_path = os.path.join(self.base_dir, "models", "ALS")
        self.model = AlternatingLeastSquares(
            factors=n_components,
            iterations=n_epochs,
            regularization=reg_all,
            random_state=random_state
        )
        self._trained_item_factors = None  # store for get_item_embeddings()

    def train(self, df):

        df = df[~df['rating'].isna()]

        # Create a temporary mapping of item IDs
        unique_items = df['film_id'].unique()
        item_id_to_temp_idx = {item_id: idx for idx, item_id in enumerate(unique_items)}
        df['item_idx'] = df['film_id'].map(item_id_to_temp_idx)

        # Encode users
        user_ids = df['user_id'].astype('category').cat.codes.values
        item_ids = df['item_idx'].values
        data = np.ones(len(df), dtype=np.float32)

        user_item_matrix = csr_matrix(
            (data, (user_ids, item_ids)),
            shape=(user_ids.max() + 1, len(unique_items))
        )

        # Train ALS model
        self.model.fit(user_item_matrix)

        # Filter out unused items
        n_items_trained = self.model.item_factors.shape[0]
        used_item_ids = df.drop_duplicates('item_idx')
        used_item_ids = used_item_ids[used_item_ids['item_idx'] < n_items_trained]

        # Final mapping for trained items
        self.item_id_to_idx = {
            row['film_id']: row['item_idx']
            for _, row in used_item_ids.iterrows()
        }
        self.idx_to_item_id = {v: k for k, v in self.item_id_to_idx.items()}

        # Keep only the factors for items in our mapping
        self._trained_item_factors = self.model.item_factors[
            :len(self.item_id_to_idx)
        ].astype(np.float32)

        # Build ANN index
        self._build_annoy_index(self._trained_item_factors)

        # Save model artifacts + DB embeddings
        self.save_artifacts_remote()

    def get_item_embeddings(self) -> dict:

        if self._trained_item_factors is None:
            raise ValueError("Model not trained yet. Cannot get embeddings.")

        return {
            self.idx_to_item_id[idx]: vec
            for idx, vec in enumerate(self._trained_item_factors)
        }

    def test_train(self):
        ratings = RatingService().get_all_ratings()
        print("[INFO] Fetched ratings.")
        self.train(ratings)

    def test_query(self, film_id='saw', k=100):
        similar = self.get_similar_items(film_id, k, True)
        if similar:
            print(f"[INFO] Similar items to '{film_id}': {similar}")


if __name__ == '__main__':
    from api import create_app

    app = create_app()

    with app.app_context():
        recommender = ALSRecommender()
        # Uncomment to retrain:
        #recommender.test_train()
        #recommender.test_query()
        recommender.create()
