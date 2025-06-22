import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Jira Ticket Data Analysis", layout="wide")
st.title("Jira Ticket Data Analysis")

# --- Load Data ---
@st.cache_data
def load_data():
    xls = pd.ExcelFile("TestJIRA.xlsx")
    df = pd.read_excel(xls, sheet_name="Your Jira Issues")
    # Standardize column names
    df.columns = [c.strip() for c in df.columns]
    return df

uploaded = st.file_uploader("Upload TestJIRA.xlsx", type="xlsx")

if uploaded is not None:
    df = pd.read_excel(uploaded, sheet_name="Your Jira Issues")
    df.columns = [c.strip() for c in df.columns]
    # (Rest of your analysis code goes here)
else:
    st.info("Please upload a TestJIRA.xlsx file to begin.")
    st.stop()


# --- Preprocess Dates ---
for col in ["Created", "Updated", "Due date", "Resolution Date"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
issue_types = df["Issue Type"].dropna().unique()
statuses = df["Status"].dropna().unique()
priorities = df["Priority"].dropna().unique()
assignees = df["Assignee"].dropna().unique()

issue_type_sel = st.sidebar.multiselect("Issue Type", issue_types, default=list(issue_types))
status_sel = st.sidebar.multiselect("Status", statuses, default=list(statuses))
priority_sel = st.sidebar.multiselect("Priority", priorities, default=list(priorities))
assignee_sel = st.sidebar.multiselect("Assignee", assignees, default=list(assignees))

filtered = df[
    df["Issue Type"].isin(issue_type_sel) &
    df["Status"].isin(status_sel) &
    df["Priority"].isin(priority_sel) &
    (df["Assignee"].isin(assignee_sel) | df["Assignee"].isna())
]

st.subheader("Filtered Jira Tickets")
st.dataframe(filtered, use_container_width=True)

# --- Metrics ---
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Tickets", len(filtered))
with col2:
    st.metric("Open Tickets", filtered[~filtered["Status"].str.lower().isin(["done", "rejected", "declined"])].shape[0])
with col3:
    overdue = filtered[
        (filtered["Due date"].notna()) &
        (filtered["Due date"] < pd.Timestamp.now()) &
        (~filtered["Status"].str.lower().isin(["done", "rejected", "declined"]))
    ]
    st.metric("Overdue", len(overdue))
with col4:
    st.metric("Closed Tickets", filtered[filtered["Status"].str.lower().isin(["done", "rejected", "declined"])].shape[0])

# --- Charts ---
st.subheader("Status Distribution")
st.bar_chart(filtered["Status"].value_counts())

st.subheader("Priority Distribution")
st.bar_chart(filtered["Priority"].value_counts())

# --- Time to Resolve ---
st.subheader("Time to Resolution (days)")
if "Created" in filtered.columns and "Resolution Date" in filtered.columns:
    closed = filtered[filtered["Resolution Date"].notna()]
    if not closed.empty:
        closed["Resolution Days"] = (closed["Resolution Date"] - closed["Created"]).dt.days
        st.write(f"Average: {closed['Resolution Days'].mean():.1f} days")
        st.line_chart(closed.set_index("Key")["Resolution Days"])
    else:
        st.info("No resolved tickets with resolution date.")

# --- Overdue Table ---
st.subheader("Overdue Tickets")
st.dataframe(overdue[["Key", "Summary", "Assignee", "Priority", "Due date", "Status"]], use_container_width=True)

# --- Download Option ---
st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered.to_csv(index=False),
    file_name="filtered_jira_issues.csv",
    mime="text/csv"
)
