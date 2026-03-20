import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# ------------------------------
# Page configuration
st.set_page_config(page_title="Snooker Club Sales Dashboard", layout="wide")
st.title("🎱 Snooker Downtown Sales Dashboard (PKR)")

# ------------------------------
# Helper functions
@st.cache_data
def load_data(filepath):
    df = pd.read_csv(filepath, parse_dates=['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    return df

def save_data(df, filepath):
    df.to_csv(filepath, index=False)

def recompute_day_numbers(df):
    """Recompute Day No and Days based on Date."""
    df = df.sort_values('Date').reset_index(drop=True)
    df['Day No'] = range(1, len(df) + 1)
    df['Days'] = df['Date'].dt.day_name()
    return df

def week_over_week_change(df):
    if len(df) < 14:
        return None
    df = df.sort_values('Date')
    last_7 = df.tail(7)['Sale'].sum()
    prev_7 = df.iloc[-14:-7]['Sale'].sum()
    if prev_7 == 0:
        return None
    return ((last_7 - prev_7) / prev_7) * 100

# ------------------------------
# File path
CSV_FILE = "Snooker Downtown.csv"

# Load data into session state
if 'df' not in st.session_state:
    if os.path.exists(CSV_FILE):
        st.session_state.df = load_data(CSV_FILE)
        # 👇 Add this line to ensure Day No and Days columns exist
        st.session_state.df = recompute_day_numbers(st.session_state.df)
    else:
        st.error(f"File {CSV_FILE} not found. Please make sure it's in the same directory.")
        st.stop()

# For edit tracking
if 'edit_row_index' not in st.session_state:
    st.session_state.edit_row_index = None

# ------------------------------
# Tabs
tab1, tab2 = st.tabs(["📝 Data Entry", "📈 Performance"])

# ------------------------------
# Tab 1: Data Entry with Add/Edit/Delete
with tab1:
    st.header("Manage Daily Sales")

    # --- Add / Edit Form ---
    if st.session_state.edit_row_index is not None:
        # Editing existing row
        row = st.session_state.df.loc[st.session_state.edit_row_index]
        default_date = row['Date']
        default_sale = row['Sale']
        form_title = f"✏️ Edit Sale for {default_date.strftime('%Y-%m-%d')}"
    else:
        # Adding new: default to today
        default_date = datetime.today().date()
        default_sale = 0
        form_title = "➕ Add Today's Sale"

    with st.form(key="sale_form", clear_on_submit=True):
        st.subheader(form_title)

        # Date input (can be changed, but will auto‑compute day and day number on submit)
        col1, col2, col3 = st.columns(3)
        with col1:
            sale_date = st.date_input("Date", value=default_date)
        with col2:
            sale_amount = st.number_input("Sale (PKR)", min_value=0, value=int(default_sale), step=100)
        with col3:
            # Display auto‑computed day and day number (for reference only)
            # We'll recompute properly after submit
            temp_date = pd.to_datetime(sale_date)
            st.markdown(f"**Day:** {temp_date.day_name()}")
            st.markdown("**Day No:** will be auto‑assigned")

        submitted = st.form_submit_button("Save Sale")

        if submitted:
            # Create a new row
            new_row = pd.DataFrame({
                'Date': [pd.to_datetime(sale_date)],
                'Sale': [sale_amount]
            })

            if st.session_state.edit_row_index is not None:
                # Replace the existing row
                st.session_state.df.loc[st.session_state.edit_row_index] = new_row.iloc[0]
                st.session_state.edit_row_index = None
                st.success("Sale updated!")
            else:
                # Append new row
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                st.success("Sale added!")

            # Recompute day numbers and names to keep everything consistent
            st.session_state.df = recompute_day_numbers(st.session_state.df)
            save_data(st.session_state.df, CSV_FILE)
            st.rerun()

    # --- List of Existing Entries with Edit/Delete ---
    st.divider()
    st.subheader("Existing Sales Records")

    # Prepare a display DataFrame (without index)
    display_df = st.session_state.df.copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    # Add a column for edit/delete buttons
    # We'll use columns to create buttons next to each row
    for i, row in display_df.iterrows():
        with st.container():
            cols = st.columns([2, 1, 1, 1, 1, 1])
            cols[0].write(f"**{row['Date']}**")
            cols[1].write(row['Days'])
            cols[2].write(f"Day {row['Day No']}")
            cols[3].write(f"{row['Sale']} PKR")
            if cols[4].button("✏️ Edit", key=f"edit_{i}"):
                st.session_state.edit_row_index = i
                st.rerun()
            if cols[5].button("🗑️ Delete", key=f"del_{i}"):
                st.session_state.df = st.session_state.df.drop(i).reset_index(drop=True)
                st.session_state.df = recompute_day_numbers(st.session_state.df)
                save_data(st.session_state.df, CSV_FILE)
                st.success("Entry deleted.")
                st.rerun()

# ------------------------------
# Tab 2: Performance
with tab2:
    st.header("Performance Overview")

    df_perf = st.session_state.df.copy()
    if df_perf.empty:
        st.warning("No data available.")
        st.stop()

    # Ensure proper sorting
    df_perf['Date'] = pd.to_datetime(df_perf['Date'])
    df_perf = df_perf.sort_values('Date').reset_index(drop=True)

    # Week-over-week change
    wow_change = week_over_week_change(df_perf)

    # Metrics (no $, use PKR)
    total_sales = df_perf['Sale'].sum()
    avg_daily = df_perf['Sale'].mean()
    last_7_sum = df_perf.tail(7)['Sale'].sum() if len(df_perf) >= 7 else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sales", f"{total_sales:,.0f} PKR")
    with col2:
        st.metric("Avg Daily Sale", f"{avg_daily:,.0f} PKR")
    with col3:
        if last_7_sum is not None:
            st.metric("Last 7 Days", f"{last_7_sum:,.0f} PKR")
        else:
            st.metric("Last 7 Days", "N/A")
    with col4:
        if wow_change is not None:
            st.metric("Week/Week Change", f"{wow_change:+.1f}%")
        else:
            st.metric("Week/Week Change", "Need ≥14 days")

    # --- Last Week Sales Bar Chart ---
    st.subheader("Last 7 Days Sales")
    if len(df_perf) >= 7:
        last_week_df = df_perf.tail(7).copy()
        # Format date for better x-axis labels
        last_week_df['Date_str'] = last_week_df['Date'].dt.strftime('%a, %b %d')
        fig = px.bar(last_week_df, x='Date_str', y='Sale',
                     title="Daily Sales (Last 7 Days)",
                     labels={'Sale': 'Sale (PKR)', 'Date_str': 'Date'},
                     text='Sale')
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to show last 7 days.")

    # --- Full Trend Chart (with moving average) ---
    st.subheader("Daily Sales Trend (All Data)")
    fig2 = px.line(df_perf, x='Date', y='Sale', markers=True,
                   title="Sales Over Time",
                   labels={'Sale': 'Sale (PKR)', 'Date': 'Date'})
    df_perf['MA7'] = df_perf['Sale'].rolling(7, min_periods=1).mean()
    fig2.add_scatter(x=df_perf['Date'], y=df_perf['MA7'], mode='lines',
                     name='7-day moving avg', line=dict(dash='dash'))
    st.plotly_chart(fig2, use_container_width=True)

    # --- Bar Chart by Day of Week ---
    st.subheader("Average Sales by Day of Week")
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_perf['Days'] = pd.Categorical(df_perf['Days'], categories=dow_order, ordered=True)
    dow_sales = df_perf.groupby('Days', observed=True)['Sale'].mean().reset_index()
    fig3 = px.bar(dow_sales, x='Days', y='Sale', title="Average Daily Sales by Weekday",
                  labels={'Sale': 'Avg Sale (PKR)'})
    st.plotly_chart(fig3, use_container_width=True)

    # Raw data expander
    with st.expander("Show raw data"):
        st.dataframe(df_perf, use_container_width=True)