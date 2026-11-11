from typing import Any, Dict
from html import escape

import streamlit as st

from frontend.components._helpers import get_score_color, get_score_emoji


# Component max scores match backend/core/config.py SCORE_WEIGHTS.
# (Backend returns each component's score on its own scale, not 0–100.)
COMPONENTS = [
    ("Formatting",        "formatting",        20, "📝"),
    ("Keywords & Skills", "keywords",          25, "🔑"),
    ("Content Quality",   "content",           25, "📄"),
    ("Skill Validation",  "skill_validation",  15, "✅"),
    ("ATS Compatibility", "ats_compatibility", 15, "🤖"),
]


def display_overall_score(analysis: Dict[str, Any]) -> None:
    """Big colored score card with a short interpretation line."""
    score = float(analysis.get("ATS_score", analysis.get("ats_score", 0)))
    interpretation = analysis.get("interpretation", "")
    text_color, bg_color = get_score_color(score)
    emoji = get_score_emoji(score)

    st.markdown("## 📊 Analysis Results")
    st.markdown(
        f"""
        <div class="score-card" style="--score-color:{text_color}; --score-bg:{bg_color}; --score-percent:{min(max(score, 0), 100)}%;">
            <div class="score-ring" aria-label="ATS score: {score:.0f} out of 100">
                <span class="score-value">{score:.0f}</span><span class="score-total">OUT OF 100</span>
            </div>
            <div class="score-copy">
                <div class="score-overline">{emoji} RESUME ASSESSMENT</div>
                <h3>Overall ATS Score</h3>
                <p>{escape(str(interpretation))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_score_breakdown(analysis: Dict[str, Any]) -> None:
    """Five progress bars, one per scoring component."""
    component_scores = analysis.get("component_scores") or {}
    st.markdown("### 📈 Score Breakdown")

    left, right = st.columns(2, gap="medium")
    for i, (label, key, max_score, icon) in enumerate(COMPONENTS):
        value = float(component_scores.get(key, 0))
        percentage = value / max_score if max_score else 0
        bar_color = "#137567" if percentage >= 0.8 else "#c68b32" if percentage >= 0.6 else "#cd5b65"

        with left if i % 2 == 0 else right:
            st.markdown(
                f"""
                <div class="breakdown-card">
                    <div class="breakdown-label"><strong>{icon} {label}</strong><span>{value:.0f} / {max_score}</span></div>
                    <div class="score-track" role="progressbar" aria-label="{label}" aria-valuenow="{value}" aria-valuemin="0" aria-valuemax="{max_score}">
                        <span style="background:{bar_color}; width:{min(max(percentage, 0), 1) * 100}%;"></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
