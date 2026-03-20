import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import pytz

# ------------------------------
# Page configuration
st.set_page_config(page_title="Snooker Club Sales Dashboard", layout="wide")
st.title("🎱 Snooker Downtown Sales Dashboard (PKR)")

# ------------------------------
# Constants
CSV_FILE = "Snooker Downtown.csv"
GAMES_FILE = "games.csv"

# Game types (used for dropdown)
PRICES = {
    "Single": 100,
    "Double": 150,
    "Century": 200
}

# ------------------------------
# Helper functions for sales
@st.cache_data
def load_data(filepath):
    df = pd.read_csv(filepath, parse_dates=['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    return df

def save_data(df, filepath):
    df.to_csv(filepath, index=False)

def recompute_day_numbers(df):
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
# Helper functions for games
def load_games():
    if os.path.exists(GAMES_FILE):
        df = pd.read_csv(GAMES_FILE, parse_dates=['Date'])
        return df
    else:
        return pd.DataFrame(columns=[
            'Date', 'Time', 'Game', 'Table', 'Balls', 'Minutes',
            'Player', 'Subtotal', 'Discount', 'Total', 'Money_Taken'
        ])

def save_games(df):
    df.to_csv(GAMES_FILE, index=False)

def get_current_time_pk():
    tz = pytz.timezone('Asia/Karachi')
    return datetime.now(tz).time()

# ------------------------------
# Load sales data
if 'df' not in st.session_state:
    if os.path.exists(CSV_FILE):
        st.session_state.df = load_data(CSV_FILE)
        st.session_state.df = recompute_day_numbers(st.session_state.df)
    else:
        st.error(f"File {CSV_FILE} not found. Please make sure it's in the same directory.")
        st.stop()

if 'edit_row_index' not in st.session_state:
    st.session_state.edit_row_index = None

# ------------------------------
# Load games data
if 'games_df' not in st.session_state:
    st.session_state.games_df = load_games()

if 'edit_game_index' not in st.session_state:
    st.session_state.edit_game_index = None

# ------------------------------
# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Data Entry", "📈 Performance", "🎱 Games Played"])

# ------------------------------
# Tab 1: Data Entry (same as before)
with tab1:
    st.header("Manage Daily Sales")

    # Add / Edit Form
    if st.session_state.edit_row_index is not None:
        row = st.session_state.df.loc[st.session_state.edit_row_index]
        default_date = row['Date']
        default_sale = row['Sale']
        form_title = f"✏️ Edit Sale for {default_date.strftime('%Y-%m-%d')}"
    else:
        default_date = datetime.today().date()
        default_sale = 0
        form_title = "➕ Add Today's Sale"

    with st.form(key="sale_form", clear_on_submit=True):
        st.subheader(form_title)

        col1, col2, col3 = st.columns(3)
        with col1:
            sale_date = st.date_input("Date", value=default_date)
        with col2:
            sale_amount = st.number_input("Sale (PKR)", min_value=0, value=int(default_sale), step=100)
        with col3:
            temp_date = pd.to_datetime(sale_date)
            st.markdown(f"**Day:** {temp_date.day_name()}")
            st.markdown("**Day No:** will be auto‑assigned")

        submitted = st.form_submit_button("Save Sale")

        if submitted:
            new_row = pd.DataFrame({
                'Date': [pd.to_datetime(sale_date)],
                'Sale': [sale_amount]
            })

            if st.session_state.edit_row_index is not None:
                st.session_state.df.loc[st.session_state.edit_row_index] = new_row.iloc[0]
                st.session_state.edit_row_index = None
                st.success("Sale updated!")
            else:
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                st.success("Sale added!")

            st.session_state.df = recompute_day_numbers(st.session_state.df)
            save_data(st.session_state.df, CSV_FILE)
            st.rerun()

    # List of Existing Entries
    st.divider()
    st.subheader("Existing Sales Records")

    display_df = st.session_state.df.copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
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

    df_perf['Date'] = pd.to_datetime(df_perf['Date'])
    df_perf = df_perf.sort_values('Date').reset_index(drop=True)

    wow_change = week_over_week_change(df_perf)

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

    # Last 7 Days Bar Chart
    st.subheader("Last 7 Days Sales")
    if len(df_perf) >= 7:
        last_week_df = df_perf.tail(7).copy()
        last_week_df['Date_str'] = last_week_df['Date'].dt.strftime('%a, %b %d')
        fig = px.bar(last_week_df, x='Date_str', y='Sale',
                     title="Daily Sales (Last 7 Days)",
                     labels={'Sale': 'Sale (PKR)', 'Date_str': 'Date'},
                     text='Sale')
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to show last 7 days.")

    # Full Trend Chart
    st.subheader("Daily Sales Trend (All Data)")
    fig2 = px.line(df_perf, x='Date', y='Sale', markers=True,
                   title="Sales Over Time",
                   labels={'Sale': 'Sale (PKR)', 'Date': 'Date'})
    df_perf['MA7'] = df_perf['Sale'].rolling(7, min_periods=1).mean()
    fig2.add_scatter(x=df_perf['Date'], y=df_perf['MA7'], mode='lines',
                     name='7-day moving avg', line=dict(dash='dash'))
    st.plotly_chart(fig2, use_container_width=True)

    # Bar Chart by Day of Week
    st.subheader("Average Sales by Day of Week")
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_perf['Days'] = pd.Categorical(df_perf['Days'], categories=dow_order, ordered=True)
    dow_sales = df_perf.groupby('Days', observed=True)['Sale'].mean().reset_index()
    fig3 = px.bar(dow_sales, x='Days', y='Sale', title="Average Daily Sales by Weekday",
                  labels={'Sale': 'Avg Sale (PKR)'})
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("Show raw data"):
        st.dataframe(df_perf, use_container_width=True)

# ------------------------------
# Tab 3: Games Played (fixed)
with tab3:
    st.header("Games Played – Per‑Table Recording")

    # Helper to get current Islamabad time
    def get_current_time_pk():
        tz = pytz.timezone('Asia/Karachi')
        return datetime.now(tz).time()

    # Reset form function
    def reset_game_form():
        st.session_state.game_date = datetime.today().date()
        st.session_state.game_time = get_current_time_pk()
        st.session_state.game_type = "Single"
        st.session_state.table_num = 1
        st.session_state.balls = 1
        st.session_state.minutes = 60
        st.session_state.player_name = ""
        st.session_state.discount = 0
        st.session_state.money_taken = 0
        st.session_state.edit_game_index = None

    # Initialize session state for form fields if not exists
    if 'game_date' not in st.session_state:
        st.session_state.game_date = datetime.today().date()
    if 'game_time' not in st.session_state:
        st.session_state.game_time = get_current_time_pk()
    if 'game_type' not in st.session_state:
        st.session_state.game_type = "Single"
    if 'table_num' not in st.session_state:
        st.session_state.table_num = 1
    if 'balls' not in st.session_state:
        st.session_state.balls = 1
    if 'minutes' not in st.session_state:
        st.session_state.minutes = 60
    if 'player_name' not in st.session_state:
        st.session_state.player_name = ""
    if 'discount' not in st.session_state:
        st.session_state.discount = 0
    if 'money_taken' not in st.session_state:
        st.session_state.money_taken = 0
    if 'edit_game_index' not in st.session_state:
        st.session_state.edit_game_index = None

    # If editing, load the row data into session state (convert any numpy ints to Python int)
    if st.session_state.edit_game_index is not None:
        row = st.session_state.games_df.loc[st.session_state.edit_game_index]
        st.session_state.game_date = row['Date'].date()
        st.session_state.game_time = datetime.strptime(row['Time'], "%H:%M").time()
        st.session_state.game_type = row['Game']
        st.session_state.table_num = int(row['Table'])   # convert to Python int
        st.session_state.balls = int(row['Balls'])       # convert
        st.session_state.minutes = int(row['Minutes'])   # convert
        st.session_state.player_name = row.get('Player', '')
        st.session_state.discount = int(row['Discount']) if pd.notna(row['Discount']) else 0
        st.session_state.money_taken = int(row['Money_Taken']) if pd.notna(row['Money_Taken']) else 0

    # Dynamic price calculation
    def calculate_subtotal():
        if st.session_state.game_type == "Century":
            return st.session_state.minutes * 8
        else:
            ball_price_map = {1: 100, 6: 120, 10: 150, 15: 200}
            base = ball_price_map.get(st.session_state.balls, 0)
            multiplier = 2 if st.session_state.game_type == "Double" else 1
            return base * multiplier

    # --- Form for adding/editing a game ---
    with st.form("game_form"):
        if st.session_state.edit_game_index is not None:
            st.subheader(f"✏️ Edit Game (ID {st.session_state.edit_game_index})")
        else:
            st.subheader("➕ Add New Game")

        col1, col2 = st.columns(2)

        with col1:
            st.session_state.game_date = st.date_input("Date", value=st.session_state.game_date)
            st.session_state.game_time = st.time_input("Time (Islamabad PKT)", value=st.session_state.game_time)
            st.session_state.player_name = st.text_input("Player Name", value=st.session_state.player_name)

            game_type_options = list(PRICES.keys())
            st.session_state.game_type = st.selectbox("Game Type", game_type_options,
                                                      index=game_type_options.index(st.session_state.game_type))

            st.session_state.table_num = st.selectbox("Table Number", [1, 2, 3],
                                                      index=st.session_state.table_num-1)

            if st.session_state.game_type == "Century":
                st.session_state.minutes = st.number_input("Minutes Played", min_value=1,
                                                           value=st.session_state.minutes, step=1)
            else:
                ball_options = [1, 6, 10, 15]
                st.session_state.balls = st.selectbox("Balls", ball_options,
                                                      index=ball_options.index(st.session_state.balls))

        with col2:
            subtotal = calculate_subtotal()
            st.markdown(f"**Subtotal:** {subtotal} PKR")
            st.session_state.discount = st.number_input("Discount (PKR)", min_value=0,
                                                        value=st.session_state.discount, step=10)
            total_after_discount = subtotal - st.session_state.discount
            st.markdown(f"**Total after discount:** {total_after_discount} PKR")
            st.session_state.money_taken = st.number_input("Money Taken (PKR)", min_value=0,
                                                           value=max(0, total_after_discount), step=10)

        submitted = st.form_submit_button("Save Game")

        if submitted:
            # Build the new row
            new_row = {
                'Date': pd.to_datetime(st.session_state.game_date),
                'Time': st.session_state.game_time.strftime("%H:%M"),
                'Game': st.session_state.game_type,
                'Table': st.session_state.table_num,
                'Balls': st.session_state.balls if st.session_state.game_type != "Century" else 0,
                'Minutes': st.session_state.minutes if st.session_state.game_type == "Century" else 0,
                'Player': st.session_state.player_name,
                'Subtotal': subtotal,
                'Discount': st.session_state.discount,
                'Total': total_after_discount,
                'Money_Taken': st.session_state.money_taken
            }

            if st.session_state.edit_game_index is not None:
                st.session_state.games_df.loc[st.session_state.edit_game_index] = new_row
                st.success("Game updated!")
                st.session_state.edit_game_index = None
            else:
                new_df = pd.DataFrame([new_row])
                st.session_state.games_df = pd.concat([st.session_state.games_df, new_df], ignore_index=True)
                st.success("Game recorded!")

            # Save to CSV and reset the form
            save_games(st.session_state.games_df)
            reset_game_form()
            st.rerun()

    # --- List of existing games (with edit/delete) ---
    st.divider()
    st.subheader("Existing Games")

    if st.session_state.games_df.empty:
        st.info("No games recorded yet.")
    else:
        display_games = st.session_state.games_df.copy()
        display_games['Date'] = display_games['Date'].dt.strftime('%Y-%m-%d')

        for i, row in display_games.iterrows():
            with st.container():
                cols = st.columns([1, 1, 1, 1, 1, 1, 1.5, 1, 1, 1])
                cols[0].write(f"**{row['Date']}**")
                cols[1].write(row['Time'])
                cols[2].write(row['Game'])
                cols[3].write(f"T{row['Table']}")
                cols[4].write(row['Balls'] if row['Balls'] != 0 else "-")
                cols[5].write(row['Minutes'] if row['Minutes'] != 0 else "-")
                cols[6].write(row.get('Player', ''))
                cols[7].write(f"{row['Money_Taken']} PKR")
                if cols[8].button("✏️ Edit", key=f"edit_game_{i}"):
                    st.session_state.edit_game_index = i
                    st.rerun()
                if cols[9].button("🗑️ Delete", key=f"del_game_{i}"):
                    st.session_state.games_df = st.session_state.games_df.drop(i).reset_index(drop=True)
                    save_games(st.session_state.games_df)
                    if st.session_state.edit_game_index == i:
                        st.session_state.edit_game_index = None
                    st.success("Game deleted.")
                    st.rerun()

    # --- Today's summary ---
    st.divider()
    st.subheader("Today's Summary")

    today = datetime.today().date()
    today_games = st.session_state.games_df[
        st.session_state.games_df['Date'].dt.date == today
    ] if not st.session_state.games_df.empty else pd.DataFrame()

    if not today_games.empty:
        today_total = today_games['Money_Taken'].sum()
        st.metric("💰 Total Money Taken Today", f"{today_total:,.0f} PKR")
        st.dataframe(
            today_games[['Time', 'Game', 'Table', 'Balls', 'Minutes', 'Player', 'Subtotal', 'Discount', 'Total', 'Money_Taken']],
            use_container_width=True,
            hide_index=True
        )

        # Breakdown by table
        st.subheader("Breakdown by Table (Today)")
        table_totals = today_games.groupby('Table')['Money_Taken'].sum().reset_index()
        fig_table = px.bar(table_totals, x='Table', y='Money_Taken',
                           title="Money Taken per Table (Today)",
                           labels={'Money_Taken': 'PKR'})
        st.plotly_chart(fig_table, use_container_width=True)
    else:
        st.info("No games recorded for today yet.")

    # --- View other days ---
    with st.expander("View games from another day"):
        selected_date = st.date_input("Select date to view", value=today)
        selected_games = st.session_state.games_df[
            st.session_state.games_df['Date'].dt.date == selected_date
        ] if not st.session_state.games_df.empty else pd.DataFrame()

        if not selected_games.empty:
            st.dataframe(
                selected_games[['Time', 'Game', 'Table', 'Balls', 'Minutes', 'Player', 'Subtotal', 'Discount', 'Total', 'Money_Taken']],
                use_container_width=True,
                hide_index=True
            )
            st.metric(f"Total money taken on {selected_date.strftime('%Y-%m-%d')}",
                      f"{selected_games['Money_Taken'].sum():,.0f} PKR")
        else:
            st.info("No games recorded for that date.")