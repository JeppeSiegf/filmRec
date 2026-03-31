import os
import pickle
import pandas as pd

from recomendation_engine.recommendation_base import BaseRecommender

os.environ['TF_USE_LEGACY_KERAS'] = '1'

import tensorflow as tf
import tensorflow_recommenders as tfrs
import numpy as np



class EnhancedHybridCFModel(tfrs.models.Model):
    def __init__(
            self,
            user_vocab_size,
            item_vocab_size,
            genre_vocab_size,
            director_vocab_size,
            lang_vocab_size,
            tag_vocab_size=0,
            theme_vocab_size=0,
            series_vocab_size=0,
            embedding_dim=64,
            max_genres=5,
            max_directors=3,
            max_tags=5,
            max_themes=5,
    ):
        super().__init__()

        self.embedding_dim = embedding_dim
        self.max_genres = max_genres
        self.max_directors = max_directors
        self.max_tags = max_tags
        self.max_themes = max_themes

        # CF embeddings
        self.user_embedding_cf = tf.keras.layers.Embedding(user_vocab_size, embedding_dim)
        self.item_embedding_cf = tf.keras.layers.Embedding(item_vocab_size, embedding_dim)

        # Content embeddings
        self.genre_embedding = tf.keras.layers.Embedding(genre_vocab_size, embedding_dim)
        self.director_embedding = tf.keras.layers.Embedding(director_vocab_size, embedding_dim)
        self.lang_embedding = tf.keras.layers.Embedding(lang_vocab_size, embedding_dim)
        self.tag_embedding = tf.keras.layers.Embedding(max(1, tag_vocab_size), embedding_dim)
        self.theme_embedding = tf.keras.layers.Embedding(max(1, theme_vocab_size), embedding_dim)
        self.series_embedding = tf.keras.layers.Embedding(max(1, series_vocab_size), embedding_dim)

        # Simple attention for multi-value features (using built-in)
        self.genre_attention = tf.keras.layers.MultiHeadAttention(num_heads=2, key_dim=32)
        self.director_attention = tf.keras.layers.MultiHeadAttention(num_heads=2, key_dim=32)
        self.tag_attention = tf.keras.layers.MultiHeadAttention(num_heads=2, key_dim=32)
        self.theme_attention = tf.keras.layers.MultiHeadAttention(num_heads=2, key_dim=32)

        # Year projection
        self.year_projection = tf.keras.Sequential([
            tf.keras.layers.Dense(embedding_dim, activation='relu'),
            tf.keras.layers.LayerNormalization()
        ])

        # Content fusion
        self.content_fusion = tf.keras.Sequential([
            tf.keras.layers.Dense(embedding_dim, activation='tanh'),
            tf.keras.layers.LayerNormalization()
        ])

        # Simple fusion gate
        self.fusion_gate = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])


        # Rating head
        self.rating_head = tf.keras.Sequential([
            tf.keras.layers.Dense(embedding_dim, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1)
        ])

        # Item similarity head (for item-item relationships)
        self.similarity_head = tf.keras.Sequential([
            tf.keras.layers.Dense(embedding_dim, activation='relu'),
            tf.keras.layers.Dense(embedding_dim)  # Same dim for cosine similarity
        ])

        # Tasks
        self.retrieval_task = tfrs.tasks.Retrieval(metrics=None)

    def _pool_with_attention(self, embeddings, attention_layer, mask=None):
        """Simple attention pooling using built-in MultiHeadAttention"""
        if mask is not None:
            # Convert to attention mask format
            attention_mask = tf.cast(mask, tf.float32)[:, tf.newaxis, tf.newaxis, :]
        else:
            attention_mask = None

        # Self-attention then average pool
        attended = attention_layer(embeddings, embeddings, attention_mask=attention_mask)

        if mask is not None:
            mask_expanded = tf.expand_dims(tf.cast(mask, tf.float32), -1)
            attended = attended * mask_expanded
            pooled = tf.reduce_sum(attended, axis=1) / (tf.reduce_sum(mask_expanded, axis=1) + 1e-8)
        else:
            pooled = tf.reduce_mean(attended, axis=1)

        return pooled

    def _get_content_representation(self, features):
        # Multi-value embeddings
        genre_embs = self.genre_embedding(features['genre_idx'])
        director_embs = self.director_embedding(features['director_idx'])
        tag_embs = self.tag_embedding(features.get('tag_idx', tf.zeros_like(features['genre_idx'])))
        theme_embs = self.theme_embedding(features.get('theme_idx', tf.zeros_like(features['genre_idx'])))

        # Single-value embeddings
        lang_emb = self.lang_embedding(features['lang_idx'])
        series_emb = self.series_embedding(features.get('series_idx', tf.zeros_like(features['lang_idx'])))

        # Masks
        genre_mask = features['genre_idx'] > 0
        director_mask = features['director_idx'] > 0
        tag_mask = features.get('tag_idx', tf.zeros_like(features['genre_idx'])) > 0
        theme_mask = features.get('theme_idx', tf.zeros_like(features['genre_idx'])) > 0

        # Pool multi-value features with attention
        genre_agg = self._pool_with_attention(genre_embs, self.genre_attention, genre_mask)
        director_agg = self._pool_with_attention(director_embs, self.director_attention, director_mask)
        tag_agg = self._pool_with_attention(tag_embs, self.tag_attention, tag_mask)
        theme_agg = self._pool_with_attention(theme_embs, self.theme_attention, theme_mask)

        # Year projection
        year_norm = tf.expand_dims(
            features.get('year_norm', tf.zeros_like(tf.cast(features['user_idx'], tf.float32))),
            axis=-1
        )
        year_proj = self.year_projection(year_norm)

        # Combine all content features
        content_concat = tf.concat([
            genre_agg, director_agg, tag_agg, theme_agg,
            lang_emb, series_emb, year_proj
        ], axis=-1)

        content_representation = self.content_fusion(content_concat)
        return content_representation

    def _compute_diversity_penalty(self, item_features, item_embeddings):
        """Simple penalty for items with same director/series"""
        batch_size = tf.shape(item_features['item_idx'])[0]

        # Graph-safe conditional
        return tf.cond(
            tf.less_equal(batch_size, 1),
            lambda: tf.constant(0.0, dtype=tf.float32),  # Return 0 if batch too small
            lambda: self._compute_penalty_logic(item_features, item_embeddings)  # Compute penalty
        )

    def _compute_penalty_logic(self, item_features, item_embeddings):
        """The actual penalty computation logic"""
        current_directors = item_features['director_idx'][:-1]
        next_directors = item_features['director_idx'][1:]

        # Check if any director matches
        current_expanded = tf.expand_dims(current_directors, axis=2)
        next_expanded = tf.expand_dims(next_directors, axis=1)

        director_matches = tf.reduce_sum(
            tf.cast(tf.equal(current_expanded, next_expanded) & (current_expanded > 0), tf.float32),
            axis=[1, 2]
        )

        # Same for series
        current_series = item_features.get('series_idx', tf.zeros_like(item_features['lang_idx']))[:-1]
        next_series = item_features.get('series_idx', tf.zeros_like(item_features['lang_idx']))[1:]
        series_matches = tf.cast(tf.equal(current_series, next_series) & (current_series > 0), tf.float32)

        # Penalty calculation
        current_embs = item_embeddings[:-1]
        next_embs = item_embeddings[1:]

        current_norm = tf.nn.l2_normalize(current_embs, axis=1)
        next_norm = tf.nn.l2_normalize(next_embs, axis=1)
        similarities = tf.reduce_sum(current_norm * next_norm, axis=1)

        penalty_mask = (director_matches > 0) | (series_matches > 0)
        penalties = tf.where(penalty_mask, similarities, 0.0)

        return tf.reduce_mean(penalties)

    def _compute_contrastive_loss(self, features, item_embeddings):
        """Lightweight contrastive loss for item-item similarity."""
        batch_size = tf.shape(item_embeddings)[0]

        return tf.cond(
            tf.less_equal(batch_size, 1),
            lambda: tf.constant(0.0, dtype=tf.float32),
            lambda: self._compute_contrastive_logic(features, item_embeddings)
        )

    def _compute_contrastive_logic(self, features, item_embeddings):
        """The actual contrastive loss computation logic"""
        # Normalize embeddings
        norm_emb = tf.nn.l2_normalize(item_embeddings, axis=1)
        sim_matrix = tf.matmul(norm_emb, norm_emb, transpose_b=True)  # (batch, batch)

        # Compute positive/negative masks
        genres = features['genre_idx']
        directors = features['director_idx']
        series = features.get('series_idx', tf.zeros_like(features['lang_idx']))

        # Positive: share at least one genre, but different director/series
        genre_overlap = tf.reduce_sum(
            tf.cast(tf.equal(tf.expand_dims(genres, 1), tf.expand_dims(genres, 0)), tf.float32),
            axis=2
        )
        director_overlap = tf.reduce_sum(
            tf.cast(tf.equal(tf.expand_dims(directors, 1), tf.expand_dims(directors, 0)), tf.float32),
            axis=2
        )
        same_series = tf.cast(tf.equal(tf.expand_dims(series, 1), tf.expand_dims(series, 0)), tf.float32)
        positive_mask = (genre_overlap > 0) & (director_overlap == 0) & (same_series == 0)

        # Negative: same director or same series
        negative_mask = (director_overlap > 0) | (same_series > 0)

        # Compute contrastive losses
        positive_loss = tf.reduce_mean(tf.where(positive_mask, 1.0 - sim_matrix, 0.0))
        negative_loss = tf.reduce_mean(tf.where(negative_mask, tf.nn.relu(sim_matrix - 0.2), 0.0))

        return positive_loss + negative_loss

    def call(self, features, training=False):
        user_emb_cf = self.user_embedding_cf(features['user_idx'])
        item_emb_cf = self.item_embedding_cf(features['item_idx'])

        content_repr = self._get_content_representation(features)

        # Simple fusion
        gate_input = tf.concat([item_emb_cf, content_repr], axis=-1)
        gate_weight = self.fusion_gate(gate_input)
        fused_item_emb = gate_weight * item_emb_cf + (1.0 - gate_weight) * content_repr

        # Enhanced item embedding for similarity
        similarity_emb = self.similarity_head(fused_item_emb)

        # Rating prediction
        combined = tf.concat([user_emb_cf, fused_item_emb], axis=-1)
        rating_pred = self.rating_head(combined)

        return {
            'user_embedding': user_emb_cf,
            'item_embedding': fused_item_emb,
            'item_embedding_cf': item_emb_cf,
            'content_representation': content_repr,
            'rating_prediction': rating_pred,
            'similarity_embedding': similarity_emb
        }

    def compute_loss(self, features, training=False):
        outputs = self.call(features, training=training)
        item_emb = outputs['similarity_embedding']

        # Rating loss
        ratings = tf.cast(features['rating'], tf.float32)
        predictions = tf.squeeze(outputs['rating_prediction'], -1)
        rated_mask = tf.cast(ratings > 0, tf.float32)
        errors = tf.square(predictions - ratings) * rated_mask
        denom = tf.reduce_sum(rated_mask)
        rating_loss = tf.cond(
            tf.greater(denom, 0.0),
            lambda: tf.reduce_sum(errors) / denom,
            lambda: tf.constant(0.0, dtype=tf.float32)
        )

        # Retrieval loss
        retrieval_loss = self.retrieval_task(
            query_embeddings=outputs['user_embedding'],
            candidate_embeddings=outputs['item_embedding']
        )

        # Diversity penalty
        diversity_penalty = tf.constant(0.0, dtype=tf.float32)
        if training:
            diversity_penalty = self._compute_diversity_penalty(features, item_emb)

        # Contrastive loss (lightweight)
        contrastive_loss = tf.constant(0.0, dtype=tf.float32)
        if training:
            contrastive_loss = self._compute_contrastive_loss(features, item_emb)

        # Combine losses
        total_loss = (
                1.0 * rating_loss +
                0.5 * retrieval_loss +
                0.2 * diversity_penalty +
                0.3 * contrastive_loss
        )
        return total_loss





# Model factory


class TFRSRecommender(BaseRecommender):
    def get_item_embeddings(self) -> dict:
        pass

    def __init__(self, n_components=64, n_trees=100, n_epochs=10, random_state=42,
                 max_genres=5, max_directors=3, max_tags=None, max_themes=None):
        super().__init__(n_components, n_trees)
        self.folder_path = os.path.join(self.base_dir, 'models', 'MetadataEnhanced')
        self.n_epochs = n_epochs
        self.random_state = random_state
        self.max_genres = max_genres
        self.max_directors = max_directors
        self.max_tags = max_tags or max_genres
        self.max_themes = max_themes or max_genres
        self.model = None
        self.encoders = {}
        # Stats for numeric features
        self.year_mean = 0.0
        self.year_std = 1.0

        tf.random.set_seed(random_state)
        np.random.seed(random_state)

    def _prepare_data(self, df, metadata_df):
        """Clean and merge data with metadata and ensure list-typed columns."""
        df = df.dropna(subset=['user_id', 'film_id']).copy()

        # Merge with metadata (ensure required cols exist on metadata_df)
        metadata_clean = metadata_df[['page_ref','release_year', 'genres', 'crew_refs', 'languages',
                                      'tags', 'themes', 'series']].copy()
        df = df.merge(metadata_clean, left_on='film_id', right_on='page_ref', how='left')

        # Ensure list types for multi-value fields (genres, tags, themes, directors)
        def ensure_list(x):
            if isinstance(x, list):
                return x
            if pd.isna(x):
                return []
            # if it's a single string value, wrap into list
            return [x]

        df['genres'] = df['genres'].apply(ensure_list)
        df['tags'] = df['tags'].apply(ensure_list)
        df['themes'] = df['themes'].apply(ensure_list)
        df['directors'] = df['crew_refs'].apply(ensure_list)

        # languages is a list but contains only one element — convert to single attribute
        df["primary_language_id"] = df["languages"].apply(
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else ("unknown" if pd.isna(x) else x)
        )

        # release_year: fill missing with median or -1
        df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
        df['release_year'] = df['release_year'].fillna(df['release_year'].median())

        # series_id: keep as is (may be None); convert to str for encoding later
        df['series_id'] = df['series'].fillna('')  # empty string indicates no series

        return df

    def _create_vocab_encoders(self, df):
        """Create vocabulary encoders using explode for multi-value fields."""
        encoders = {}

        # Standard single-value categorical features
        for col in ['user_id', 'film_id', 'primary_language_id', 'series_id']:
            unique_vals = sorted(df[col].astype(str).fillna('').unique())
            encoders[col] = {'<UNK>': 0}
            encoders[col].update({val: idx + 1 for idx, val in enumerate(unique_vals)})

        # Multi-value features: genres, directors, tags, themes
        # use explode for speed
        def explode_unique(series):
            return sorted(pd.Series(series.explode().dropna().astype(str)).unique())

        all_genres = explode_unique(df['genres'])
        all_directors = explode_unique(df['directors'])
        all_tags = explode_unique(df['tags'])
        all_themes = explode_unique(df['themes'])

        encoders['genres'] = {val: idx for idx, val in enumerate(['<PAD>'] + all_genres)}
        encoders['directors'] = {val: idx for idx, val in enumerate(['<PAD>'] + all_directors)}
        encoders['tags'] = {val: idx for idx, val in enumerate(['<PAD>'] + all_tags)}
        encoders['themes'] = {val: idx for idx, val in enumerate(['<PAD>'] + all_themes)}

        # store back
        self.encoders = encoders
        return encoders

    def _encode_multi_feature(self, feature_list, encoder, max_len):
        """Encode list features to fixed-length arrays (pad with 0)."""
        if not feature_list:
            return [0] * max_len

        indices = []
        for item in feature_list[:max_len]:
            if item is None:
                indices.append(0)
            else:
                indices.append(encoder.get(str(item), 0))
        while len(indices) < max_len:
            indices.append(0)
        return indices

    def _encode_features(self, df):
        """Encode all features; also compute year normalization params."""
        self.encoders = self._create_vocab_encoders(df)

        # Standard encoding helper for categorical->int
        def safe_encode(series, encoder):
            return series.astype(str).apply(lambda x: encoder.get(x, 0)).astype(int)

        df['user_idx'] = safe_encode(df['user_id'], self.encoders['user_id'])
        df['film_idx'] = safe_encode(df['film_id'], self.encoders['film_id'])
        df['lang_idx'] = safe_encode(df['primary_language_id'], self.encoders['primary_language_id'])
        df['series_idx'] = safe_encode(df['series_id'].astype(str), self.encoders['series_id'])

        # Numeric release_year: normalize to mean/std
        self.year_mean = float(df['release_year'].mean())
        self.year_std = float(df['release_year'].std()) if df['release_year'].std() > 0 else 1.0
        df['year_norm'] = ((df['release_year'] - self.year_mean) / self.year_std).astype(np.float32)

        # Multi-value features -> fixed-length indices
        df['genre_indices'] = df['genres'].apply(
            lambda x: self._encode_multi_feature(x, self.encoders['genres'], self.max_genres)
        )
        df['director_indices'] = df['directors'].apply(
            lambda x: self._encode_multi_feature(x, self.encoders['directors'], self.max_directors)
        )
        df['tag_indices'] = df['tags'].apply(
            lambda x: self._encode_multi_feature(x, self.encoders['tags'], self.max_tags)
        )
        df['theme_indices'] = df['themes'].apply(
            lambda x: self._encode_multi_feature(x, self.encoders['themes'], self.max_themes)
        )

        return df

    def _create_dataset(self, df, batch_size=512):
        """Create TensorFlow dataset from encoded dataframe."""
        genre_array = np.vstack(df['genre_indices'].values).astype(np.int32)
        director_array = np.vstack(df['director_indices'].values).astype(np.int32)
        tag_array = np.vstack(df['tag_indices'].values).astype(np.int32)
        theme_array = np.vstack(df['theme_indices'].values).astype(np.int32)

        ds = tf.data.Dataset.from_tensor_slices({
            'user_idx': df['user_idx'].astype(np.int32),
            'item_idx': df['film_idx'].astype(np.int32),
            'genre_idx': genre_array,
            'director_idx': director_array,
            'tag_idx': tag_array,
            'theme_idx': theme_array,
            'lang_idx': df['lang_idx'].astype(np.int32),
            'series_idx': df['series_idx'].astype(np.int32),
            'year_norm': df['year_norm'].astype(np.float32),
            'rating': df['rating'].astype(np.float32),
        })

        return ds.shuffle(10000, seed=self.random_state).batch(batch_size).prefetch(tf.data.AUTOTUNE)

    def train(self, ratings, metadata_df):
        """Train the model"""
        print("Preparing data...")
        df = ratings if isinstance(ratings, pd.DataFrame) else self.convert_ratings_to_dataframe(ratings)
        df = self._prepare_data(df, metadata_df)
        df = self._encode_features(df)

        # --- Ensure item_id <-> idx mapping matches encoders (fix for consistency with Annoy) ---
        # encoders['film_id'] maps film_id -> idx (0 is <UNK>)
        self.item_id_to_idx = {film_id: idx for film_id, idx in self.encoders['film_id'].items()}
        self.idx_to_item_id = {idx: film_id for film_id, idx in self.encoders['film_id'].items()}

        # Create dataset
        dataset = self._create_dataset(df)

        print("Creating model...")
        # Create model
        self.model = EnhancedHybridCFModel(
            user_vocab_size=len(self.encoders['user_id']),
            item_vocab_size=len(self.encoders['film_id']),
            genre_vocab_size=len(self.encoders['genres']),
            director_vocab_size=len(self.encoders['directors']),
            lang_vocab_size=len(self.encoders['primary_language_id']),
            tag_vocab_size=len(self.encoders.get('tags', {})),
            theme_vocab_size=len(self.encoders.get('themes', {})),
            series_vocab_size=len(self.encoders.get('series_id', {})),
            embedding_dim=self.n_components,
            max_genres=self.max_genres,
            max_directors=self.max_directors,
            max_tags=self.max_tags,
            max_themes=self.max_themes,
        )

        # Train
        print("Training...")
        self.model.compile(optimizer=tf.keras.optimizers.Adam(0.001))
        self.model.fit(dataset, epochs=self.n_epochs, verbose=1)

        # --- AFTER training: build candidate embeddings for FactorizedTopK and Annoy ---
        print("Building similarity index and retrieval candidates...")
        all_item_indices = np.arange(len(self.encoders['film_id']))

        # Build a mapping of item metadata from training dataframe (pick first occurrence)
        item_metadata = {}
        for _, row in df.iterrows():
            film_idx = int(row['film_idx'])
            if film_idx not in item_metadata:
                item_metadata[film_idx] = {
                    'genre_idx': row['genre_indices'],
                    'director_idx': row['director_indices'],
                    'lang_idx': int(row['lang_idx'])
                }

        # Compute embeddings for all items (in batches) using the trained model
        batch_size = 1000
        all_embeddings = []
        valid_indices = []

        for start_idx in range(0, len(all_item_indices), batch_size):
            end_idx = min(start_idx + batch_size, len(all_item_indices))
            batch_indices = all_item_indices[start_idx:end_idx]

            batch_genres = []
            batch_directors = []
            batch_langs = []

            for idx in batch_indices:
                if idx in item_metadata:
                    batch_genres.append(item_metadata[idx]['genre_idx'])
                    batch_directors.append(item_metadata[idx]['director_idx'])
                    batch_langs.append(item_metadata[idx]['lang_idx'])
                else:
                    # Fallback for items without metadata
                    batch_genres.append([0] * self.max_genres)
                    batch_directors.append([0] * self.max_directors)
                    batch_langs.append(0)

            batch_features = {
                'user_idx': tf.zeros([len(batch_indices)], dtype=tf.int32),
                'item_idx': tf.constant(batch_indices, dtype=tf.int32),
                'genre_idx': tf.constant(batch_genres, dtype=tf.int32),
                'director_idx': tf.constant(batch_directors, dtype=tf.int32),
                'lang_idx': tf.constant(batch_langs, dtype=tf.int32),
                'rating': tf.zeros([len(batch_indices)], dtype=tf.float32)
            }

            outputs = self.model(batch_features, training=False)
            emb = outputs['item_embedding'].numpy()
            all_embeddings.append(emb)
            valid_indices.extend(batch_indices.tolist())

        # Combine embeddings: shape (num_items, dim)
        if len(all_embeddings) == 0:
            raise RuntimeError("No item embeddings were produced - check metadata/encoders.")
        item_embeddings = np.vstack(all_embeddings)

        # Build candidate ids corresponding to the order of item_embeddings
        # Use film_id strings via inverse of encoders
        idx_to_film = {idx: film for film, idx in self.encoders['film_id'].items()}
        candidate_ids = np.array([idx_to_film.get(i, '<UNK>') for i in range(item_embeddings.shape[0])], dtype=object)

        # Create candidates dataset for FactorizedTopK
        candidates_ds = tf.data.Dataset.from_tensor_slices((candidate_ids, item_embeddings.astype(np.float32))).batch(1024)

        # Attach FactorizedTopK metric to the model's retrieval task (for evaluation)
        factorized = tfrs.metrics.FactorizedTopK(candidates=candidates_ds)
        self.model.retrieval_task = tfrs.tasks.Retrieval(metrics=factorized)

        # Build Annoy index using the same item_embeddings (ensure order matches self.item_id_to_idx)
        # We earlier set self.item_id_to_idx from encoders, and candidate_ids are ordered by idx, so it's consistent.
        self._build_annoy_index(item_embeddings)

        # Saven
        self._save_model()
        print("Training completed!")

    def _save_model(self):
        """Save model"""
        os.makedirs(self.folder_path, exist_ok=True)

        # Save weights
        self.model.save_weights(os.path.join(self.folder_path, 'model_weights'))

        # Save config
        config = {
            'encoders': self.encoders,
            'max_genres': self.max_genres,
            'max_directors': self.max_directors,
            'n_components': self.n_components
        }
        with open(os.path.join(self.folder_path, 'model_config.pkl'), 'wb') as f:
            pickle.dump(config, f)

        # Save Annoy
        self.save_artifacts_locally()

    def load_model(self):
        """Load model"""
        # Load config
        with open(os.path.join(self.folder_path, 'model_config.pkl'), 'rb') as f:
            config = pickle.load(f)

        self.encoders = config['encoders']
        self.max_genres = config['max_genres']
        self.max_directors = config['max_directors']
        self.n_components = config['n_components']

        # Recreate model
        self.model = EnhancedHybridCFModel(
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

        # Load Annoy
        self.load_artifacts()

    def test_train(self):

        interactions_df = self.get_interaction_data()
        metadata_df = self.get_item_meta_data()

        self.train(interactions_df, metadata_df)

    def test_query(self, film_id='pulp-fiction', k=10):
        """Test similarity queries"""
        if self.model is None:
            self.load_model()

        sims = self.get_similar_items(film_id, k, include_scores=True)
        print(f"Similar to {film_id}:")
        for item, score in sims:
            print(f"  {item}: {score:.4f}")
        return sims




if __name__ == '__main__':
    from api import create_app

    app = create_app()
    with app.app_context():
        recommender = TFRSRecommender(n_epochs=10)

        # Train or load
        choice = input("Train new model? (y/n): ").lower().strip()
        if choice == 'y':
            recommender.test_train()
        else:
            try:
                recommender.load_model()
            except:
                print("No saved model found, training new one...")
                recommender.test_train()

        # Test both item similarity and user recommendations
        test_films = ['pulp-fiction', 'the-godfather', 'blade-runner-2049']
        for film in test_films:
            print(f"\n--- {film} ---")
            recommender.test_query(film, k=10)




        # Interactive testing
        while True:
            print("\nOptions:")
            print("1. Test item similarity")

            print("3. Quit")

            choice = input("Choice: ").strip()
            if choice == '1':
                film_id = input("Enter film ID: ").strip()
                if film_id:
                    recommender.test_query(film_id, k=10)
            elif choice == '3':
                break
            else:
                print("Invalid choice")
