import os
import importlib
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


class LivenessChecker:
    """Liveness checker with optional custom function.

    Provide env `FACE_LIVENESS_FUNC` as `module.sub:func` to use your own
    liveness function. The function should accept a single frame (BGR numpy
    array) or a list of frames and return a truthy value for live.
    """

    def __init__(self):
        self._custom_check = _load_callable(os.getenv("FACE_LIVENESS_FUNC", ""))

    def _default_single(self, bgr: np.ndarray) -> bool:
        # Basic heuristics: reject too-dark/flat frames
        if bgr is None or not isinstance(bgr, np.ndarray) or bgr.size == 0:
            return False
        # Compute luma-like grayscale
        gray = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2]).astype(np.float32)
        mean = float(np.mean(gray))
        std = float(np.std(gray))
        # Tunable thresholds via env
        min_mean = float(os.getenv("LIVENESS_MIN_MEAN", "35"))
        min_std = float(os.getenv("LIVENESS_MIN_STD", "12"))
        return mean >= min_mean and std >= min_std

    def _default_multi(self, frames: list) -> bool:
        if not frames:
            return False
        # At least one good frame
        good = any(self._default_single(f) for f in frames if isinstance(f, np.ndarray))
        if not good:
            return False
        # And some motion between consecutive frames (mean absolute diff)
        diffs = []
        for i in range(1, len(frames)):
            a, b = frames[i - 1], frames[i]
            if not isinstance(a, np.ndarray) or not isinstance(b, np.ndarray):
                continue
            da = np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32)))
            diffs.append(float(da))
        if not diffs:
            return True
        min_motion = float(os.getenv("LIVENESS_MIN_MOTION", "2.0"))
        return max(diffs) >= min_motion

    def check(self, frame_or_frames) -> bool:
        if self._custom_check is not None:
            return bool(self._custom_check(frame_or_frames))
        if isinstance(frame_or_frames, list):
            return self._default_multi(frame_or_frames)
        return self._default_single(frame_or_frames)
