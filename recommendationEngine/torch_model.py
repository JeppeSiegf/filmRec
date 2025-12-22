# recommender_simple_threefactor.py
import os
import pickle
from typing import Dict, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import Dataset, DataLoader

from recommendationEngine.recommendation_base import BaseRecommender

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class TwoTower(nn.Module):
    """Standard two-tower model for collaborative filtering."""

    def __init__(self, n_users: int, n_items: int, dim: int = 128):
        super().__init__()
        self.u_emb = nn.Embedding(n_users, dim, padding_idx=0)
        self.i_emb = nn.Embedding(n_items, dim, padding_idx=0)

    def forward(self, u_idx, i_idx):
        u = self.u_emb(u_idx)
        i = self.i_emb(i_idx)
        return F.normalize(u, dim=1), F.normalize(i, dim=1)

class InteractionsDataset(Dataset):
    """Dataset for user-item interactions."""

    def __init__(self, df: pd.DataFrame):
        self.u = df['user_idx'].to_numpy(np.int64)
        self.i = df['item_idx'].to_numpy(np.int64)
        self.rating = df['rating_norm'].to_numpy(np.float32)
        self.liked = df['liked'].to_numpy(np.float32)
        self.has_rating = df['has_rating'].to_numpy(np.float32)

    def __len__(self):
        return len(self.u)

    def __getitem__(self, idx):
        return {
            'u': int(self.u[idx]),
            'i': int(self.i[idx]),
            'rating': float(self.rating[idx]),
            'liked': float(self.liked[idx]),
            'has_rating': float(self.has_rating[idx]),
        }


def collate_batch(batch):
    """Collate batch and move to device."""
    return {
        'u_idx': torch.tensor([b['u'] for b in batch], dtype=torch.long, device=DEVICE),
        'i_idx': torch.tensor([b['i'] for b in batch], dtype=torch.long, device=DEVICE),
        'rating': torch.tensor([b['rating'] for b in batch], dtype=torch.float32, device=DEVICE),
        'liked': torch.tensor([b['liked'] for b in batch], dtype=torch.float32, device=DEVICE),
        'has_rating': torch.tensor([b['has_rating'] for b in batch], dtype=torch.float32, device=DEVICE),
    }


# ====================
# Recommender
# ====================
class SimpleThreeFactorRecommender(BaseRecommender):
    """
    Two-tower collaborative filtering using three signals:
    1. Implicit interaction (user engaged with item)
    2. Explicit likes
    3. Explicit ratings
    """

    def __init__(
            self,
            embedding_dim: int = 128,
            lambda_like: float = 2.0,
            lambda_rating: float = 1.0,
            batch_size: int = 256,
            epochs: int = 5,
            lr: float = 1e-3,
            temp: float = 0.07,
    ):
        super().__init__(n_components=embedding_dim, n_trees=100)
        self.dim = embedding_dim
        self.lambda_like = lambda_like
        self.lambda_rating = lambda_rating
        self.batch_size = batch_size
        self.epochs = epochs
        self.lr = lr
        self.temp = temp

        self.model = None
        self.encoders = {}

        self.folder_path = os.path.join(self.base_dir, "models", "TTN")
        self.item_embeddings = None
        self.candidate_ids = None

    # ==================
    # Encoding
    # ==================
    def _make_encoders(self, df: pd.DataFrame):
        """Create user and item ID encoders."""
        users = sorted(df['user_id'].astype(str).unique())
        items = sorted(df['film_id'].astype(str).unique())

        self.encoders = {
            'user': {v: i + 1 for i, v in enumerate(users)},
            'item': {v: i + 1 for i, v in enumerate(items)},
        }
        self.encoders['user']['<UNK>'] = 0
        self.encoders['item']['<UNK>'] = 0

    def _encode_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode IDs and normalize signals."""
        df = df.copy()

        # Encode IDs
        df['user_idx'] = df['user_id'].astype(str).map(self.encoders['user']).fillna(0).astype(int)
        df['item_idx'] = df['film_id'].astype(str).map(self.encoders['item']).fillna(0).astype(int)

        # Normalize rating: 1-10 → 0-1
        df['rating'] = pd.to_numeric(df.get('rating', 0), errors='coerce').fillna(0)
        df['has_rating'] = (df['rating'] > 0).astype(float)
        df['rating_norm'] = df['rating'].apply(lambda x: (x - 1.0) / 9.0 if x > 0 else 0.0)

        # Binary liked
        df['liked'] = df.get('liked', 0).fillna(0).astype(float)

        # Keep only rows with some signal
        df = df[(df['liked'] > 0) | (df['rating'] > 0)].reset_index(drop=True)

        return df

    # ==================
    # Training
    # ==================
    def train(self, interactions: pd.DataFrame):
        df = interactions.dropna(subset=['user_id', 'film_id']).copy()
        self._make_encoders(df)
        df = self._encode_df(df)

        if df.empty:
            raise RuntimeError("No valid interactions")

        ds = InteractionsDataset(df)
        dl = DataLoader(
            ds,
            batch_size=self.batch_size,
            shuffle=True,
            collate_fn=collate_batch,
            num_workers=0,
        )

        n_users = max(self.encoders['user'].values()) + 1
        n_items = max(self.encoders['item'].values()) + 1
        self.model = TwoTower(n_users, n_items, dim=self.dim).to(DEVICE)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)

        for epoch in range(self.epochs):
            self.model.train()
            total_loss = 0.0

            for batch in dl:
                u_idx = batch["u_idx"]
                i_idx = batch["i_idx"]
                rating = batch["rating"]  # normalized 0–1
                liked = batch["liked"]
                has_rating = batch["has_rating"]

                u_emb, i_emb = self.model(u_idx, i_idx)

                mask = has_rating > 0
                if mask.sum() > 0:
                    pred = (u_emb[mask] * i_emb[mask]).sum(dim=1)
                    target = rating[mask]
                    loss_rating = ((pred - target) ** 2).mean()
                else:
                    loss_rating = 0.0

                batch_size = len(u_idx)
                if batch_size > 1:
                    logits = (u_emb @ i_emb.t())  # user-item dot product
                    labels = torch.arange(batch_size, device=DEVICE)
                    loss_implicit = F.cross_entropy(logits, labels)
                else:
                    loss_implicit = 0.0

                loss_implicit = loss_implicit * (1.0 + self.lambda_like * liked.mean())
                loss = loss_rating + loss_implicit

                opt.zero_grad()
                loss.backward()
                opt.step()

                total_loss += loss.item()

            print(f"Epoch {epoch + 1}/{self.epochs} — Loss: {total_loss / len(dl):.4f}")

        self._build_item_embeddings(n_items)
        self._save_model_files()

    def _build_item_embeddings(self, n_items: int):
        self.model.eval()

        all_items = torch.arange(n_items, dtype=torch.long, device=DEVICE)

        embeddings = []
        with torch.no_grad():
            for start in range(0, n_items, 1024):
                batch = all_items[start:start + 1024]
                _, i_emb = self.model(torch.zeros_like(batch), batch)
                embeddings.append(i_emb.cpu().numpy())

        self.item_embeddings = np.vstack(embeddings).astype(np.float32)

        idx2item = {v: k for k, v in self.encoders['item'].items()}

        self.item_id_to_idx = {
            idx2item[i]: i
            for i in range(n_items)
            if i in idx2item
        }

        self.idx_to_item_id = {v: k for k, v in self.item_id_to_idx.items()}

        # Build Annoy using EXACT same indices
        self._build_annoy_index(self.item_embeddings)

    def _save_model_files(self):
        """Save model weights and metadata."""
        # Create folder only if it doesn't exist
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)

        # Save model weights
        torch.save(self.model.state_dict(), os.path.join(self.folder_path, "state.pt"))

        # Save encoders
        with open(os.path.join(self.folder_path, "encoders.pkl"), "wb") as f:
            pickle.dump(self.encoders, f)

        # Save item embeddings
        np.save(os.path.join(self.folder_path, "item_embeddings.npy"), self.item_embeddings)

        # Save candidate IDs
        with open(os.path.join(self.folder_path, "candidate_ids.pkl"), "wb") as f:
            pickle.dump(self.candidate_ids, f)

        # Optional base artifacts
        try:
            self.save_artifacts_locally()
        except Exception as e:
            print(f"Warning: Could not save base artifacts: {e}")

    def load_model(self):
        """Load model state, encoders, embeddings and Annoy index from self.folder_path."""
        folder = self.folder_path
        # check required files
        required = [
            os.path.join(folder, "encoders.pkl"),
            os.path.join(folder, "state.pt"),
            os.path.join(folder, "item_embeddings.npy"),
            os.path.join(folder, "candidate_ids.pkl"),
        ]
        missing = [p for p in required if not os.path.exists(p)]
        if missing:
            raise FileNotFoundError(f"Missing model files in {folder}: {missing}")

        # load encoders
        with open(os.path.join(folder, "encoders.pkl"), "rb") as f:
            self.encoders = pickle.load(f)

        # sanity check
        if 'item' not in self.encoders:
            raise RuntimeError("Loaded encoders missing 'item' key")

        n_users = max(self.encoders['user'].values()) + 1
        n_items = max(self.encoders['item'].values()) + 1

        # recreate model and load state
        self.model = TwoTower(n_users, n_items, dim=self.dim).to(DEVICE)
        self.model.load_state_dict(torch.load(os.path.join(folder, "state.pt"), map_location=DEVICE))
        self.model.eval()

        # load embeddings and candidate ids
        self.item_embeddings = np.load(os.path.join(folder, "item_embeddings.npy"))
        with open(os.path.join(folder, "candidate_ids.pkl"), "rb") as f:
            self.candidate_ids = pickle.load(f)

        # try to load item_id_to_idx if saved; otherwise reconstruct from candidate_ids
        item_id_to_idx_path = os.path.join(folder, "item_id_to_idx.pkl")
        if os.path.exists(item_id_to_idx_path):
            with open(item_id_to_idx_path, "rb") as f:
                self.item_id_to_idx = pickle.load(f)
            self.idx_to_item_id = {v: k for k, v in self.item_id_to_idx.items()}
        else:
            # build mapping from candidate_ids (assume candidate_ids array index = annoy index)
            self.item_id_to_idx = {fid: int(idx) for idx, fid in enumerate(self.candidate_ids)}
            self.idx_to_item_id = {idx: fid for fid, idx in self.item_id_to_idx.items()}

        # load annoy/index artifacts (prints warning on failure)
        try:
            self.load_artifacts()
        except Exception as e:
            print(f"Warning: load_artifacts failed: {e}")

    # ==================
    # Inference (Required by base class)
    # ==================
    def get_item_embeddings(self, item_ids: list) -> np.ndarray:
        """Get embeddings for specific items."""
        if self.model is None:
            self.load_model()

        # Normalize IDs: strip whitespace, lowercase, replace spaces with dashes
        item_indices = [
            self.encoders['item'].get(str(iid).strip().lower().replace(' ', '-'), 0)
            for iid in item_ids
        ]

        self.model.eval()
        with torch.no_grad():
            indices_tensor = torch.tensor(item_indices, dtype=torch.long, device=DEVICE)
            _, i_emb = self.model(torch.zeros_like(indices_tensor), indices_tensor)
            return i_emb.cpu().numpy()

    def get_similar_items(self, film_id, k=10, include_scores=False):
        if self.model is None or not hasattr(self, "annoy_index"):
            self.load_model()

        # candidate_ids: np.array where index == annoy item index
        try:
            item_idx = int(np.where(self.candidate_ids == film_id)[0][0])
        except IndexError:
            print(f"Film ID '{film_id}' not found in item mapping.")
            return []

        if include_scores:
            idxs, distances = self.annoy_index.get_nns_by_item(
                item_idx, k, include_distances=True
            )
            return [
                (self.candidate_ids[idx], 1.0 - dist)
                for idx, dist in zip(idxs, distances)
            ]
        else:
            idxs = self.annoy_index.get_nns_by_item(item_idx, k)
            return [self.candidate_ids[idx] for idx in idxs]

    def test_train(self):
        """Test training on interaction data."""
        interactions = self.get_interaction_data()
        self.train(interactions)
        return True

    def test_query(self, film_id: str, k: int = 10):
        """Test getting similar items."""
        if self.model is None:
            self.load_model()
        return self.get_similar_items(film_id, k=k, include_scores=True)


# Main
# ====================
if __name__ == "__main__":
    rec = SimpleThreeFactorRecommender(
        embedding_dim=128,
        lambda_like=2.0,
        lambda_rating=1.0,
        batch_size=256,
        epochs=5,
    )

    # Load model
    rec.test_query("pulp-fiction")

    # Debug: Check if pulp-fiction exists
    print("\n=== Debugging Film IDs ===")
    print(f"Total items in encoder: {len(rec.encoders['item'])}")

    # Check exact key
    if 'pulp-fiction' in rec.encoders['item']:
        print("✓ 'pulp-fiction' found in encoders")
        idx = rec.encoders['item']['pulp-fiction']
        print(f"  Index: {idx}")
    else:
        print("✗ 'pulp-fiction' NOT found")
        # Search for similar
        pulp_matches = [k for k in rec.encoders['item'].keys() if 'pulp' in str(k).lower()]
        print(f"  Films with 'pulp': {pulp_matches[:5]}")

    # Show some sample IDs
    print("\nSample film IDs (first 10):")
    for i, film_id in enumerate(list(rec.encoders['item'].keys())[:10]):
        if film_id != '<UNK>':
            print(f"  {i + 1}. {film_id}")

    # Try query
    print("\n=== Testing Query ===")
    try:
        results = rec.test_query('stalker', k=15)
        print("Results:")
        for film_id, score in results:
            print(f"  {film_id}: {score:.4f}")
    except Exception as e:
        print(f"Error: {e}")