"""
lead_tier_section.py - Drop-in additions for your Streamlit dashboard (app.py)

Adds:
    1. A donut chart showing lead distribution across the 3 tiers
    2. 'Action Required: Top Priority Leads' table (Tier 1 (Hot) only, sorted by Lead Score desc)

Both degrade gracefully if the uploaded CSV lacks 'Lead Tier' / 'Lead Score'.
Only uses streamlit, pandas and altair (altair ships with Streamlit, no extra install).

HOW TO USE IN app.py
--------------------
    from lead_tier_section import render_lead_tier_section

    # ... your existing code that loads the CSV into `df` and shows metrics ...

    render_lead_tier_section(df)      # <- add as the last line
"""

import altair as alt
import pandas as pd
import streamlit as st

TIER_COL = "Lead Tier"
SCORE_COL = "Lead Score"
HOT_TIER = "Tier 1 (Hot)"

# Fixed order + colors so the chart is consistent even if a tier has 0 leads
TIER_ORDER = ["Tier 1 (Hot)", "Tier 2 (Warm)", "Tier 3 (Cold)"]
TIER_COLORS = ["#E74C3C", "#F39C12", "#3498DB"]  # red, orange, blue


def _clean_tiers(df: pd.DataFrame) -> pd.Series:
    """Strip stray whitespace so 'Tier 1 (Hot) ' still matches."""
    return df[TIER_COL].astype(str).str.strip()


def render_tier_distribution(df: pd.DataFrame) -> None:
    """Donut chart of leads per tier."""
    st.subheader("📊 Lead Tier Distribution")

    if TIER_COL not in df.columns:
        st.info(
            f"ℹ️ Column **'{TIER_COL}'** not found in this file, so the tier chart "
            "is hidden. Upload the output of the Lead Scorer "
            "(e.g. `v2_prioritized_leads.csv`) to see it."
        )
        return

    counts = (
        _clean_tiers(df)
        .value_counts()
        .reindex(TIER_ORDER, fill_value=0)  # keep all 3 tiers, even if empty
        .rename_axis("Tier")
        .reset_index(name="Leads")
    )

    if counts["Leads"].sum() == 0:
        st.warning(
            "⚠️ No rows matched the expected tier labels "
            f"({', '.join(TIER_ORDER)}). Check the values in the '{TIER_COL}' column."
        )
        return

    counts["Share"] = counts["Leads"] / counts["Leads"].sum()

    donut = (
        alt.Chart(counts)
        .mark_arc(innerRadius=70, outerRadius=130)
        .encode(
            theta=alt.Theta("Leads:Q"),
            color=alt.Color(
                "Tier:N",
                scale=alt.Scale(domain=TIER_ORDER, range=TIER_COLORS),
                legend=alt.Legend(title="Lead Tier"),
            ),
            tooltip=[
                alt.Tooltip("Tier:N"),
                alt.Tooltip("Leads:Q", title="Leads"),
                alt.Tooltip("Share:Q", title="Share", format=".1%"),
            ],
        )
        .properties(height=320)
    )

    chart_col, stats_col = st.columns([2, 1])
    with chart_col:
        st.altair_chart(donut, use_container_width=True)
    with stats_col:
        for _, row in counts.iterrows():
            st.metric(row["Tier"], f"{int(row['Leads']):,}", f"{row['Share']:.1%} of leads",
                      delta_color="off")


def render_priority_leads(df: pd.DataFrame) -> None:
    """Table of Tier 1 (Hot) leads sorted by Lead Score descending."""
    st.subheader("🔥 Action Required: Top Priority Leads")

    missing = [c for c in (TIER_COL, SCORE_COL) if c not in df.columns]
    if missing:
        st.info(
            f"ℹ️ Missing column(s): **{', '.join(missing)}**. The priority table needs both "
            f"'{TIER_COL}' and '{SCORE_COL}'. Upload the Lead Scorer output to enable it."
        )
        return

    hot = df[_clean_tiers(df) == HOT_TIER].copy()

    # Scores might arrive as strings; coerce so sorting is numeric, not alphabetical
    hot[SCORE_COL] = pd.to_numeric(hot[SCORE_COL], errors="coerce")
    hot = hot.sort_values(SCORE_COL, ascending=False, na_position="last")

    if hot.empty:
        st.success("✅ No Tier 1 (Hot) leads in this file right now.")
        return

    st.caption(f"{len(hot):,} hot lead(s), highest score first.")

    max_score = hot[SCORE_COL].max()
    st.dataframe(
        hot,
        use_container_width=True,
        hide_index=True,
        column_config={
            SCORE_COL: st.column_config.ProgressColumn(
                SCORE_COL,
                min_value=0,
                max_value=float(max(max_score, 100)) if pd.notna(max_score) else 100.0,
                format="%.1f",
            )
        },
    )

    st.download_button(
        "⬇️ Download Top Priority Leads (CSV)",
        data=hot.to_csv(index=False).encode("utf-8"),
        file_name="top_priority_leads.csv",
        mime="text/csv",
    )


def render_lead_tier_section(df: pd.DataFrame) -> None:
    """Single entry point: call this from app.py. Never raises, so the rest of the app keeps working."""
    st.divider()
    try:
        render_tier_distribution(df)
    except Exception as exc:  # defensive: a bad CSV should never crash the dashboard
        st.error(f"Could not render the tier chart: {exc}")

    st.divider()
    try:
        render_priority_leads(df)
    except Exception as exc:
        st.error(f"Could not render the priority leads table: {exc}")
