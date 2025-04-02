from sklearn.preprocessing import LabelEncoder
import numpy as np

class MetadataProcessor:
    def __init__(self):
        self.director_encoder = LabelEncoder()
        self.director_embeddings = None

    def fit(self, directors):
        self.director_encoder.fit(directors)
        # Randomly initialize director embeddings
        self.director_embeddings = np.random.randn(len(directors), 10)  # 10D embedding

    def transform_directors(self, director_list):
        director_indices = self.director_encoder.transform(director_list)
        return self.director_embeddings[director_indices]

    def transform_genres(self, genre_list, unique_genres):
        genre_vector = np.zeros(len(unique_genres))
        for genre in genre_list:
            if genre in unique_genres:
                genre_vector[unique_genres.index(genre)] = 1
        return genre_vector
