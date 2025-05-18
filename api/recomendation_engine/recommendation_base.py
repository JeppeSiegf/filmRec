import abc
import os
import pickle

import numpy as np
import pandas as pd
from annoy import AnnoyIndex


class BaseRecommender(abc.ABC):

    def __init__(self, n_components=100, n_trees=100):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder_path = ''
        self.n_components = n_components
        self.n_trees = n_trees
        self.item_id_to_idx = {}
        self.idx_to_item_id = {}
        self.annoy_index = None

    def create(self, ratings):
        df = self.convert_ratings_to_dataframe(ratings)
        self.train(df)

    @abc.abstractmethod
    def train(self, df):
        pass

    @staticmethod
    def convert_ratings_to_dataframe(ratings):
        return pd.DataFrame([{
            'id': rating.id,
            'user_id': rating.user_id,
            'film_id': rating.film_id,
            'rating': rating.rating,
            'liked': rating.liked,
            'rating_date': rating.rating_date
        } for rating in ratings])

    def _set_item_mapping(self, df):
        item_ids = sorted(df['film_id'].unique())
        self.item_id_to_idx = {id: idx for idx, id in enumerate(item_ids)}
        self.idx_to_item_id = {v: k for k, v in self.item_id_to_idx.items()}

    def _build_annoy_index(self, item_vectors):
        self.annoy_index = AnnoyIndex(self.n_components, 'angular')
        for item_idx, vector in enumerate(item_vectors):
            self.annoy_index.add_item(item_idx, vector.astype(np.float32))
        self.annoy_index.build(self.n_trees)

    def save_artifacts(self):

        if not self.folder_path:
            raise ValueError("folder_path is not set. Cannot save artifacts.")
        os.makedirs(self.folder_path, exist_ok=True)
        self.annoy_index.save(f"{self.folder_path}/item_similarity.ann")
        with open(f"{self.folder_path}/item_id_to_idx.pkl", 'wb') as f:
            pickle.dump(self.item_id_to_idx, f)

    def load_artifacts(self):
        self.annoy_index = AnnoyIndex(self.n_components, 'angular')
        print(self.folder_path)
        self.annoy_index.load(f"{self.folder_path}/item_similarity.ann")

        with open(f"{self.folder_path}/item_id_to_idx.pkl", 'rb') as f:
            self.item_id_to_idx = pickle.load(f)
        self.idx_to_item_id = {v: k for k, v in self.item_id_to_idx.items()}

    def get_similar_items(self, film_id, k=10, include_scores=False):
        if not self.annoy_index:
            self.load_artifacts()

        item_idx = self.item_id_to_idx.get(film_id)
        if item_idx is None:
            print(f"Film ID '{film_id}' not found in item mapping.")
            return []

        if include_scores:
            idxs, distances = self.annoy_index.get_nns_by_item(item_idx, k, include_distances=True)
            return [(self.idx_to_item_id[idx], 1 - dist) for idx, dist in
                    zip(idxs, distances)]  # similarity = 1 - distance
        else:
            return [self.idx_to_item_id[idx] for idx in self.annoy_index.get_nns_by_item(item_idx, k)]
