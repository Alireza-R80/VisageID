import numpy as np


def simple_embed(image_bgr: np.ndarray) -> np.ndarray:
    """Deterministic 128-dim embedding based on mean color.

    Computes mean over H,W for each B,G,R channel and tiles to 128 dims.
    Scales to [0,1] float32 for stable cosine comparisons.
    """
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("expected BGR image")
    mean_bgr = image_bgr.mean(axis=(0, 1)).astype(np.float32) / 255.0
    # Tile to 128 dims
    vec = np.tile(mean_bgr, int(np.ceil(128 / 3)))[:128]
    return vec.astype(np.float32)


def robust_embed(image_bgr: np.ndarray) -> np.ndarray:
    """Lightweight, ML-free embedding using HOG-like gradients.

    - Converts to grayscale (from BGR)
    - Resizes to 64x64 (nearest)
    - Computes simple gradients and 8-bin orientation histograms on 8x8 cells
    - L2 normalizes the final descriptor

    This is not production-grade, but significantly better than mean color.
    """
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("expected BGR image")

    b = image_bgr[..., 0].astype(np.float32)
    g = image_bgr[..., 1].astype(np.float32)
    r = image_bgr[..., 2].astype(np.float32)
    gray = (0.114 * b + 0.587 * g + 0.299 * r)

    # Resize to 64x64 via nearest-neighbor using numpy indexing (no CV dependency)
    H, W = gray.shape
    target = 64
    ys = (np.linspace(0, max(H - 1, 0), target)).astype(np.int32)
    xs = (np.linspace(0, max(W - 1, 0), target)).astype(np.int32)
    small = gray[ys][:, xs]

    # Gradients (simple [-1, 0, 1])
    dx = np.zeros_like(small)
    dy = np.zeros_like(small)
    dx[:, 1:-1] = (small[:, 2:] - small[:, :-2]) * 0.5
    dy[1:-1, :] = (small[2:, :] - small[:-2, :]) * 0.5

    mag = np.sqrt(dx * dx + dy * dy) + 1e-6
    ang = (np.arctan2(dy, dx) + 2 * np.pi) % (2 * np.pi)  # [0, 2pi)

    # 8x8 cells, 8 orientation bins
    cell = 8
    bins = 8
    bin_w = (2 * np.pi) / bins
    hists = []
    for y0 in range(0, target, cell):
        for x0 in range(0, target, cell):
            m = mag[y0:y0 + cell, x0:x0 + cell]
            a = ang[y0:y0 + cell, x0:x0 + cell]
            # Vote into bins by magnitude
            bidx = np.floor(a / bin_w).astype(np.int32)
            bidx = np.clip(bidx, 0, bins - 1)
            hist = np.zeros((bins,), dtype=np.float32)
            # Flatten loops for speed
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    hist[bidx[i, j]] += m[i, j]
            hists.append(hist)

    desc = np.concatenate(hists).astype(np.float32)
    # Block-wise normalize (optional); do simple global L2 normalize
    n = float(np.linalg.norm(desc))
    if n > 0:
        desc /= n
    return desc
