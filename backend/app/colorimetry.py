import numpy as np
import cv2
from typing import Dict, Tuple
from .reference_data import REFERENCE_CHART, PAD_POSITIONS


def read_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode uploaded image bytes into an OpenCV BGR array."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image. Please upload a valid image file.")
    return img


def extract_pad_color(img: np.ndarray, x_fraction: float, patch_size: int = 20) -> Tuple[int, int, int]:
    """
    Extract the average RGB color from a small patch on the strip image,
    at a given horizontal fraction of the image width (vertical center assumed).
    """
    h, w, _ = img.shape
    cx = int(w * x_fraction)
    cy = int(h * 0.5)

    half = patch_size // 2
    x1, x2 = max(cx - half, 0), min(cx + half, w)
    y1, y2 = max(cy - half, 0), min(cy + half, h)

    patch = img[y1:y2, x1:x2]
    avg_bgr = patch.reshape(-1, 3).mean(axis=0)
    b, g, r = avg_bgr
    return (int(r), int(g), int(b))  # return as RGB


def nearest_reference(rgb: Tuple[int, int, int], parameter: str) -> Dict:
    """Find the closest matching reference color for a given parameter."""
    options = REFERENCE_CHART[parameter]
    best_label, best_color, best_dist = None, None, float("inf")

    for label, ref_rgb in options:
        dist = sum((a - b) ** 2 for a, b in zip(rgb, ref_rgb)) ** 0.5
        if dist < best_dist:
            best_dist, best_label, best_color = dist, label, ref_rgb

    return {
        "result": best_label,
        "matched_reference_rgb": best_color,
        "distance": round(best_dist, 2),
    }


def analyze_strip(image_bytes: bytes) -> Dict:
    """Full pipeline: decode image -> extract pad colors -> match against reference chart."""
    img = read_image_from_bytes(image_bytes)

    results = {}
    for parameter, x_fraction in PAD_POSITIONS.items():
        rgb = extract_pad_color(img, x_fraction)
        match = nearest_reference(rgb, parameter)
        results[parameter] = {
            "detected_rgb": rgb,
            **match
        }

    return results