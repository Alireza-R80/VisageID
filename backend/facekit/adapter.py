import numpy as np
from .crypto import encrypt

class FaceAdapter:
    """Stub face recognition adapter."""
    def __init__(self):
        pass

    def embed(self, image_bgr) -> np.ndarray:
        # For development we return a random vector
        return np.random.rand(128)

    def embed_and_encrypt(self, image_bgr) -> bytes:
        vector = self.embed(image_bgr).astype(np.float32)
        return encrypt(vector.tobytes())

    def match(self, probe: np.ndarray, gallery: list[np.ndarray], metric: str = "cosine") -> tuple[int, float]:
        if not gallery:
            return -1, 0.0
        if metric == "cosine":
            sims = [float(np.dot(probe, g) / (np.linalg.norm(probe) * np.linalg.norm(g))) for g in gallery]
            idx = int(np.argmax(sims))
            return idx, sims[idx]
        raise ValueError("Unsupported metric")
