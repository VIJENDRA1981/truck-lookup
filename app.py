# app.py
# Truck Lookup Web App — Streamlit
# Enter a Truck No. (or pick from dropdown) → instantly see Broker Name, PAN Name, PAN No.
# Works with your own Excel/CSV upload; includes a built‑in example dataset.

import io
from io import BytesIO
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Truck Lookup", page_icon="🚚", layout="wide")

st.title("🚚 Truck Lookup — Broker & PAN Details")
st.caption("Type or select a Truck No. to fetch Broker Name, PAN Name, and PAN No. from your data.")

# =========================
# Helpers
# =========================

def load_file(uploaded_file) -> pd.DataFrame:
    """Load CSV or Excel into a DataFrame."""
    if uploaded_file is None:
        return None
    name = uploaded_file.name.lower()
    if name.endswith((".csv", ".txt")):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        st.warning("Unsupported file type. Please upload CSV or Excel (xlsx).")
        return None


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def suggest_column(df: pd.DataFrame, keywords: list[str]) -> str | None:
    cols = list(df.columns)
    lowered = {c: c.lower() for c in cols}
    for c in cols:
        lc = lowered[c]
        if any(k in lc for k in keywords):
            return c
    return None


def make_example_df() -> pd.DataFrame:
    return pd.DataFrame({
        "SR NO.": [1,2,3,4,5,6],
        "Date": ["16-08-2025"]*6,
        "Challan No.": ["101","102","103","104","105","106"],
        "Broker Name": ["SRPL COMPANY VEHICLE"]*6,
        "Truck No.": ["GJ06ZZ1406","GJ06BX1706","GJ06BV8677","GJ06BV8938","GJ06BX1823","GJ06BT9034"],
        "PAN Name": ["SRPL"]*6,
        "PAN No.": ["AAGCS6114G"]*6,
    })


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    return output.getvalue()

# =========================
# Sidebar — Data Source
# =========================
with st.sidebar:
    st.header("📂 Data Source")
    uploaded = st.file_uploader("Upload CSV or Excel (.xlsx)", type=["csv","txt","xlsx","xlsm","xls"])
    use_example = st.toggle("Use example data", value=(uploaded is None))

if uploaded is not None:
    df_raw = load_file(uploaded)
else:
    df_raw = make_example_df() if use_example else None

if df_raw is None:
    st.info("Upload a CSV/Excel or enable 'Use example data' in the sidebar.")
    st.stop()

# Clean columns
_df = clean_columns(df_raw)

# =========================
# Column Mapping
# =========================
st.subheader("🧭 Map Columns (if needed)")
col1, col2, col3, col4 = st.columns(4)

truck_guess = suggest_column(_df, ["truck", "vehicle", "veh"])
broker_guess = suggest_column(_df, ["broker", "party", "vendor", "company"])
panname_guess = suggest_column(_df, ["pan name", "panname", "name"])
panno_guess = suggest_column(_df, ["pan no", "pan", "panno", "pan number"])  # keep generic order

with col1:
    truck_col = st.selectbox("Truck No. column", options=list(_df.columns), index=(list(_df.columns).index(truck_guess) if truck_guess in _df.columns else 0))
with col2:
    broker_col = st.selectbox("Broker Name column", options=list(_df.columns), index=(list(_df.columns).index(broker_guess) if broker_guess in _df.columns else 0))
with col3:
    panname_col = st.selectbox("PAN Name column", options=list(_df.columns), index=(list(_df.columns).index(panname_guess) if panname_guess in _df.columns else 0))
with col4:
    panno_col = st.selectbox("PAN No. column", options=list(_df.columns), index=(list(_df.columns).index(panno_guess) if panno_guess in _df.columns else 0))

# =========================
# Search Controls
# =========================
st.subheader("🔎 Search Truck")
left, right = st.columns([2,1])

with left:
    query = st.text_input("Type Truck No. (exact or partial)", placeholder="e.g., GJ06BX1706 or 'GJ06B'")
with right:
    exact = st.toggle("Exact match only", value=False)

unique_trucks = sorted(_df[truck_col].dropna().astype(str).unique())
selected = st.multiselect("Or pick from list", options=unique_trucks, max_selections=1)

active_query = (selected[0] if selected else query).strip()

# =========================
# Filter Logic
# =========================
res = _df[[truck_col, broker_col, panname_col, panno_col]].copy()
res.columns = ["Truck No.", "Broker Name", "PAN Name", "PAN No."]

if active_query:
    if exact:
        mask = res["Truck No."].astype(str).str.casefold() == active_query.casefold()
    else:
        mask = res["Truck No."].astype(str).str.contains(active_query, case=False, na=False)
    res = res.loc[mask]

count = len(res)

st.success(f"{count} record(s) found." if active_query else f"Showing all {len(res)} record(s). Use search to filter.")

st.dataframe(res, use_container_width=True, hide_index=True)

# =========================
# Download Buttons
# =========================
col_a, col_b = st.columns(2)
with col_a:
    csv_bytes = res.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="truck_lookup_results.csv", mime="text/csv")
with col_b:
    xlsx_bytes = to_excel_bytes(res)
    st.download_button("⬇️ Download Excel", data=xlsx_bytes, file_name="truck_lookup_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# =========================
# Tips
# =========================
with st.expander("💡 Tips"):
    st.markdown(
        "- You can upload your live data file from the sidebar.\n"
        "- If column names differ, use the mapping selectors above.\n"
        "- Turn on **Exact match only** for strict matches; turn off to allow partial search.\n"
        "- Use the download buttons to share results on WhatsApp/Email."
    )
