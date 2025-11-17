import abc
import os
import pickle

import numpy as np
import pandas as pd
from annoy import AnnoyIndex

from api.api.services.film_rec_service import RecommendationService


class BaseRecommender(abc.ABC):
    def __init__(self, n_components=100, n_trees=100):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder_path = ''
        self.n_components = n_components
        self.n_trees = n_trees
        self.item_id_to_idx = {}
        self.idx_to_item_id = {}
        self.annoy_index = None

    def create(self):
        df = self.get_interaction_data()
        self.train(df)
        self.save_artifacts_remote()


    @abc.abstractmethod
    def train(self, df):
        pass

    @abc.abstractmethod
    def get_item_embeddings(self) -> dict:
        """
        Should return:
        {
            'film_id_1': [float, float, ...],
            'film_id_2': [float, float, ...],
            ...
        }
        """
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

    def get_interaction_data(self):

        interaction_df = RecommendationService().get_user_interaction_df()
        return interaction_df

    def get_item_meta_data(self):

        item_meta_df = RecommendationService().get_film_metadata_df()
        return item_meta_df

    def _set_item_mapping(self, df):
        item_ids = sorted(df['film_id'].unique())
        self.item_id_to_idx = {id: idx for idx, id in enumerate(item_ids)}
        self.idx_to_item_id = {v: k for k, v in self.item_id_to_idx.items()}

    def _build_annoy_index(self, item_vectors):
        self.annoy_index = AnnoyIndex(self.n_components, 'angular')
        for item_idx, vector in enumerate(item_vectors):
            self.annoy_index.add_item(item_idx, vector.astype(np.float32))
        self.annoy_index.build(self.n_trees)

    def save_artifacts_locally(self):
        if not self.folder_path:
            raise ValueError("folder_path is not set. Cannot save artifacts.")
        os.makedirs(self.folder_path, exist_ok=True)

        self.annoy_index.save(f"{self.folder_path}/item_similarity.ann")
        with open(f"{self.folder_path}/item_id_to_idx.pkl", 'wb') as f:
            pickle.dump(self.item_id_to_idx, f)

    def save_artifacts_remote(self):
        # Get embeddings from subclass
        raw_embeddings = self.get_item_embeddings()

        # Prepare for DB
        embeddings_payload = []
        for film_id, vec in raw_embeddings.items():
            if hasattr(vec, "tolist"):
                vec = vec.tolist()
            embeddings_payload.append({
                'page_ref': film_id,
                'embedding': [float(x) for x in vec]
            })

        # Send to DB
        RecommendationService().update_embeddings(embeddings_payload)

    def load_artifacts(self):
        self.annoy_index = AnnoyIndex(self.n_components, 'angular')
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
            return [(self.idx_to_item_id[idx], 1 - dist) for idx, dist in zip(idxs, distances)]
        else:
            return [self.idx_to_item_id[idx] for idx in self.annoy_index.get_nns_by_item(item_idx, k)]
