import numpy as np
from implicit.als import AlternatingLeastSquares

from scipy.sparse import csr_matrix

from api import create_app
from api.recomendation_engine.recommendation_base import BaseRecommender
from api.services.rating_service import RatingService


class ALSRecommender(BaseRecommender):
    def __init__(self, n_components=100, n_trees=100,
                 n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42):
        super().__init__(n_components, n_trees)
        self.folder_path = "api/recommendation_engine/ALSmodel"
        self.model = AlternatingLeastSquares(
            factors=n_components,
            iterations=n_epochs,
            regularization=reg_all,
            random_state=random_state
        )

    def train(self, ratings):
        df = self.convert_ratings_to_dataframe(ratings)
        df = df[df['rating'] > 0]  # Implicit feedback

        self._set_item_mapping(df)

        # Create sparse matrix
        user_ids = df['user_id'].astype('category').cat.codes.values
        item_ids = df['film_id'].map(self.item_id_to_idx).values
        data = np.ones(len(df))  # Implicit feedback uses binary interaction (1 if interaction exists)

        user_item_matrix = csr_matrix((data, (user_ids, item_ids)),
                                      shape=(user_ids.max() + 1, len(self.item_id_to_idx)))

        self.model.fit(user_item_matrix)

        self._build_annoy_index(self.model.item_factors.astype(np.float32))

        self.save_artifacts()

    def test1(self):
        ratings = RatingService.get_all_ratings()
        print("fetched")

        recommender.train(ratings)

    def testload(self):
        similar = recommender.get_similar_items('godzilla-raids-again'
                                                , k=100)
        print(similar)


if __name__ == '__main__':

    app = create_app()
    with app.app_context():
        recommender = ALSRecommender()
        recommender.testload()