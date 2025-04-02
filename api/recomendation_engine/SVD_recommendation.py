import os

from sklearn.decomposition import TruncatedSVD

from api import create_app
from api.recomendation_engine.recommendation_base import BaseRecommender

import abc
import numpy as np
import pandas as pd
import pickle
from surprise import SVD as SurpriseSVD
from surprise import Dataset, Reader
from annoy import AnnoyIndex

from api.services.rating_service import RatingService


class SVDRecommender(BaseRecommender):
    def __init__(self, n_components=100, n_trees=100,
                 n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42):
        super().__init__(n_components, n_trees,)
        self.folder_path = "api/recommendation_engine/SVDmodel"
        self.reader = Reader(rating_scale=(0, 1))
        self.svd_params = {
            'n_factors': n_components,
            'n_epochs': n_epochs,
            'lr_all': lr_all,
            'reg_all': reg_all,
            'random_state': random_state
        }

    def train(self, ratings):

        df = self.convert_ratings_to_dataframe(ratings)
        df = df[df['rating'] >= 0]

        self._set_item_mapping(df)

        data = Dataset.load_from_df(
            df[['user_id', 'film_id', 'rating']],
            self.reader
        )
        trainset = data.build_full_trainset()

        svd = SurpriseSVD(**self.svd_params)
        svd.fit(trainset)

        # Create item vectors with proper alignment
        item_vectors = np.zeros((len(self.item_id_to_idx), self.n_components))
        internal_id_map = {trainset.to_raw_iid(i): i for i in range(trainset.n_items)}

        for film_id, idx in self.item_id_to_idx.items():
            if film_id in internal_id_map:
                item_vectors[idx] = svd.qi[internal_id_map[film_id]]

        self._build_annoy_index(item_vectors)
        self.save_artifacts()

    def test1(self):
        ratings = RatingService.get_all_ratings()
        print("fetched")

        recommender.train(ratings)

    def testload(self):

        similar = recommender.get_similar_items('zama'
                                                , k=10)
        print(similar)
        similar = recommender.get_similar_items('the-hunger-games-catching-fire', k=10)
        print(similar)
        similar = recommender.get_similar_items('saw', k=10)
        print(similar)
        similar = recommender.get_similar_items('the-rabbis-cat', k=10)
        print(similar)


if __name__ == '__main__':
    # Load interaction data
    app = create_app()
    with app.app_context():
        recommender = SVDRecommender()
        recommender.testload()
