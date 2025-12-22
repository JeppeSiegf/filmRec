import os
from datetime import time

import numpy as np
import psutil
from lightfm import LightFM
from lightfm.data import Dataset

from api import create_app
from recomendation_engine.recommendation_base import BaseRecommender
from api.services.rating_service import RatingService


class LFMRecommender(BaseRecommender):
    def __init__(self, n_components=10, n_trees=100,
                 n_epochs=20, lr=0.05, reg=0.0, loss='warp', random_state=42):
        super().__init__(n_components, n_trees)
        self.folder_path = "models/LightFM"
        self.model = LightFM(
            no_components=n_components,
            learning_rate=lr,
            item_alpha=reg,
            loss=loss,

            random_state=random_state
        )
        self.n_epochs = n_epochs
        self.dataset = Dataset()

    def memory_usage(self):
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def train(self, df):
        # Ensure user_ids and item_ids are unique and converted to strings
        df['rating'] = df['rating'].fillna(0)
        df = df.head(100)
        user_ids = df['user_id'].astype(str).unique()
        item_ids = df['film_id'].astype(str).unique()

        # Fit LightFM Dataset to get consistent mappings
        self.dataset.fit(users=user_ids, items=item_ids)

        # Get LightFM's internal item ID -> index mapping
        _, _, self.item_id_to_idx, _ = self.dataset.mapping()

        # Build interactions matrix using the mappings from LightFM
        interactions, _ = self.dataset.build_interactions(
            zip(df['user_id'].astype(str), df['film_id'].astype(str))
        )
        print(f"Initial Memory Usage: {self.memory_usage()} MB")

        for epoch in range(self.n_epochs):
            # Train model for one epoch
            self.model.fit(interactions, epochs=1, num_threads=1, verbose=True)

            # Print memory usage after each epoch
            print(f"Memory Usage after Epoch {epoch + 1}: {self.memory_usage()} MB")
            time.sleep(1)  # Slight delay for monitoring

        print(f"Final Memory Usage: {self.memory_usage()} MB")
        # Fetch item embeddings (latent factors) for the items
        n_items = len(self.item_id_to_idx)
        latent_vectors = self.model.item_embeddings[:n_items]

        # Build Annoy index with the latent vectors (embeddings)
        self._build_annoy_index(latent_vectors.astype(np.float32))

        return latent_vectors

    def test1(self):
        ratings = RatingService.get_all_ratings()
        print("fetched")

        recommender.train(ratings)

    def testload(self):
        similar = recommender.get_similar_items('im-still-here-2024'
                                                , k=100)
        print(similar)


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        recommender = LFMRecommender()
        print("fetched")
        ratings = RatingService.get_all_ratings()
        fact = recommender.create(ratings)
