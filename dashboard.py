import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
from supabase import create_client

# ------------------------------
# Page configuration
st.set_page_config(
    page_title="Snooker Downtown",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🎱 Snooker Downtown Sales Dashboard")

# ------------------------------
# Modern Light Theme CSS
st.markdown("""
<style>
    /* Light modern background */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }

    /* Main container */
    .main {
        background-color: transparent;
    }

    /* Glass-like cards with soft shadows */
    .stMetric, .stForm, div[data-testid="stVerticalBlock"] > div > div {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(12px);
    }

    .stMetric:hover, .stForm:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12) !important;
    }

    /* Typography */
    h1 {
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin-bottom: 0.5rem !important;
    }
    h2, h3 {
        color: #1e2937 !important;
        font-weight: 600 !important;
    }

    /* Metrics */
    .stMetric label {
        color: #64748b !important;
        font-size: 0.85rem !important;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    .stMetric .stMetricValue {
        font-size: 2.35rem !important;
        font-weight: 700 !important;
        color: #14b8a6 !important;
    }

    /* Buttons - Modern teal */
    .stButton > button {
        background: linear-gradient(90deg, #14b8a6, #0f766e) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(20, 184, 166, 0.25) !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(20, 184, 166, 0.35) !important;
        background: linear-gradient(90deg, #0f766e, #14b8a6) !important;
    }

    /* Inputs & Selects */
    .stTextInput > div, .stNumberInput > div, .stDateInput > div, 
    .stTimeInput > div, .stSelectbox > div {
        background: white !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        color: #0f172a !important;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        color: #0f172a !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: white !important;
        border-radius: 16px !important;
        padding: 6px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        color: #64748b !important;
    }
    .stTabs [aria-selected="true"] {
        background: #14b8a6 !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* Dataframes */
    .dataframe {
        background: white !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
    }
    .dataframe th {
        background: #f8fafc !important;
        color: #0f766e !important;
        font-weight: 600;
    }
    .dataframe tr:hover {
        background: #f1f5f9 !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 14px !important;
        border: 1px solid #e2e8f0 !important;
        color: #1e2937 !important;
    }

    /* Plotly charts background */
    .js-plotly-plot .plotly .main-svg {
        background: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Supabase setup
SUPABASE_URL = "https://szfwabxombagxpodppcu.supabase.co"
SUPABASE_KEY = "sb_publishable_l0RY0KvpyLUmcj2x2HHTTQ_O8bSbik0"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------
# Helper: get current time in Karachi
def get_current_time_pk():
    tz = pytz.timezone('Asia/Karachi')
    return datetime.now(tz).time()

# ------------------------------
# Sales functions (unchanged logic)
def load_sales():
    response = supabase.table("sales").select("*").order("date", desc=False).execute()
    data = response.data
    if not data:
        return pd.DataFrame(columns=["id", "date", "days", "day_no", "sale"])
    df = pd.DataFrame(data)
    df.rename(columns={"date": "Date", "days": "Days", "day_no": "Day No", "sale": "Sale"}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def save_sales(df):
    records = []
    for _, row in df.iterrows():
        records.append({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "days": row["Days"],
            "day_no": int(row["Day No"]),
            "sale": int(row["Sale"])
        })
    supabase.table("sales").delete().neq("id", 0).execute()
    for rec in records:
        supabase.table("sales").insert(rec).execute()

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
# Games functions (unchanged)
def load_games():
    response = supabase.table("games").select("*").order("date", desc=False).execute()
    data = response.data
    if not data:
        return pd.DataFrame(columns=['id', 'date', 'time', 'game', 'table', 'balls', 'minutes',
                                     'player', 'subtotal', 'discount', 'total', 'money_taken'])
    df = pd.DataFrame(data)
    df.rename(columns={
        "date": "Date", "time": "Time", "game": "Game", "table": "Table",
        "balls": "Balls", "minutes": "Minutes", "player": "Player",
        "subtotal": "Subtotal", "discount": "Discount",
        "total": "Total", "money_taken": "Money_Taken"
    }, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def save_games(df):
    records = []
    for _, row in df.iterrows():
        records.append({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "time": row["Time"],
            "game": row["Game"],
            "table": int(row["Table"]),
            "balls": int(row["Balls"]),
            "minutes": int(row["Minutes"]),
            "player": row["Player"],
            "subtotal": int(row["Subtotal"]),
            "discount": int(row["Discount"]),
            "total": int(row["Total"]),
            "money_taken": int(row["Money_Taken"])
        })
    supabase.table("games").delete().neq("id", 0).execute()
    for rec in records:
        supabase.table("games").insert(rec).execute()

# ------------------------------
# Load data into session state
if 'df' not in st.session_state:
    st.session_state.df = load_sales()
    st.session_state.df = recompute_day_numbers(st.session_state.df)

if 'edit_row_index' not in st.session_state:
    st.session_state.edit_row_index = None

if 'games_df' not in st.session_state:
    st.session_state.games_df = load_games()

if 'edit_game_index' not in st.session_state:
    st.session_state.edit_game_index = None

# Game pricing
PRICES = {"Single": 100, "Double": 150, "Century": 200}

# ------------------------------
# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Data Entry", "📈 Performance", "🎱 Games Played"])

# ------------------------------
# Tab 1: Data Entry
with tab1:
    st.header("Manage Daily Sales")

    if st.session_state.edit_row_index is not None:
        row = st.session_state.df.loc[st.session_state.edit_row_index]
        default_date = row['Date'].date()
        default_sale = row['Sale']
        form_title = f"✏️ Edit Sale – {default_date}"
    else:
        default_date = datetime.today().date()
        default_sale = 0
        form_title = "➕ Add New Sale"

    with st.form(key="sale_form", clear_on_submit=True):
        st.subheader(form_title)
        col1, col2 = st.columns(2)
        with col1:
            sale_date = st.date_input("Date", value=default_date)
        with col2:
            sale_amount = st.number_input("Sale Amount (PKR)", min_value=0, value=int(default_sale), step=500)

        temp_date = pd.to_datetime(sale_date)
        st.info(f"**Day:** {temp_date.day_name()}   |   **Day No:** Auto-assigned")

        submitted = st.form_submit_button("💾 Save Sale", use_container_width=True)

        if submitted:
            new_row = pd.DataFrame({
                'Date': [pd.to_datetime(sale_date)],
                'Sale': [sale_amount]
            })

            if st.session_state.edit_row_index is not None:
                st.session_state.df.loc[st.session_state.edit_row_index] = new_row.iloc[0]
                st.session_state.edit_row_index = None
                st.success("✅ Sale updated successfully!")
            else:
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                st.success("✅ Sale added successfully!")

            st.session_state.df = recompute_day_numbers(st.session_state.df)
            save_sales(st.session_state.df)
            st.rerun()

    st.divider()
    st.subheader("All Sales Records")

    display_df = st.session_state.df.copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    sales_list = display_df[['Date', 'Days', 'Day No', 'Sale']].copy()
    sales_list.columns = ['Date', 'Day', '#', 'Sale (PKR)']
    st.dataframe(sales_list, use_container_width=True, height=400)

    for i, row in display_df.iterrows():
        with st.expander(f"📅 {row['Date']} – {row['Days']} – {row['Sale']} PKR"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit", key=f"edit_{i}"):
                    st.session_state.edit_row_index = i
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"del_{i}"):
                    st.session_state.df = st.session_state.df.drop(i).reset_index(drop=True)
                    st.session_state.df = recompute_day_numbers(st.session_state.df)
                    save_sales(st.session_state.df)
                    st.success("Entry deleted.")
                    st.rerun()

# ------------------------------
# Tab 2: Performance
with tab2:
    st.header("Performance Overview")

    df_perf = st.session_state.df.copy()
    if df_perf.empty:
        st.warning("No sales data available yet.")
        st.stop()

    df_perf = df_perf.sort_values('Date').reset_index(drop=True)

    wow_change = week_over_week_change(df_perf)
    total_sales = df_perf['Sale'].sum()
    avg_daily = df_perf['Sale'].mean()
    last_7_sum = df_perf.tail(7)['Sale'].sum() if len(df_perf) >= 7 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sales", f"{total_sales:,.0f} PKR")
    with col2:
        st.metric("Average Daily Sale", f"{avg_daily:,.0f} PKR")
    with col3:
        st.metric("Last 7 Days", f"{last_7_sum:,.0f} PKR")
    with col4:
        if wow_change is not None:
            st.metric("Week-over-Week", f"{wow_change:+.1f}%")
        else:
            st.metric("Week-over-Week", "Need 14+ days")

    # Charts remain the same (they adapt well to light theme)
    st.subheader("Last 7 Days Sales")
    if len(df_perf) >= 7:
        last_week_df = df_perf.tail(7).copy()
        last_week_df['Date_str'] = last_week_df['Date'].dt.strftime('%a, %b %d')
        fig = px.bar(last_week_df, x='Date_str', y='Sale',
                     title="Daily Sales (Last 7 Days)",
                     labels={'Sale': 'Sale (PKR)', 'Date_str': 'Date'},
                     text='Sale')
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside', marker_color='#14b8a6')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sales Trend Over Time")
    fig2 = px.line(df_perf, x='Date', y='Sale', markers=True,
                   title="Sales Over Time",
                   labels={'Sale': 'Sale (PKR)', 'Date': 'Date'})
    df_perf['MA7'] = df_perf['Sale'].rolling(7, min_periods=1).mean()
    fig2.add_scatter(x=df_perf['Date'], y=df_perf['MA7'], mode='lines',
                     name='7-day Moving Average', line=dict(dash='dash', color='#0ea5e9'))
    fig2.update_traces(marker_color='#14b8a6', line_color='#14b8a6')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Average Sales by Day of Week")
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_perf['Days'] = pd.Categorical(df_perf['Days'], categories=dow_order, ordered=True)
    dow_sales = df_perf.groupby('Days', observed=True)['Sale'].mean().reset_index()
    fig3 = px.bar(dow_sales, x='Days', y='Sale', title="Average Sales by Weekday")
    fig3.update_traces(marker_color='#14b8a6')
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("View Raw Data"):
        st.dataframe(df_perf, use_container_width=True)

# ------------------------------
# Tab 3: Games Played
with tab3:
    st.header("Games Played – Table Recording")

    # (Your existing game form and logic – only CSS changed for light theme)
    # Keep all the game functions, session state, calculate_subtotal, etc. exactly as in your original code

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

    # Initialize session state variables (unchanged)
    for key, value in {
        'game_date': datetime.today().date(),
        'game_time': get_current_time_pk(),
        'game_type': "Single",
        'table_num': 1,
        'balls': 1,
        'minutes': 60,
        'player_name': "",
        'discount': 0,
        'money_taken': 0,
        'edit_game_index': None
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Edit mode handling (unchanged)
    if st.session_state.edit_game_index is not None:
        row = st.session_state.games_df.loc[st.session_state.edit_game_index]
        st.session_state.game_date = row['Date'].date()
        st.session_state.game_time = datetime.strptime(row['Time'], "%H:%M").time()
        st.session_state.game_type = row['Game']
        st.session_state.table_num = int(row['Table'])
        st.session_state.balls = int(row['Balls']) if row['Game'] != "Century" else 1
        st.session_state.minutes = int(row['Minutes']) if row['Game'] == "Century" else 60
        st.session_state.player_name = row.get('Player', '')
        st.session_state.discount = int(row['Discount']) if pd.notna(row['Discount']) else 0
        st.session_state.money_taken = int(row['Money_Taken']) if pd.notna(row['Money_Taken']) else 0

    def calculate_subtotal():
        if st.session_state.game_type == "Century":
            return st.session_state.minutes * 8
        else:
            ball_price_map = {1: 100, 6: 120, 10: 150, 15: 200}
            base = ball_price_map.get(st.session_state.balls, 0)
            multiplier = 2 if st.session_state.game_type == "Double" else 1
            return base * multiplier

    with st.form("game_form"):
        if st.session_state.edit_game_index is not None:
            st.subheader(f"✏️ Edit Game")
        else:
            st.subheader("➕ Add New Game")

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.game_date = st.date_input("Date", value=st.session_state.game_date)
            st.session_state.game_time = st.time_input("Time (PKT)", value=st.session_state.game_time)
            st.session_state.player_name = st.text_input("Player Name", value=st.session_state.player_name)
            st.session_state.game_type = st.selectbox("Game Type", ["Single", "Double", "Century"],
                                                      index=["Single", "Double", "Century"].index(st.session_state.game_type))
            st.session_state.table_num = st.selectbox("Table Number", [1, 2, 3],
                                                      index=st.session_state.table_num-1)

            if st.session_state.game_type == "Century":
                st.session_state.minutes = st.number_input("Minutes Played", min_value=1,
                                                           value=st.session_state.minutes, step=5)
            else:
                st.session_state.balls = st.selectbox("Balls", [1, 6, 10, 15],
                                                      index=[1,6,10,15].index(st.session_state.balls))

        with col2:
            subtotal = calculate_subtotal()
            st.markdown(f"**Subtotal:** {subtotal:,} PKR")
            st.session_state.discount = st.number_input("Discount (PKR)", min_value=0,
                                                        value=st.session_state.discount, step=10)
            total_after = subtotal - st.session_state.discount
            st.markdown(f"**Total after discount:** {total_after:,} PKR")
            st.session_state.money_taken = st.number_input("Money Taken (PKR)",
                                                           value=max(0, total_after), step=10)

        submitted = st.form_submit_button("💾 Save Game", use_container_width=True)

        if submitted:
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
                'Total': total_after,
                'Money_Taken': st.session_state.money_taken
            }

            if st.session_state.edit_game_index is not None:
                st.session_state.games_df.loc[st.session_state.edit_game_index] = new_row
                st.success("Game updated!")
                st.session_state.edit_game_index = None
            else:
                st.session_state.games_df = pd.concat([st.session_state.games_df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Game recorded!")

            save_games(st.session_state.games_df)
            reset_game_form()
            st.rerun()

    # Rest of Tab 3 (Existing Games, Today's Summary, etc.) – same as your original code
    st.divider()
    st.subheader("Existing Games")

    if st.session_state.games_df.empty:
        st.info("No games recorded yet.")
    else:
        display_games = st.session_state.games_df.copy()
        display_games['Date'] = display_games['Date'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_games[['Date', 'Time', 'Game', 'Table', 'Balls', 'Minutes', 'Player', 'Money_Taken']],
                     use_container_width=True, height=400)

        for i, row in display_games.iterrows():
            with st.expander(f"📅 {row['Date']} {row['Time']} – {row['Game']} – Table {row['Table']} – {row['Player']} – {row['Money_Taken']} PKR"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_game_{i}"):
                        st.session_state.edit_game_index = i
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_game_{i}"):
                        st.session_state.games_df = st.session_state.games_df.drop(i).reset_index(drop=True)
                        save_games(st.session_state.games_df)
                        st.success("Game deleted.")
                        st.rerun()

    # Today's Summary (unchanged logic)
    st.divider()
    st.subheader("Today's Summary")
    today = datetime.today().date()
    today_games = st.session_state.games_df[st.session_state.games_df['Date'].dt.date == today] if not st.session_state.games_df.empty else pd.DataFrame()

    if not today_games.empty:
        today_total = today_games['Money_Taken'].sum()
        st.metric("💰 Total Money Taken Today", f"{today_total:,.0f} PKR")
        st.dataframe(today_games[['Time', 'Game', 'Table', 'Balls', 'Minutes', 'Player', 'Money_Taken']],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No games recorded for today yet.")

    with st.expander("View Games from Another Day"):
        selected_date = st.date_input("Select date", value=today)
        selected_games = st.session_state.games_df[st.session_state.games_df['Date'].dt.date == selected_date] if not st.session_state.games_df.empty else pd.DataFrame()
        if not selected_games.empty:
            st.dataframe(selected_games[['Time', 'Game', 'Table', 'Balls', 'Minutes', 'Player', 'Money_Taken']],
                         use_container_width=True, hide_index=True)
            st.metric(f"Total on {selected_date}", f"{selected_games['Money_Taken'].sum():,.0f} PKR")
        else:
            st.info("No games on selected date.")