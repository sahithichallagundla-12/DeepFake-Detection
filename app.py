"""
app.py
------
DeepFake Identity Guard – Streamlit Web Application
Run with:  streamlit run app.py
"""

import streamlit as st
from PIL import Image
import sys, os

# Make sure the utils package is importable regardless of working directory
sys.path.insert(0, os.path.dirname(__file__))

from utils.image_analysis import analyze_image
from utils.similarity      import self_consistency_check
from utils.report          import build_report, format_report_markdown


# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DeepFake Identity Guard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ---- Global ---- */
body { font-family: 'Segoe UI', sans-serif; }

/* ---- Header banner ---- */
.header-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
}
.header-banner h1 { font-size: 2.2rem; margin: 0; }
.header-banner p  { margin: 0.4rem 0 0; opacity: 0.85; font-size: 1.05rem; }

/* ---- Risk badges ---- */
.risk-low      { background:#d4edda; color:#155724; border:1px solid #c3e6cb; }
.risk-moderate { background:#fff3cd; color:#856404; border:1px solid #ffc107; }
.risk-high     { background:#f8d7da; color:#721c24; border:1px solid #f5c6cb; }
.risk-badge {
    display:inline-block; padding:0.4rem 1.2rem;
    border-radius:50px; font-weight:700; font-size:1.1rem;
}

/* ---- Score card ---- */
.score-card {
    background: #f8f9fa;
    border-left: 5px solid #0f3460;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}

/* ---- Indicator card ---- */
.indicator-card {
    background: #fff;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}

/* ---- Guidance card ---- */
.guidance-card {
    background: #e8f4fd;
    border-left: 4px solid #0d6efd;
    padding: 0.8rem 1.2rem;
    border-radius: 6px;
    margin: 0.4rem 0;
    font-size: 0.95rem;
}

/* ---- Meter bar ---- */
.meter-outer {
    background: #e9ecef;
    border-radius: 50px;
    height: 28px;
    width: 100%;
    overflow: hidden;
    margin: 0.5rem 0;
}
.meter-inner {
    height: 100%;
    border-radius: 50px;
    display:flex; align-items:center; justify-content:flex-end;
    padding-right: 10px;
    color: white; font-weight: 700; font-size: 0.9rem;
    transition: width 0.6s ease;
}
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-banner">
    <h1>🛡️ DeepFake Identity Guard</h1>
    <p>Protecting digital identities through AI-powered image manipulation detection.</p>
</div>
""", unsafe_allow_html=True)


# ── Helper: Risk Meter ────────────────────────────────────────────────────────

def render_risk_meter(score: float, risk_level: str):
    pct = int(score * 100)
    color_map = {"Low": "#28a745", "Moderate": "#ffc107", "High": "#dc3545"}
    color = color_map.get(risk_level, "#6c757d")
    st.markdown(f"""
    <div class="meter-outer">
      <div class="meter-inner" style="width:{pct}%; background:{color};">
        {pct}%
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Helper: Indicator row ─────────────────────────────────────────────────────

def render_indicator(label: str, score: float, note: str, threshold: float = 0.35):
    pct   = int(score * 100)
    flag  = score >= threshold
    emoji = "🔴" if flag else "🟢"
    color = "#dc3545" if flag else "#28a745"
    st.markdown(f"""
    <div class="indicator-card">
        <strong>{emoji} {label}</strong>
        <div class="meter-outer" style="height:16px; margin:6px 0;">
          <div class="meter-inner"
               style="width:{pct}%; background:{color}; height:16px; font-size:0.75rem;">
            {pct}%
          </div>
        </div>
        <small style="color:#6c757d;">{note}</small>
    </div>
    """, unsafe_allow_html=True)


# ── Layout: two columns ───────────────────────────────────────────────────────

left_col, right_col = st.columns([1, 1.6], gap="large")

with left_col:
    st.subheader("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose an image file (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        pil_image = Image.open(uploaded_file).convert("RGB")
        st.image(pil_image, caption="Uploaded Image", use_column_width=True)

        w, h = pil_image.size
        st.caption(f"📐 {w} × {h} px  |  {uploaded_file.size // 1024} KB")

        st.markdown("---")
        analyze_btn = st.button(
            "🔍 Analyse Image",
            use_container_width=True,
            type="primary",
        )
    else:
        st.info("👆 Upload an image to begin analysis.")
        analyze_btn = False


# ── Analysis ──────────────────────────────────────────────────────────────────

if uploaded_file and analyze_btn:
    with st.spinner("🔄 Analysing image – this may take a few seconds…"):
        analysis     = analyze_image(pil_image)
        similarity   = {"self_consistency": self_consistency_check(pil_image)}
        report       = build_report(analysis, similarity)
        report_md    = format_report_markdown(report)

    # ── Right column: results ─────────────────────────────────────────────

    with right_col:
        st.subheader("📊 Analysis Results")

        # ── Risk badge + meter ────────────────────────────────────────────
        risk    = report["risk_level"]
        score   = report["overall_score"]
        cls_map = {"Low": "risk-low", "Moderate": "risk-moderate", "High": "risk-high"}

        st.markdown(f"""
        <p>
            <strong>Risk Level:</strong>&nbsp;
            <span class="risk-badge {cls_map[risk]}">{risk}</span>
        </p>
        <p><strong>Deepfake Probability:</strong> {report['deepfake_probability']}</p>
        """, unsafe_allow_html=True)

        st.markdown("**Manipulation Risk Meter:**")
        render_risk_meter(score, risk)

        st.markdown("---")

        # ── Manipulation Heatmap (Innovative Feature) ─────────────────────
        st.subheader("🌡️ Manipulation Heatmap")
        st.caption(
            "Heatmap highlights regions with the highest manipulation signals "
            "(red = suspicious, blue = normal)."
        )
        st.image(
            analysis["heatmap_image"],
            caption="ELA + Gradient Heatmap Overlay",
            use_column_width=True,
        )

        st.markdown("---")

        # ── Per-indicator breakdown ────────────────────────────────────────
        st.subheader("🔬 Detailed Indicators")

        fa = analysis["face_analysis"]
        render_indicator(
            f"Face Inconsistency  (faces found: {fa['faces_found']})",
            fa["score"], fa["note"], threshold=0.40
        )

        ea = analysis["ela_analysis"]
        render_indicator("Pixel Anomaly (ELA)", ea["score"], ea["note"], threshold=0.30)

        ba = analysis["blur_analysis"]
        render_indicator(
            f"Blur / Compression Artefacts  (Laplacian var: {ba['laplacian_variance']:.1f})",
            ba["score"], ba["note"], threshold=0.40
        )

        sa = analysis["synthetic_analysis"]
        render_indicator(
            "Synthetic / GAN Indicators",
            sa["score"], sa["note"], threshold=0.55
        )

        sc = similarity["self_consistency"]
        render_indicator(
            "Hash Stability Check",
            1.0 - sc["stability_score"],
            sc["note"],
            threshold=0.12
        )

        st.markdown("---")

        # ── ELA image ─────────────────────────────────────────────────────
        with st.expander("🔎 View Raw ELA (Error Level Analysis) Map"):
            st.image(
                ea["ela_image"],
                caption="ELA Map – brighter regions = higher error level",
                use_column_width=True,
            )

        # ── Hash fingerprints ──────────────────────────────────────────────
        with st.expander("🔑 Image Hash Fingerprints"):
            for algo, val in sc["hash_strings"].items():
                st.code(f"{algo.upper()}: {val}", language="text")

        st.markdown("---")

        # ── Safety Guidance ────────────────────────────────────────────────
        st.subheader("🛡️ Safety Guidance")
        for tip in report["safety_guidance"]:
            st.markdown(f'<div class="guidance-card">{tip}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── Full Report Download ───────────────────────────────────────────
        st.subheader("📄 Full Report")
        with st.expander("View Full Markdown Report"):
            st.markdown(report_md)

        st.download_button(
            label="⬇️  Download Report (.md)",
            data=report_md,
            file_name="deepfake_identity_guard_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

        st.caption(f"*{report['disclaimer']}*")

elif not uploaded_file:
    with right_col:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#6c757d;">
            <div style="font-size:4rem;">🔍</div>
            <h3>Ready to Analyse</h3>
            <p>Upload an image on the left and click <strong>Analyse Image</strong>
               to get a full manipulation report.</p>
            <hr/>
            <p><strong>What we check:</strong></p>
            <ul style="text-align:left; display:inline-block;">
                <li>👤 Face inconsistencies</li>
                <li>🖼️ Pixel anomalies (ELA)</li>
                <li>🌀 Blur & compression artefacts</li>
                <li>🤖 Synthetic/GAN image indicators</li>
                <li>🔁 Image hash similarity & stability</li>
                <li>🌡️ <strong>Manipulation heatmap</strong> (innovative)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="text-align:center; font-size:0.85rem; color:#6c757d; padding:0.5rem;">
    🛡️ <strong>DeepFake Identity Guard</strong> · Built for digital safety ·
    For emergencies contact <a href="https://cybercrime.gov.in" target="_blank">cybercrime.gov.in</a>
    or <a href="https://stopncii.org" target="_blank">StopNCII.org</a>
</div>
""", unsafe_allow_html=True)
