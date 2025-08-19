import os
import importlib
from typing import Optional, Tuple
import numpy as np


def _load_callable(path: str):
    if not path:
        return None
    try:
        mod_name, func_name = path.split(":", 1)
        mod = importlib.import_module(mod_name)
        return getattr(mod, func_name)
    except Exception:
        return None


class FaceDetector:
    """Detector wrapper around a user-provided callable.

    Set env FACE_DETECT_FUNC="module.sub:func".
    Contract for func:
      - Input: BGR numpy image (H x W x 3)
      - Output any of:
          - cropped face image (numpy array HxWx3)
          - (x1, y1, x2, y2) bbox in pixels
          - (bbox, prob) where bbox is (x1, y1, x2, y2) and prob is float
          - list of the above (we'll take the best/highest prob)
    """

    def __init__(self):
        self._fn = _load_callable(os.getenv("FACE_DETECT_FUNC", ""))
        self.min_prob = float(os.getenv("FACE_DETECT_MIN_PROB", "0.85"))

    def _select_from_list(self, items):
        # Prefer items with probability, otherwise first item
        best = None
        best_p = -1.0
        for it in items:
            if isinstance(it, tuple) and len(it) == 2 and isinstance(it[0], (tuple, list)):
                bbox, prob = it
                if prob is None:
                    prob = 0.0
                if prob > best_p:
                    best = (bbox, prob)
                    best_p = prob
            elif isinstance(it, (tuple, list)) and len(it) == 4:
                if best is None:
                    best = (tuple(it), 0.0)
            elif isinstance(it, np.ndarray):
                # cropped image
                if best is None:
                    return it, 1.0
        if best is None:
            return None, 0.0
        return best

    def detect_and_crop(self, bgr: np.ndarray) -> Optional[np.ndarray]:
        if self._fn is None:
            return None
        try:
            out = self._fn(bgr)
        except Exception:
            return None
        # Normalize outputs
        if out is None:
            return None
        if isinstance(out, list):
            selected = self._select_from_list(out)
            if not selected:
                return None
            out = selected
        if isinstance(out, np.ndarray):
            return out
        if isinstance(out, tuple) and len(out) == 2 and isinstance(out[0], (tuple, list)):
            bbox, prob = out
            if prob is not None and prob < self.min_prob:
                return None
            x1, y1, x2, y2 = map(int, bbox)
            x1 = max(0, x1); y1 = max(0, y1)
            x2 = max(x1 + 1, x2); y2 = max(y1 + 1, y2)
            return bgr[y1:y2, x1:x2, :]
        if isinstance(out, (tuple, list)) and len(out) == 4:
            x1, y1, x2, y2 = map(int, out)
            x1 = max(0, x1); y1 = max(0, y1)
            x2 = max(x1 + 1, x2); y2 = max(y1 + 1, y2)
            return bgr[y1:y2, x1:x2, :]
        return None

