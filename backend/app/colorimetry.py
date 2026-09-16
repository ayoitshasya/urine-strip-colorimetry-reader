# -----------------------------------------------------------------------
# colorimetry.py
#
# What this file does:
#   Contains the core image-analysis logic for the app: turning an
#   uploaded photo of a urine test strip into a set of clinical readings
#   (Glucose, Protein, pH, Ketones, Blood). It decodes the image, samples
#   the color at each expected "pad" location on the strip, and matches
#   that color against a reference chart to decide the result level.
#
# Where it fits in the project:
#   This is the heart of the colorimetry reader — the actual "reading" of
#   the strip. main.py's /analyze endpoint calls `analyze_strip()` as its
#   single entry point into this module.
#
# Closely related files:
#   - reference_data.py: supplies REFERENCE_CHART (known reference colors
#     per parameter/level) and PAD_POSITIONS (where each pad sits on the
#     strip image) that this module matches against.
#   - main.py: calls analyze_strip() and turns ValueError into an HTTP 400.
# -----------------------------------------------------------------------

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
    # Convert the pad's relative horizontal position (0.0-1.0) into actual
    # pixel coordinates for this specific image's width. The vertical
    # position is assumed to always be the image's vertical center, since
    # strip photos are expected to be roughly centered/aligned.
    cx = int(w * x_fraction)
    cy = int(h * 0.5)

    # Sample a small square patch around (cx, cy) rather than a single
    # pixel, then average it — this smooths out camera noise, JPEG
    # compression artifacts, and small alignment errors.
    half = patch_size // 2
    x1, x2 = max(cx - half, 0), min(cx + half, w)
    y1, y2 = max(cy - half, 0), min(cy + half, h)

    patch = img[y1:y2, x1:x2]
    avg_bgr = patch.reshape(-1, 3).mean(axis=0)
    # OpenCV loads/stores images in BGR channel order (not RGB), so the
    # channels must be unpacked in that order and then re-assembled as RGB
    # before returning, to match what the rest of the app (and the
    # reference chart) expects.
    b, g, r = avg_bgr
    return (int(r), int(g), int(b))  # return as RGB


def nearest_reference(rgb: Tuple[int, int, int], parameter: str) -> Dict:
    """Find the closest matching reference color for a given parameter."""
    options = REFERENCE_CHART[parameter]
    best_label, best_color, best_dist = None, None, float("inf")

    # Simple nearest-neighbor color match: compute the Euclidean distance
    # in RGB space between the detected color and every known reference
    # color for this parameter, and keep whichever reference is closest.
    # This is an approximation — real colorimetry would use a calibrated
    # color space (e.g. Lab) — but works reasonably well for consistent
    # lighting conditions.
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
    # PAD_POSITIONS defines, for each clinical parameter (Glucose, Protein,
    # etc.), where along the strip's width its color pad is expected to be.
    # Loop through every parameter, sample its pad's color, and classify it.
    for parameter, x_fraction in PAD_POSITIONS.items():
        rgb = extract_pad_color(img, x_fraction)
        match = nearest_reference(rgb, parameter)
        results[parameter] = {
            "detected_rgb": rgb,
            **match
        }

    return results