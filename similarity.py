"""
similarity.py
-------------
Image hashing utilities for duplicate / altered-version detection.
Uses perceptual hashing (pHash) and average hashing (aHash) from the
`imagehash` library so that visually similar images produce similar hashes
even after minor edits, resizing, or colour adjustments.
"""

import io
import imagehash
from PIL import Image


# ── Hash Generation ───────────────────────────────────────────────────────────

def compute_hashes(pil_image: Image.Image) -> dict:
    """
    Compute multiple hash types for the given image.
    Returns a dict with hash objects and their hex strings.
    """
    img_rgb = pil_image.convert("RGB")
    return {
        "phash":    imagehash.phash(img_rgb),          # Perceptual hash
        "ahash":    imagehash.average_hash(img_rgb),   # Average hash
        "dhash":    imagehash.dhash(img_rgb),           # Difference hash
        "whash":    imagehash.whash(img_rgb),           # Wavelet hash
    }


def hashes_to_strings(hash_dict: dict) -> dict:
    """Convert hash objects → hex strings for display / storage."""
    return {k: str(v) for k, v in hash_dict.items()}


# ── Similarity Comparison ─────────────────────────────────────────────────────

def compare_hashes(hash_a: dict, hash_b: dict) -> dict:
    """
    Compare two hash dicts and return per-algorithm Hamming distances
    plus an overall similarity score (0 = identical, 1 = completely different).
    """
    results = {}
    max_dist = 64  # pHash / aHash use 64-bit hashes

    for algo in ("phash", "ahash", "dhash", "whash"):
        dist = hash_a[algo] - hash_b[algo]          # Hamming distance
        similarity = 1.0 - dist / max_dist
        results[algo] = {"hamming_distance": dist, "similarity": round(similarity, 3)}

    # Overall similarity = mean of the four algorithms
    avg_sim = sum(v["similarity"] for v in results.values()) / len(results)
    results["overall_similarity"] = round(avg_sim, 3)
    return results


def interpret_similarity(overall_similarity: float) -> dict:
    """
    Turn a raw similarity score into a human-readable label and flag.
    """
    if overall_similarity >= 0.97:
        label = "Exact or near-exact match"
        flag  = True
        detail = (
            "This image is virtually identical to a known version. "
            "It may be an unmodified copy or have only imperceptible changes."
        )
    elif overall_similarity >= 0.85:
        label = "Highly similar – possible altered copy"
        flag  = True
        detail = (
            "The image shares strong visual similarities with another version. "
            "Minor cropping, colour grading, or watermark removal may have been applied."
        )
    elif overall_similarity >= 0.65:
        label = "Moderately similar – review recommended"
        flag  = False
        detail = (
            "Some structural similarity detected. "
            "Could share the same subject or scene but with significant edits."
        )
    else:
        label = "Low similarity – likely a different image"
        flag  = False
        detail = "No strong visual match found against the comparison image."

    return {"label": label, "flagged": flag, "detail": detail}


# ── Self-Similarity Check (single-image heuristic) ────────────────────────────

def self_consistency_check(pil_image: Image.Image) -> dict:
    """
    Compare the original image against a slightly augmented version of itself
    (mild brightness shift).  Manipulated images often show hash instability
    under tiny perturbations because edited regions react differently.
    Returns a stability score: high stability → consistent image.
    """
    from PIL import ImageEnhance

    original_hashes = compute_hashes(pil_image)

    # Slightly brighten and compare
    enhancer  = ImageEnhance.Brightness(pil_image.convert("RGB"))
    augmented = enhancer.enhance(1.05)
    aug_hashes = compute_hashes(augmented)

    comparison = compare_hashes(original_hashes, aug_hashes)
    stability  = comparison["overall_similarity"]

    note = (
        "Hash instability under minor augmentation – some regions may be composited."
        if stability < 0.88
        else "Image hashes remain stable under minor augmentation."
    )
    return {
        "stability_score": stability,
        "flagged": stability < 0.88,
        "note": note,
        "hash_strings": hashes_to_strings(original_hashes),
    }
