import os
import re
import streamlit as st

CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "style.css")

# Semantic status palette — deliberately fixed (not theme-driven), each
# tuned dark/saturated enough that white badge text stays readable
# whether the page itself is in Light or Dark mode.
COLOR_SUCCESS = "#15803d"
COLOR_WARNING = "#b45309"
COLOR_DANGER = "#b91c1c"
COLOR_NEUTRAL = "#475569"
COLOR_PRIMARY = "#0891b2"

# Extra accent palette — used only for decorative elements (numbered step
# badges, the AI Explanation card) that carry no status meaning, so they're
# kept separate from the semantic colors above.
COLOR_ACCENT_CYAN = "#0891b2"
COLOR_ACCENT_AMBER = "#b45309"
COLOR_ACCENT_VIOLET = "#6d28d9"
COLOR_ACCENT_CORAL = "#e11d48"

STEP_BADGE_COLORS = [COLOR_ACCENT_CYAN, COLOR_ACCENT_AMBER, COLOR_ACCENT_VIOLET]


def load_css():
    """Inject assets/style.css into the page. Safe no-op if the file is missing."""
    if os.path.exists(CSS_PATH):
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def similarity_status(score_pct):
    """
    Map a 0-100 similarity score to (label, colour):
      0-30   -> Low Match
      31-60  -> Moderate Match
      61-100 -> High Match
    """
    if score_pct <= 30:
        return "Low Match", COLOR_DANGER
    if score_pct <= 60:
        return "Moderate Match", COLOR_WARNING
    return "High Match", COLOR_SUCCESS


def health_status(score):
    """
    Map a 0-100 Vehicle_Health_Score to (label, colour):
      80-100 -> Excellent
      60-79  -> Good
      40-59  -> Fair
      0-39   -> Poor
    """
    if score is None:
        return "Unknown", COLOR_NEUTRAL
    if score >= 80:
        return "Excellent", COLOR_SUCCESS
    if score >= 60:
        return "Good", COLOR_PRIMARY
    if score >= 40:
        return "Fair", COLOR_WARNING
    return "Poor", COLOR_DANGER


def risk_color(risk_level):
    """Map the existing Maintenance_Risk_Level string to a display colour."""
    if not risk_level:
        return COLOR_NEUTRAL
    level = str(risk_level).lower()
    if "low" in level:
        return COLOR_SUCCESS
    if "medium" in level:
        return COLOR_WARNING
    if "high" in level:
        return COLOR_DANGER
    return COLOR_NEUTRAL


def status_badge(label, color):
    """
    Return an inline HTML pill/badge for status display.

    Uses a solid, pre-darkened background with white text rather than a
    translucent tint over the page background — that way contrast holds
    whether the surrounding page is in Streamlit Light or Dark mode.
    """
    return (
        f'<span style="background-color:{color}; color:#ffffff; '
        f'padding:3px 11px; border-radius:12px; font-size:0.85rem; '
        f'font-weight:600;">{label}</span>'
    )


def section_header(title, subtitle=None):
    """
    Consistent section heading used across the report.

    Titles that start with "N. " (the three top-level steps — "1. Select
    Vehicle", "2. Describe the Complaint", "3. Diagnosis Report") render as
    a colored circular step badge instead of a plain heading, cycling
    through STEP_BADGE_COLORS. Every other header (card titles like
    "Vehicle", "Detected Fault", "AI Explanation") is unaffected.
    """
    step_match = re.match(r"^(\d+)\.\s+(.*)", title)
    if step_match:
        step_num, rest = step_match.groups()
        color = STEP_BADGE_COLORS[(int(step_num) - 1) % len(STEP_BADGE_COLORS)]
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:10px; '
            f'margin:0.25rem 0 0.7rem;">'
            f'<span style="display:inline-flex; align-items:center; justify-content:center; '
            f'width:28px; height:28px; border-radius:50%; background-color:{color}; '
            f'color:#ffffff; font-weight:700; font-size:0.85rem; flex-shrink:0;">{step_num}</span>'
            f'<span style="font-size:1.15rem; font-weight:600; color:var(--text-color);">{rest}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"#### {title}")
    if subtitle:
        st.caption(subtitle)
