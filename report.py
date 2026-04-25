"""
report.py
---------
Generates a structured analysis report from the image analysis
and similarity results.
"""

from datetime import datetime


# ── Safety Guidance Library ───────────────────────────────────────────────────

SAFETY_GUIDANCE = {
    "Low": [
        "✅ No strong manipulation signals detected.",
        "Keep a local backup of the original image with its metadata (EXIF data).",
        "If you still feel uncomfortable, you can run a reverse image search on "
        "Google Images or TinEye to check for unauthorised copies.",
        "Stay vigilant – run a fresh scan if the image is redistributed.",
    ],
    "Moderate": [
        "⚠️  Moderate manipulation signals detected – further review is advised.",
        "Preserve the image and all associated metadata as evidence.",
        "Perform a manual reverse-image search (Google Images, TinEye, PimEyes) "
        "to locate other versions.",
        "Report the image to the platform where it was found using their "
        "'Report / Flag' feature.",
        "Document the URL, timestamp, and any usernames associated with the image.",
        "Consider contacting a trusted person or digital-safety organisation "
        "such as the Cyber Civil Rights Initiative (cybercivilrights.org).",
    ],
    "High": [
        "🚨 HIGH RISK – Strong indicators of deepfake or manipulation detected.",
        "Do NOT share or engage with the image further to avoid amplification.",
        "Preserve all evidence: screenshot the URLs, capture timestamps, and "
        "save the image securely offline.",
        "Report to the hosting platform immediately using their abuse/CSAM/NCII "
        "reporting tools.",
        "Contact your national cybercrime authority:",
        "  • India  : cybercrime.gov.in / 1930",
        "  • USA    : ic3.gov (FBI Internet Crime Complaint Center)",
        "  • UK     : Action Fraud – actionfraud.police.uk",
        "  • EU     : Report to Europol via your national police",
        "Request image removal via StopNCII (stopncii.org) – a free tool that "
        "creates a hash fingerprint to block the image across partner platforms.",
        "Seek legal advice: non-consensual deepfakes are illegal in many "
        "jurisdictions and you may be entitled to a takedown order.",
        "Reach out for emotional support: Cyber Civil Rights Initiative helpline "
        "or local victim support services.",
    ],
}


# ── Report Builder ────────────────────────────────────────────────────────────

def build_report(analysis_results: dict, similarity_results: dict) -> dict:
    """
    Consolidate analysis and similarity results into a final report dict.
    """
    risk_level    = analysis_results["risk_level"]
    overall_score = analysis_results["overall_score"]

    # Deepfake probability string
    deepfake_pct  = round(overall_score * 100, 1)
    if deepfake_pct < 30:
        probability_label = f"{deepfake_pct}% – Unlikely to be manipulated"
    elif deepfake_pct < 55:
        probability_label = f"{deepfake_pct}% – Possible manipulation"
    else:
        probability_label = f"{deepfake_pct}% – Likely manipulated / synthetic"

    # Collect detected indicators
    indicators = []
    fa = analysis_results["face_analysis"]
    if fa["score"] > 0.40:
        indicators.append(f"Face inconsistency detected ({fa['note']})")

    ea = analysis_results["ela_analysis"]
    if ea["score"] > 0.30:
        indicators.append(f"Pixel anomaly (ELA) detected ({ea['note']})")

    ba = analysis_results["blur_analysis"]
    if ba["score"] > 0.40:
        indicators.append(f"Blur / compression artefact detected ({ba['note']})")

    sa = analysis_results["synthetic_analysis"]
    if sa["score"] > 0.55:
        indicators.append(f"Synthetic image indicator detected ({sa['note']})")

    if not indicators:
        indicators.append("No specific manipulation indicators triggered.")

    # Similar image findings
    sim_findings = []
    sc = similarity_results.get("self_consistency", {})
    if sc.get("flagged"):
        sim_findings.append(f"Hash instability detected – {sc.get('note', '')}")
    else:
        sim_findings.append("Image hashes are self-consistent (no instability).")

    report = {
        "generated_at":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "risk_level":         risk_level,
        "deepfake_probability": probability_label,
        "overall_score":      overall_score,
        "manipulation_indicators": indicators,
        "similar_image_findings":  sim_findings,
        "hash_fingerprints":  similarity_results.get("self_consistency", {})
                                                .get("hash_strings", {}),
        "safety_guidance":    SAFETY_GUIDANCE[risk_level],
        "disclaimer": (
            "This tool uses heuristic analysis and is not a replacement for "
            "professional forensic examination. Results are indicative only."
        ),
    }
    return report


def format_report_markdown(report: dict) -> str:
    """Render the report as a Markdown string for display."""
    lines = [
        "# 🛡️ DeepFake Identity Guard – Analysis Report",
        f"**Generated:** {report['generated_at']}",
        "",
        f"## Risk Level: `{report['risk_level']}`",
        f"**Deepfake Probability:** {report['deepfake_probability']}",
        "",
        "## 🔍 Detected Manipulation Indicators",
    ]
    for ind in report["manipulation_indicators"]:
        lines.append(f"- {ind}")

    lines += [
        "",
        "## 🔁 Similar Image Findings",
    ]
    for finding in report["similar_image_findings"]:
        lines.append(f"- {finding}")

    if report["hash_fingerprints"]:
        lines += ["", "**Image Hash Fingerprints:**"]
        for algo, val in report["hash_fingerprints"].items():
            lines.append(f"- `{algo.upper()}`: `{val}`")

    lines += [
        "",
        "## 🛡️ Safety Guidance",
    ]
    for tip in report["safety_guidance"]:
        lines.append(f"- {tip}")

    lines += [
        "",
        "---",
        f"*{report['disclaimer']}*",
    ]
    return "\n".join(lines)
