import os
import pickle
import numpy as np
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares

from api.recomendation_engine.recommendation_base import BaseRecommender
from api.services.rating_service import RatingService


class ALSRecommender(BaseRecommender):
    def __init__(self, n_components=100, n_trees=100,
                 n_epochs=20, reg_all=0.02, random_state=42):
        super().__init__(n_components, n_trees,)
        self.folder_path = os.path.join(self.base_dir, "models", "ALS")
        self.model = AlternatingLeastSquares(
            factors=n_components,
            iterations=n_epochs,
            regularization=reg_all,
            random_state=random_state
        )

    def train(self, ratings):
        df = self.convert_ratings_to_dataframe(ratings)
        df = df[~df['rating'].isna()]  # keep all non-NaN (including 0 and False)

        # Step 1: Create a temporary mapping of item IDs
        unique_items = df['film_id'].unique()
        item_id_to_temp_idx = {item_id: idx for idx, item_id in enumerate(unique_items)}
        df['item_idx'] = df['film_id'].map(item_id_to_temp_idx)

        # Step 2: Encode users
        user_ids = df['user_id'].astype('category').cat.codes.values
        item_ids = df['item_idx'].values
        data = np.ones(len(df), dtype=np.float32)

        user_item_matrix = csr_matrix(
            (data, (user_ids, item_ids)),
            shape=(user_ids.max() + 1, len(unique_items))
        )

        # Step 3: Train ALS
        self.model.fit(user_item_matrix)

        # Step 4: Filter out unused items (i.e., items ALS actually learned)
        n_items_trained = self.model.item_factors.shape[0]
        used_item_ids = df.drop_duplicates('item_idx')
        used_item_ids = used_item_ids[used_item_ids['item_idx'] < n_items_trained]

        self.item_id_to_idx = {
            row['film_id']: row['item_idx']
            for _, row in used_item_ids.iterrows()
        }
        self.idx_to_item_id = {v: k for k, v in self.item_id_to_idx.items()}

        # Step 5: Build Annoy only for trained items
        self._build_annoy_index(self.model.item_factors[:len(self.item_id_to_idx)].astype(np.float32))
        self.save_artifacts()

    def test_train(self):
        ratings = RatingService.get_all_ratings()
        print("[INFO] Fetched ratings.")
        self.train(ratings)

    def test_query(self, film_id='saw', k=100):
        similar = self.get_similar_items(film_id, k, True)
        if similar:
            print(f"[INFO] Similar items to '{film_id}': {similar}")





# Run this as a script for manual testing
if __name__ == '__main__':
    from api import create_app

    app = create_app()
    with app.app_context():
        recommender = ALSRecommender()
        # Uncomment to retrain:
        recommender.test_query()
        # recommender.test_query('pulp-fiction')
