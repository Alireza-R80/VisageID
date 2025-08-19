import os
import importlib
import numpy as np
from .crypto import encrypt

def _load_callable(path: str):
    if not path:
        return None
    try:
        mod_name, func_name = path.split(":", 1)
        mod = importlib.import_module(mod_name)
        return getattr(mod, func_name)
    except Exception:
        return None


class FaceAdapter:
    """Face recognition adapter with optional custom embed function.

    Provide env `FACE_EMBED_FUNC` as `module.sub:func` to use your own
    embedding function. The function should accept a BGR numpy array and
    return a 1D numpy array (float32 recommended).
    """

    def __init__(self):
        func_path = os.getenv("FACE_EMBED_FUNC", "")
        self._custom_embed = _load_callable(func_path)
        # Model name used to tag embeddings and filter gallery
        self.model_name = os.getenv("FACE_EMBED_MODEL_NAME", func_path or "dev-random").strip() or "dev-random"

    def embed(self, image_bgr) -> np.ndarray:
        if self._custom_embed is not None:
            vec = self._custom_embed(image_bgr)
            return np.asarray(vec)
        # Development fallback: random vector
        return np.random.rand(128)

    def embed_and_encrypt(self, image_bgr) -> bytes:
        vector = self.embed(image_bgr).astype(np.float32)
        return encrypt(vector.tobytes())

    def match(self, probe: np.ndarray, gallery: list[np.ndarray], metric: str = "cosine") -> tuple[int, float]:
        if not gallery:
            return -1, 0.0
        if metric == "cosine":
            pnorm = float(np.linalg.norm(probe))
            if not np.isfinite(pnorm) or pnorm == 0.0:
                return -1, 0.0
            sims: list[float] = []
            for g in gallery:
                gnorm = float(np.linalg.norm(g))
                if not np.isfinite(gnorm) or gnorm == 0.0:
                    sims.append(-1.0)
                    continue
                s = float(np.dot(probe, g) / (pnorm * gnorm))
                if not np.isfinite(s):
                    s = -1.0
                # clip to [-1, 1] to be safe
                s = max(-1.0, min(1.0, s))
                sims.append(s)
            if not sims:
                return -1, 0.0
            idx = int(np.argmax(sims))
            return idx, sims[idx]
        raise ValueError("Unsupported metric")
