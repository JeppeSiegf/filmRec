import abc
import os
import pickle
import numpy as np
import pandas as pd
from annoy import AnnoyIndex

os.environ['TF_USE_LEGACY_KERAS'] = '1'

import tensorflow as tf
import tensorflow_recommenders as tfrs


class BaseRecommender(abc.ABC):
    def __init__(self, n_components=64, n_trees=100):
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
            'id': r.id,
            'user_id': r.user_id,
            'film_id': r.film_id,
            'rating': r.rating,
            'liked': r.liked,
            'rating_date': r.rating_date
        } for r in ratings])

    def _set_item_mapping(self, df):
        item_ids = sorted(df['film_id'].unique())
        self.item_id_to_idx = {item_id: idx for idx, item_id in enumerate(item_ids)}
        self.idx_to_item_id = {idx: item_id for item_id, idx in self.item_id_to_idx.items()}

    def _build_annoy_index(self, item_vectors):
        self.annoy_index = AnnoyIndex(self.n_components, 'angular')
        for idx, vector in enumerate(item_vectors):
            self.annoy_index.add_item(idx, vector.astype(np.float32))
        self.annoy_index.build(self.n_trees)

    def save_artifacts(self):
        os.makedirs(self.folder_path, exist_ok=True)
        if self.annoy_index:
            self.annoy_index.save(os.path.join(self.folder_path, 'item_similarity.ann'))
        with open(os.path.join(self.folder_path, 'item_id_to_idx.pkl'), 'wb') as f:
            pickle.dump(self.item_id_to_idx, f)

    def load_artifacts(self):
        self.annoy_index = AnnoyIndex(self.n_components, 'angular')
        self.annoy_index.load(os.path.join(self.folder_path, 'item_similarity.ann'))
        with open(os.path.join(self.folder_path, 'item_id_to_idx.pkl'), 'rb') as f:
            self.item_id_to_idx = pickle.load(f)
        self.idx_to_item_id = {idx: item for item, idx in self.item_id_to_idx.items()}

    def get_similar_items(self, film_id, k=10, include_scores=False):
        if self.annoy_index is None:
            self.load_artifacts()
        idx = self.item_id_to_idx.get(film_id)
        if idx is None:
            print(f"Warning: Film ID '{film_id}' not found")
            return []
        if include_scores:
            idxs, dists = self.annoy_index.get_nns_by_item(idx, k, include_distances=True)
            sims = [max(0, 1 - d) for d in dists]
            return [(self.idx_to_item_id[i], s) for i, s in zip(idxs, sims)]
        return [self.idx_to_item_id[i] for i in self.annoy_index.get_nns_by_item(idx, k)]


class HybridCFModel(tfrs.models.Model):
    def __init__(self, user_vocab_size, item_vocab_size, genre_vocab_size,
                 director_vocab_size, lang_vocab_size, embedding_dim=64, max_genres=5, max_directors=3):
        super().__init__()

        self.embedding_dim = embedding_dim
        self.max_genres = max_genres
        self.max_directors = max_directors

        # Core embeddings
        self.user_embedding = tf.keras.layers.Embedding(user_vocab_size, embedding_dim)
        self.item_embedding = tf.keras.layers.Embedding(item_vocab_size, embedding_dim)

        # Content embeddings - all same dimension to avoid mismatches
        self.genre_embedding = tf.keras.layers.Embedding(genre_vocab_size, embedding_dim)
        self.director_embedding = tf.keras.layers.Embedding(director_vocab_size, embedding_dim)
        self.lang_embedding = tf.keras.layers.Embedding(lang_vocab_size, embedding_dim)

        # Attention layers for multi-value features
        self.genre_attention = tf.keras.layers.Dense(1, activation='softmax')
        self.director_attention = tf.keras.layers.Dense(1, activation='softmax')

        # Content fusion layer
        self.content_fusion = tf.keras.layers.Dense(embedding_dim, activation='relu')

        # Rating prediction
        self.rating_head = tf.keras.Sequential([
            tf.keras.layers.Dense(embedding_dim, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1)
        ])

        # Tasks
        self.rating_task = tf.keras.losses.MeanSquaredError()
        self.retrieval_task = tfrs.tasks.Retrieval(
            metrics=None  # Disable metrics to avoid candidate dataset issues
        )

    def _aggregate_multi_embeddings(self, embeddings, attention_layer, mask):
        """Aggregate multiple embeddings using attention mechanism"""
        # embeddings: [batch, max_items, embedding_dim]
        # mask: [batch, max_items] - 1 for valid items, 0 for padding

        # Apply attention weights
        attention_scores = attention_layer(embeddings)  # [batch, max_items, 1]
        attention_scores = tf.squeeze(attention_scores, axis=-1)  # [batch, max_items]

        # Mask out padding tokens
        mask = tf.cast(mask, tf.float32)
        attention_scores = attention_scores * mask + (1 - mask) * -1e9
        attention_weights = tf.nn.softmax(attention_scores, axis=-1)  # [batch, max_items]

        # Weighted sum
        attention_weights = tf.expand_dims(attention_weights, axis=-1)  # [batch, max_items, 1]
        aggregated = tf.reduce_sum(embeddings * attention_weights, axis=1)  # [batch, embedding_dim]

        return aggregated

    def call(self, features):
        # Get core embeddings
        user_emb = self.user_embedding(features['user_idx'])  # [batch, embedding_dim]
        item_emb = self.item_embedding(features['item_idx'])  # [batch, embedding_dim]

        # Multi-genre handling
        genre_embs = self.genre_embedding(features['genre_idx'])  # [batch, max_genres, embedding_dim]
        genre_mask = features['genre_idx'] > 0  # [batch, max_genres]
        genre_agg = self._aggregate_multi_embeddings(genre_embs, self.genre_attention, genre_mask)

        # Multi-director handling
        director_embs = self.director_embedding(features['director_idx'])  # [batch, max_directors, embedding_dim]
        director_mask = features['director_idx'] > 0  # [batch, max_directors]
        director_agg = self._aggregate_multi_embeddings(director_embs, self.director_attention, director_mask)

        # Language embedding (single value)
        lang_emb = self.lang_embedding(features['lang_idx'])  # [batch, embedding_dim]

        # Combine content features
        content_features = tf.concat([genre_agg, director_agg, lang_emb], axis=-1)
        content_emb = self.content_fusion(content_features)  # [batch, embedding_dim]

        # Enhanced item representation
        enhanced_item = item_emb + content_emb

        # Rating prediction
        combined = tf.concat([user_emb, enhanced_item], axis=-1)
        rating_pred = self.rating_head(combined)

        return {
            'user_embedding': user_emb,
            'item_embedding': enhanced_item,
            'rating_prediction': rating_pred
        }

    def compute_loss(self, features, training=False):
        outputs = self.call(features)

        # Rating loss (only for rated items)
        ratings = tf.cast(features['rating'], tf.float32)
        predictions = tf.squeeze(outputs['rating_prediction'])

        # Mask for rated items
        rated_mask = ratings > 0

        # Use tf.cond for conditional computation in graph mode
        def rating_loss_fn():
            return self.rating_task(
                y_true=tf.boolean_mask(ratings, rated_mask),
                y_pred=tf.boolean_mask(predictions, rated_mask)
            )

        def no_rating_loss_fn():
            return tf.constant(0.0)

        rating_loss = tf.cond(
            tf.reduce_any(rated_mask),
            rating_loss_fn,
            no_rating_loss_fn
        )

        # Retrieval loss
        retrieval_loss = self.retrieval_task(
            query_embeddings=outputs['user_embedding'],
            candidate_embeddings=outputs['item_embedding']
        )

        return rating_loss + retrieval_loss


class TensorFlowRecommender(BaseRecommender):
    def __init__(self, n_components=64, n_trees=100, n_epochs=10, random_state=42,
                 max_genres=5, max_directors=3):
        super().__init__(n_components, n_trees)
        self.folder_path = os.path.join(self.base_dir, 'models', 'HybridCF')
        self.n_epochs = n_epochs
        self.random_state = random_state
        self.max_genres = max_genres
        self.max_directors = max_directors
        self.model = None
        self.encoders = {}

        # Set seeds
        tf.random.set_seed(random_state)
        np.random.seed(random_state)

    def _prepare_data(self, df, metadata_df):
        """Clean and merge data with metadata"""
        # Clean ratings data
        df = df.dropna(subset=['user_id', 'film_id', 'rating']).copy()

        # Merge with metadata
        metadata_clean = metadata_df[['page_ref', 'genres', 'directors', 'primary_language_id']].copy()
        df = df.merge(metadata_clean, left_on='film_id', right_on='page_ref', how='left')

        # Clean metadata - ensure lists
        df['genres'] = df['genres'].apply(lambda x: x if isinstance(x, list) else ([x] if pd.notna(x) else ['unknown']))
        df['directors'] = df['directors'].apply(
            lambda x: x if isinstance(x, list) else ([x] if pd.notna(x) else ['unknown']))
        df['primary_language_id'] = df['primary_language_id'].fillna('unknown')

        return df

    def _create_vocab_encoders(self, df):
        """Create vocabulary encoders for all categorical features"""
        encoders = {}

        # Standard features - handle mixed types properly
        for col in ['user_id', 'film_id', 'primary_language_id']:
            # Drop NaN values and keep original types
            unique_vals = df[col].dropna().unique()
            # Sort by string representation to avoid type comparison issues
            unique_vals = sorted(unique_vals, key=str)
            encoders[col] = {val: idx for idx, val in enumerate(unique_vals)}

        # Multi-value features
        all_genres = set()
        all_directors = set()

        for genres in df['genres']:
            all_genres.update(str(g) for g in genres)

        for directors in df['directors']:
            all_directors.update(str(d) for d in directors)

        # Genre encoder (reserve 0 for padding)
        genre_vocab = ['<PAD>'] + sorted(all_genres)
        encoders['genres'] = {val: idx for idx, val in enumerate(genre_vocab)}

        # Director encoder (reserve 0 for padding)
        director_vocab = ['<PAD>'] + sorted(all_directors)
        encoders['directors'] = {val: idx for idx, val in enumerate(director_vocab)}

        return encoders

    def _encode_multi_feature(self, feature_list, encoder, max_len):
        """Encode a list of features to fixed-length padded array"""
        if not feature_list:
            return [0] * max_len

        # Convert to indices
        indices = []
        for item in feature_list[:max_len]:  # Truncate if too long
            item_str = str(item)
            if item_str in encoder:
                indices.append(encoder[item_str])
            else:
                # Unknown item, use padding
                indices.append(0)

        # Pad if too short
        while len(indices) < max_len:
            indices.append(0)

        return indices

    def _encode_features(self, df):
        """Encode categorical features to indices"""
        # Create encoders
        self.encoders = self._create_vocab_encoders(df)

        # Encode standard features - handle original data types
        df['user_idx'] = df['user_id'].map(self.encoders['user_id']).fillna(0).astype(int)
        df['film_idx'] = df['film_id'].map(self.encoders['film_id']).fillna(0).astype(int)
        df['lang_idx'] = df['primary_language_id'].map(self.encoders['primary_language_id']).fillna(0).astype(int)

        # Encode multi-value features
        df['genre_indices'] = df['genres'].apply(
            lambda x: self._encode_multi_feature(x, self.encoders['genres'], self.max_genres)
        )
        df['director_indices'] = df['directors'].apply(
            lambda x: self._encode_multi_feature(x, self.encoders['directors'], self.max_directors)
        )

        # Debug: Check max values don't exceed vocab sizes
        print(f"Max user_idx: {df['user_idx'].max()}, vocab size: {len(self.encoders['user_id'])}")
        print(f"Max film_idx: {df['film_idx'].max()}, vocab size: {len(self.encoders['film_id'])}")
        print(f"Max lang_idx: {df['lang_idx'].max()}, vocab size: {len(self.encoders['primary_language_id'])}")

        # Check genre and director indices
        all_genre_indices = [idx for sublist in df['genre_indices'] for idx in sublist]
        all_director_indices = [idx for sublist in df['director_indices'] for idx in sublist]

        print(f"Max genre_idx: {max(all_genre_indices)}, vocab size: {len(self.encoders['genres'])}")
        print(f"Max director_idx: {max(all_director_indices)}, vocab size: {len(self.encoders['directors'])}")

        return df

    def _create_dataset(self, df):
        """Create TensorFlow dataset"""
        # Convert multi-value features to arrays
        genre_array = np.vstack(df['genre_indices'].values)
        director_array = np.vstack(df['director_indices'].values)

        dataset = tf.data.Dataset.from_tensor_slices({
            'user_idx': df['user_idx'].astype(np.int32),
            'item_idx': df['film_idx'].astype(np.int32),
            'genre_idx': genre_array.astype(np.int32),
            'director_idx': director_array.astype(np.int32),
            'lang_idx': df['lang_idx'].astype(np.int32),
            'rating': df['rating'].astype(np.float32),
        })

        return dataset.shuffle(10000, seed=self.random_state).batch(512).prefetch(tf.data.AUTOTUNE)

    def train(self, ratings, metadata_df):
        """Train the model"""
        # Prepare data
        df = ratings if isinstance(ratings, pd.DataFrame) else self.convert_ratings_to_dataframe(ratings)
        df = self._prepare_data(df, metadata_df)
        df = self._encode_features(df)

        # Set item mapping for Annoy (use film_id as key, not encoded idx)
        self._set_item_mapping(df)

        # Create dataset
        dataset = self._create_dataset(df)

        # Create model
        self.model = HybridCFModel(
            user_vocab_size=len(self.encoders['user_id']),
            item_vocab_size=len(self.encoders['film_id']),
            genre_vocab_size=len(self.encoders['genres']),
            director_vocab_size=len(self.encoders['directors']),
            lang_vocab_size=len(self.encoders['primary_language_id']),
            embedding_dim=self.n_components,
            max_genres=self.max_genres,
            max_directors=self.max_directors
        )

        # Train
        self.model.compile(optimizer=tf.keras.optimizers.Adam(0.001))
        self.model.fit(dataset, epochs=self.n_epochs, verbose=1)

        # Extract item embeddings for Annoy
        item_embeddings = self.model.item_embedding.get_weights()[0]
        self._build_annoy_index(item_embeddings)

        # Save everything
        self._save_model()

    def _save_model(self):
        """Save model and encoders"""
        os.makedirs(self.folder_path, exist_ok=True)

        # Save TF model
        self.model.save_weights(os.path.join(self.folder_path, 'model_weights'))

        # Save encoders and config
        model_config = {
            'encoders': self.encoders,
            'max_genres': self.max_genres,
            'max_directors': self.max_directors,
            'n_components': self.n_components
        }
        with open(os.path.join(self.folder_path, 'model_config.pkl'), 'wb') as f:
            pickle.dump(model_config, f)

        # Save Annoy index
        self.save_artifacts()

    def load_model(self):
        """Load trained model"""
        # Load config and encoders
        with open(os.path.join(self.folder_path, 'model_config.pkl'), 'rb') as f:
            config = pickle.load(f)

        self.encoders = config['encoders']
        self.max_genres = config['max_genres']
        self.max_directors = config['max_directors']
        self.n_components = config['n_components']

        # Recreate model with correct vocab sizes
        self.model = HybridCFModel(
            user_vocab_size=len(self.encoders['user_id']),
            item_vocab_size=len(self.encoders['film_id']),
            genre_vocab_size=len(self.encoders['genres']),
            director_vocab_size=len(self.encoders['directors']),
            lang_vocab_size=len(self.encoders['primary_language_id']),
            embedding_dim=self.n_components,
            max_genres=self.max_genres,
            max_directors=self.max_directors
        )

        # Load weights
        self.model.load_weights(os.path.join(self.folder_path, 'model_weights'))

        # Load Annoy index
        self.load_artifacts()

    def test_train(self):
        """Test training with real data"""
        from api.services.rating_service import RatingService
        from api.api.services.film_service import FilmService

        print("Loading ratings...")
        ratings = RatingService().get_all_ratings()

        print("Loading films...")
        films = FilmService().get_all_films(
        )
        metadata_df = FilmService().convert_films_to_dataframe(films)

        print("Training model...")
        self.train(ratings, metadata_df)
        print("Training complete!")

    def test_query(self, film_id='pulp-fiction', k=10):
        """Test similarity queries"""
        if self.model is None:
            self.load_model()

        sims = self.get_similar_items(film_id, k, include_scores=True)
        print(f"Similar to {film_id}:")
        for item, score in sims:
            print(f"  {item}: {score:.4f}")


if __name__ == '__main__':
    from api import create_app

    app = create_app()
    with app.app_context():
        recommender = TensorFlowRecommender()
        # Uncomment to retrain:
        #recommender.test_train()
        recommender.test_query('inherent-vice')
        recommender.test_query('the-master-2012')
        recommender.test_query('pacifiction')
        recommender.test_query('nope')