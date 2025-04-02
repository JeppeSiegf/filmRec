from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import train_test_split
from surprise.model_selection import cross_validate
import pandas as pd


class RecommendationService:

    @staticmethod
    def get_surprise_recommendations(ratings_df, target_user_id, limit=10):
        """
        Generate film recommendations using scikit-surprise.

        :param ratings_df: Pandas DataFrame with columns: ['user_id', 'film_id', 'rating'].
        :param target_user_id: The user for whom to generate recommendations.
        :param limit: Number of recommendations to return.
        :return: List of recommended film_ids.
        """

        # Step 1: Load the dataset
        reader = Reader(rating_scale=(1, 5))  # Assuming the rating scale is 1-5
        data = Dataset.load_from_df(ratings_df[['user_id', 'film_id', 'rating']], reader)

        # Step 2: Split the dataset into training and test sets
        trainset, testset = train_test_split(data, test_size=0.25)

        # Step 3: Use an SVD algorithm for collaborative filtering
        algo = SVD()
        algo.fit(trainset)

        # Step 4: Predict ratings for all films the target user hasn't rated yet
        # First, get all films the user has already rated
        user_rated_films = set(ratings_df[ratings_df['user_id'] == target_user_id]['film_id'].values)

        # Get all unique films in the dataset
        all_films = set(ratings_df['film_id'].unique())

        # Create a list of films the user hasn't rated yet
        films_to_predict = all_films - user_rated_films

        # Step 5: Make predictions for each of these films
        predictions = []
        for film_id in films_to_predict:
            pred = algo.predict(target_user_id, film_id)
            predictions.append((film_id, pred.est))

        # Step 6: Sort the predictions by estimated rating
        predictions.sort(key=lambda x: x[1], reverse=True)

        # Step 7: Return the top N recommended film_ids
        recommended_film_ids = [film_id for film_id, _ in predictions[:limit]]

        return recommended_film_ids
