from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

# Adjust this estimate to reflect your own API cost per drafted email.
SAVINGS_PER_DRAFT_USD = 0.01

REQUIRED_COLUMNS = {
    "Company",
    "Scraped Context",
    "Email Draft",
    "Pipeline Status",
    "Date",
}

def load_csv(uploaded_file) -> pd.DataFrame:
    """Read an uploaded CSV and verify its required columns."""
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            "The CSV is missing required column(s): "
            + ", ".join(sorted(missing_columns))
        )

    return df

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dates and identify rows with drafted emails."""
    prepared = df.copy()
    prepared["Date"] = pd.to_datetime(prepared["Date"], errors="coerce")

    # Treat non-empty email draft values as drafted emails.
    prepared["_has_email_draft"] = (
        prepared["Email Draft"].fillna("").astype(str).str.strip().ne("")
    )

    return prepared

def render_metrics(df: pd.DataFrame) -> None:
    """Show the main outreach metrics."""
    total_leads = len(df)
    total_drafts = int(df["_has_email_draft"].sum())
    estimated_savings = total_drafts * SAVINGS_PER_DRAFT_USD

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads Processed", f"{total_leads:,}")
    col2.metric("Total Emails Drafted", f"{total_drafts:,}")
    col3.metric("Estimated API Cost Saved", f"${estimated_savings:,.2f}")

def render_leads_chart(df: pd.DataFrame) -> None:
    """Display daily lead counts for rows with valid dates."""
    dated_rows = df.dropna(subset=["Date"])

    if dated_rows.empty:
        st.info("No valid dates were found in the CSV, so the chart cannot be displayed.")
        return

    leads_by_date = (
        dated_rows.groupby(dated_rows["Date"].dt.date)
        .size()
        .rename("Leads")
        .sort_index()
    )
    leads_by_date.index = pd.to_datetime(leads_by_date.index)

    st.subheader("Leads Processed Over Time")
    st.bar_chart(leads_by_date, y="Leads", use_container_width=True)

def main() -> None:
    st.set_page_config(
        page_title="GTM Outreach Analytics",
        page_icon="📊",
        layout="wide",
    )

    st.title("GTM Outreach Analytics")
    st.caption("A quick view of lead processing and email drafting activity.")

    with st.sidebar:
        st.header("How to use")
        st.markdown(
            """
            1. Export your Google Sheets tracker as a CSV file.
            2. Upload the CSV below.
            3. Review the metrics and leads-by-date chart.

            **Expected columns:** `Company`, `Scraped Context`,
            `Email Draft`, `Pipeline Status`, and `Date`.
            """
        )
        st.divider()
        st.caption(
            f"Cost-savings estimate uses ${SAVINGS_PER_DRAFT_USD:.2f} "
            "per drafted email. Update this assumption in `app.py`."
        )

    uploaded_file = st.file_uploader(
        "Upload your GTM tracker CSV",
        type=["csv"],
        help="Upload a CSV exported from your outreach tracker.",
    )

    if uploaded_file is None:
        st.info("Upload a CSV file to view your outreach analytics.")
        return

    try:
        raw_df = load_csv(uploaded_file)
        df = prepare_data(raw_df)
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.error(f"Could not load the CSV: {error}")
        return

    render_metrics(df)
    st.divider()
    render_leads_chart(df)

    with st.expander("Preview uploaded data"):
        st.dataframe(raw_df.head(100), use_container_width=True)

if __name__ == "__main__":
    main()
