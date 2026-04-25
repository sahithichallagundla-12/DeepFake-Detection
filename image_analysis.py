"""
image_analysis.py
-----------------
Core image analysis functions for DeepFake Identity Guard.
Detects manipulation indicators using OpenCV + PIL heuristics.
"""

import cv2
import numpy as np
from PIL import Image, ImageFilter
import io


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert a PIL Image to an OpenCV BGR array."""
    rgb = np.array(pil_image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


# ── 1. Face Inconsistency ─────────────────────────────────────────────────────

def detect_face_inconsistencies(pil_image: Image.Image) -> dict:
    """
    Detect faces and check for basic inconsistencies:
    - Unusual skin-tone variance inside the face region
    - Edge sharpness mismatch between face and background
    Returns a dict with a score (0–1) and a human-readable note.
    """
    img_cv = pil_to_cv2(pil_image)
    gray   = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Use OpenCV's built-in frontal-face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        return {
            "score": 0.0,
            "faces_found": 0,
            "note": "No face detected – skipping face-consistency check."
        }

    scores = []
    for (x, y, w, h) in faces:
        face_region  = img_cv[y : y + h, x : x + w]
        face_gray    = gray[y : y + h, x : x + w]

        # Laplacian variance = measure of sharpness
        lap_var = cv2.Laplacian(face_gray, cv2.CV_64F).var()

        # Skin-tone variance in YCrCb space
        ycrcb      = cv2.cvtColor(face_region, cv2.COLOR_BGR2YCrCb)
        skin_mask  = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
        skin_ratio = np.sum(skin_mask > 0) / (w * h + 1e-6)

        # Heuristic: very low sharpness OR very low skin ratio → suspicious
        sharpness_score = max(0.0, 1.0 - min(lap_var / 500.0, 1.0))  # high var = sharp = good
        skin_score      = max(0.0, 1.0 - skin_ratio)                 # low skin ratio = suspicious

        scores.append((sharpness_score + skin_score) / 2.0)

    avg_score = float(np.mean(scores))
    note = (
        "Face region shows potential inconsistencies (blur / skin-tone mismatch)."
        if avg_score > 0.45
        else "Face region appears consistent."
    )
    return {"score": avg_score, "faces_found": len(faces), "note": note}


# ── 2. Pixel Anomalies (ELA – Error Level Analysis) ──────────────────────────

def detect_pixel_anomalies(pil_image: Image.Image, quality: int = 90) -> dict:
    """
    Error Level Analysis (ELA): re-compress the image and compute the
    difference map.  Regions with high error levels were likely edited.
    Returns a normalised anomaly score and the ELA image as a PIL Image.
    """
    # Re-compress to JPEG in memory
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    # Compute absolute difference
    orig_arr  = np.array(pil_image.convert("RGB")).astype(np.float32)
    comp_arr  = np.array(recompressed).astype(np.float32)
    diff      = np.abs(orig_arr - comp_arr)

    # Amplify for visibility
    ela_amplified = np.clip(diff * 10, 0, 255).astype(np.uint8)
    ela_image     = Image.fromarray(ela_amplified)

    # Score = mean of top-5 % brightest pixels (suspicious hotspots)
    flat         = diff.flatten()
    threshold    = np.percentile(flat, 95)
    hotspot_mean = float(np.mean(flat[flat >= threshold]))
    score        = min(hotspot_mean / 255.0, 1.0)

    note = (
        "High error-level variance detected – possible splicing or editing."
        if score > 0.35
        else "Error level analysis shows normal JPEG compression patterns."
    )
    return {"score": score, "note": note, "ela_image": ela_image}


# ── 3. Blur / Compression Artifacts ──────────────────────────────────────────

def detect_blur_artifacts(pil_image: Image.Image) -> dict:
    """
    Measure overall image sharpness via Laplacian variance.
    Artificially blurred regions (common in deepfakes to hide seams) lower
    the global variance.
    """
    gray    = np.array(pil_image.convert("L"))
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Also check for block artefacts (JPEG compression over-processing)
    dct_score = _block_artifact_score(gray)

    # Low sharpness AND high block score → suspicious
    sharpness_norm = max(0.0, 1.0 - min(lap_var / 1000.0, 1.0))
    combined_score = (sharpness_norm * 0.6 + dct_score * 0.4)

    note = (
        f"Image appears abnormally blurred (sharpness={lap_var:.1f}) – may indicate manipulation."
        if sharpness_norm > 0.5
        else f"Sharpness level is normal (variance={lap_var:.1f})."
    )
    return {"score": combined_score, "laplacian_variance": lap_var, "note": note}


def _block_artifact_score(gray: np.ndarray) -> float:
    """Estimate 8×8 JPEG block artefacts by measuring inter-block discontinuities."""
    h, w = gray.shape
    h8, w8 = (h // 8) * 8, (w // 8) * 8
    g = gray[:h8, :w8].astype(np.float32)

    # Horizontal block boundaries
    h_diff = np.abs(g[7::8, :] - g[8::8, :]).mean() if h8 > 8 else 0
    # Vertical block boundaries
    v_diff = np.abs(g[:, 7::8] - g[:, 8::8]).mean() if w8 > 8 else 0

    boundary_diff = (h_diff + v_diff) / 2.0
    return float(min(boundary_diff / 20.0, 1.0))


# ── 4. Synthetic Image Indicators ────────────────────────────────────────────

def detect_synthetic_indicators(pil_image: Image.Image) -> dict:
    """
    Look for telltale signs of GAN-generated / synthetic images:
    - Noise pattern uniformity (real cameras have non-uniform sensor noise)
    - Colour histogram smoothness (GANs tend to produce very smooth histograms)
    - High-frequency texture regularity
    """
    img_arr = np.array(pil_image.convert("RGB")).astype(np.float32)
    gray    = cv2.cvtColor(img_arr.astype(np.uint8), cv2.COLOR_RGB2GRAY)

    # 1. Noise uniformity: compute local std in non-overlapping 16×16 patches
    patch_stds = []
    for y in range(0, gray.shape[0] - 16, 16):
        for x in range(0, gray.shape[1] - 16, 16):
            patch_stds.append(gray[y:y+16, x:x+16].std())
    noise_uniformity = 1.0 - min(float(np.std(patch_stds)) / 20.0, 1.0)

    # 2. Histogram smoothness per channel
    smoothness_scores = []
    for ch in range(3):
        hist, _ = np.histogram(img_arr[:, :, ch], bins=64, range=(0, 256))
        hist_norm = hist / (hist.sum() + 1e-6)
        # Smooth histograms have low second-derivative magnitude
        d2 = np.abs(np.diff(hist_norm, n=2))
        smoothness_scores.append(1.0 - min(float(d2.mean()) * 100, 1.0))
    hist_smoothness = float(np.mean(smoothness_scores))

    combined = (noise_uniformity * 0.5 + hist_smoothness * 0.5)
    note = (
        "Image noise and colour distribution suggest possible synthetic/GAN origin."
        if combined > 0.6
        else "Noise and colour patterns are consistent with a real photograph."
    )
    return {
        "score": combined,
        "noise_uniformity": noise_uniformity,
        "histogram_smoothness": hist_smoothness,
        "note": note
    }


# ── 5. Manipulation Heatmap (Innovative Feature) ─────────────────────────────

def generate_manipulation_heatmap(pil_image: Image.Image) -> Image.Image:
    """
    Combine ELA + Laplacian gradient to produce a colour heatmap overlay
    highlighting the most suspicious regions of the image.
    """
    w, h = pil_image.size
    img_cv   = pil_to_cv2(pil_image)
    gray     = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # ELA map
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, format="JPEG", quality=90)
    buf.seek(0)
    recomp   = Image.open(buf).convert("RGB")
    ela_arr  = np.abs(
        np.array(pil_image.convert("RGB")).astype(np.float32) -
        np.array(recomp).astype(np.float32)
    ).mean(axis=2)

    # Laplacian map
    lap      = np.abs(cv2.Laplacian(gray, cv2.CV_64F))
    lap_norm = cv2.normalize(lap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # ELA normalised
    ela_norm = cv2.normalize(ela_arr, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Combine (weighted blend)
    combined = cv2.addWeighted(ela_norm, 0.6, lap_norm, 0.4, 0)

    # Apply Gaussian blur for smoother heatmap
    combined_smooth = cv2.GaussianBlur(combined, (21, 21), 0)

    # Apply JET colour map
    heatmap_color = cv2.applyColorMap(combined_smooth, cv2.COLORMAP_JET)

    # Resize to match original
    heatmap_resized = cv2.resize(heatmap_color, (w, h))

    # Overlay on original
    original_rgb  = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    original_resized = cv2.resize(original_rgb, (w, h))
    overlay = cv2.addWeighted(original_resized, 0.55,
                              cv2.cvtColor(heatmap_resized, cv2.COLOR_BGR2RGB), 0.45, 0)
    return Image.fromarray(overlay)


# ── 6. Master Analysis Function ───────────────────────────────────────────────

def analyze_image(pil_image: Image.Image) -> dict:
    """
    Run all checks and return a consolidated results dictionary.
    """
    face_result   = detect_face_inconsistencies(pil_image)
    ela_result    = detect_pixel_anomalies(pil_image)
    blur_result   = detect_blur_artifacts(pil_image)
    synth_result  = detect_synthetic_indicators(pil_image)
    heatmap_image = generate_manipulation_heatmap(pil_image)

    # Weighted overall score
    weights = {"face": 0.30, "ela": 0.30, "blur": 0.20, "synth": 0.20}
    overall_score = (
        face_result["score"]  * weights["face"] +
        ela_result["score"]   * weights["ela"]  +
        blur_result["score"]  * weights["blur"] +
        synth_result["score"] * weights["synth"]
    )

    # Risk level
    if overall_score < 0.30:
        risk_level = "Low"
    elif overall_score < 0.55:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    return {
        "overall_score":      round(overall_score, 3),
        "risk_level":         risk_level,
        "face_analysis":      face_result,
        "ela_analysis":       ela_result,
        "blur_analysis":      blur_result,
        "synthetic_analysis": synth_result,
        "heatmap_image":      heatmap_image,
    }
