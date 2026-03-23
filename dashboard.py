import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
from supabase import create_client

# ------------------------------
# Page configuration
st.set_page_config(page_title="Snooker Club Sales Dashboard", layout="wide")
st.title("🎱 Snooker Downtown Sales Dashboard (PKR)")

# ------------------------------
# Custom CSS for dark blue professional theme
st.markdown("""
<style>
    /* Global styles */
    .main {
        background-color: #0a192f;
    }
    
    /* Override Streamlit's default background */
    .stApp {
        background-color: #0a192f;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-weight: 600;
        color: #e6f1ff;
    }
    
    /* Metric cards */
    .stMetric {
        background-color: #112240;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid #1e3a5f;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.4);
    }
    .stMetric label {
        font-size: 0.875rem;
        font-weight: 500;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .stMetric .stMetricValue {
        font-size: 2rem;
        font-weight: 700;
        color: #64ffda;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #1e6f5c;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.2s, transform 0.1s;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #178b74;
        border: none;
        transform: scale(1.02);
    }
    .stButton button:active {
        transform: scale(0.98);
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        background-color: #112240;
        border-radius: 12px;
        border: 1px solid #1e3a5f;
        padding: 0.75rem 1rem;
        font-weight: 500;
        color: #e6f1ff;
        margin-bottom: 0.5rem;
    }
    .streamlit-expanderHeader:hover {
        background-color: #1a2f4e;
    }
    
    /* Dataframes */
    .dataframe {
        font-size: 0.875rem;
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        background-color: #112240;
        color: #e6f1ff;
        border-radius: 12px;
        overflow: hidden;
    }
    .dataframe th {
        background-color: #0a2a3b;
        color: #64ffda;
        font-weight: 600;
        padding: 0.75rem;
        border-bottom: 2px solid #1e3a5f;
    }
    .dataframe td {
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid #1e3a5f;
        color: #ccd6f6;
    }
    .dataframe tr:hover {
        background-color: #1a2f4e;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: #112240;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        border: 1px solid #1e3a5f;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        color: #8892b0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e6f5c;
        color: #ffffff;
    }
    
    /* Forms */
    .stForm {
        background-color: #112240;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #1e3a5f;
        margin-bottom: 1.5rem;
    }
    .stForm [data-baseweb="input"], .stForm [data-baseweb="select"], .stForm [data-baseweb="textarea"] {
        border-radius: 8px;
        border: 1px solid #1e3a5f;
        background-color: #0a192f;
        color: #e6f1ff;
    }
    .stForm input, .stForm textarea, .stForm select {
        background-color: #0a192f;
        color: #e6f1ff;
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #1e3a5f, transparent);
    }
    
    /* Info/Warning boxes */
    .stAlert {
        border-radius: 12px;
        border-left-width: 4px;
        background-color: #112240;
        color: #e6f1ff;
    }
    .stAlert .stAlertContent {
        color: #e6f1ff;
    }
    
    /* Selectbox, date input, etc */
    .stSelectbox, .stDateInput, .stNumberInput, .stTextInput, .stTimeInput {
        background-color: #0a192f;
        color: #e6f1ff;
    }
    .stSelectbox div, .stDateInput div, .stNumberInput div, .stTextInput div, .stTimeInput div {
        background-color: #0a192f;
        color: #e6f1ff;
    }
    
    /* Metric container adjustments */
    div[data-testid="stMetricValue"] {
        color: #64ffda;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
        .stMetric {
            margin-bottom: 1rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .stButton button {
            min-width: 44px;
            min-height: 44px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Supabase setup
SUPABASE_URL = "https://szfwabxombagxpodppcu.supabase.co"
SUPABASE_KEY = "sb_publishable_l0RY0KvpyLUmcj2x2HHTTQ_O8bSbik0"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------
# Helper: get current time in Islamabad
def get_current_time_pk():
    tz = pytz.timezone('Asia/Karachi')
    return datetime.now(tz).time()

# ------------------------------
# Sales functions
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
# Games functions
def load_games():
    response = supabase.table("games").select("*").order("date", desc=False).execute()
    data = response.data
    if not data:
        return pd.DataFrame(columns=[
            'id', 'date', 'time', 'game', 'table', 'balls', 'minutes',
            'player', 'subtotal', 'discount', 'total', 'money_taken'
        ])
    df = pd.DataFrame(data)
    df.rename(columns={
        "date": "Date",
        "time": "Time",
        "game": "Game",
        "table": "Table",
        "balls": "Balls",
        "minutes": "Minutes",
        "player": "Player",
        "subtotal": "Subtotal",
        "discount": "Discount",
        "total": "Total",
        "money_taken": "Money_Taken"
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
# Load initial data into session state
if 'df' not in st.session_state:
    st.session_state.df = load_sales()
    st.session_state.df = recompute_day_numbers(st.session_state.df)

if 'edit_row_index' not in st.session_state:
    st.session_state.edit_row_index = None

if 'games_df' not in st.session_state:
    st.session_state.games_df = load_games()

if 'edit_game_index' not in st.session_state:
    st.session_state.edit_game_index = None

# ------------------------------
# Game type pricing
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
        default_date = row['Date']
        default_sale = row['Sale']
        form_title = f"✏️ Edit Sale for {default_date.strftime('%Y-%m-%d')}"
    else:
        default_date = datetime.today().date()
        default_sale = 0
        form_title = "➕ Add Today's Sale"

    with st.form(key="sale_form", clear_on_submit=True):
        st.subheader(form_title)

        col1, col2 = st.columns(2)
        with col1:
            sale_date = st.date_input("Date", value=default_date)
        with col2:
            sale_amount = st.number_input("Sale (PKR)", min_value=0, value=int(default_sale), step=100)

        temp_date = pd.to_datetime(sale_date)
        st.markdown(f"**Day:** {temp_date.day_name()} &nbsp;&nbsp; **Day No:** will be auto‑assigned")

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
            save_sales(st.session_state.df)
            st.rerun()

    st.divider()
    st.subheader("Existing Sales Records")

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

    st.subheader("Last 7 Days Sales")
    if len(df_perf) >= 7:
        last_week_df = df_perf.tail(7).copy()
        last_week_df['Date_str'] = last_week_df['Date'].dt.strftime('%a, %b %d')
        fig = px.bar(last_week_df, x='Date_str', y='Sale',
                     title="Daily Sales (Last 7 Days)",
                     labels={'Sale': 'Sale (PKR)', 'Date_str': 'Date'},
                     text='Sale')
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside',
                          marker_color='#64ffda')
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20),
                          plot_bgcolor='rgba(17,34,64,0.5)',
                          paper_bgcolor='rgba(17,34,64,0.5)',
                          font=dict(color='#e6f1ff'),
                          title_font_color='#e6f1ff')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to show last 7 days.")

    st.subheader("Daily Sales Trend (All Data)")
    fig2 = px.line(df_perf, x='Date', y='Sale', markers=True,
                   title="Sales Over Time",
                   labels={'Sale': 'Sale (PKR)', 'Date': 'Date'})
    df_perf['MA7'] = df_perf['Sale'].rolling(7, min_periods=1).mean()
    fig2.add_scatter(x=df_perf['Date'], y=df_perf['MA7'], mode='lines',
                     name='7-day moving avg', line=dict(dash='dash', color='#ffb86b'))
    fig2.update_traces(marker_color='#64ffda', line_color='#64ffda')
    fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20),
                       plot_bgcolor='rgba(17,34,64,0.5)',
                       paper_bgcolor='rgba(17,34,64,0.5)',
                       font=dict(color='#e6f1ff'),
                       title_font_color='#e6f1ff')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Average Sales by Day of Week")
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_perf['Days'] = pd.Categorical(df_perf['Days'], categories=dow_order, ordered=True)
    dow_sales = df_perf.groupby('Days', observed=True)['Sale'].mean().reset_index()
    fig3 = px.bar(dow_sales, x='Days', y='Sale', title="Average Daily Sales by Weekday",
                  labels={'Sale': 'Avg Sale (PKR)'})
    fig3.update_traces(marker_color='#64ffda')
    fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20),
                       plot_bgcolor='rgba(17,34,64,0.5)',
                       paper_bgcolor='rgba(17,34,64,0.5)',
                       font=dict(color='#e6f1ff'),
                       title_font_color='#e6f1ff')
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("Show raw data"):
        st.dataframe(df_perf, use_container_width=True)

# ------------------------------
# Tab 3: Games Played
with tab3:
    st.header("Games Played – Per‑Table Recording")

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

    if st.session_state.edit_game_index is not None:
        row = st.session_state.games_df.loc[st.session_state.edit_game_index]
        st.session_state.game_date = row['Date'].date()
        st.session_state.game_time = datetime.strptime(row['Time'], "%H:%M").time()
        st.session_state.game_type = row['Game']
        st.session_state.table_num = int(row['Table'])
        st.session_state.balls = int(row['Balls'])
        st.session_state.minutes = int(row['Minutes'])
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

            save_games(st.session_state.games_df)
            reset_game_form()
            st.rerun()

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
            with st.expander(f"📅 {row['Date']} {row['Time']} – {row['Game']} – T{row['Table']} – {row['Player']} – {row['Money_Taken']} PKR"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_game_{i}"):
                        st.session_state.edit_game_index = i
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_game_{i}"):
                        st.session_state.games_df = st.session_state.games_df.drop(i).reset_index(drop=True)
                        save_games(st.session_state.games_df)
                        if st.session_state.edit_game_index == i:
                            st.session_state.edit_game_index = None
                        st.success("Game deleted.")
                        st.rerun()

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
            today_games[['Time', 'Game', 'Table', 'Balls', 'Minutes', 'Player', 'Money_Taken']],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Breakdown by Table (Today)")
        table_totals = today_games.groupby('Table')['Money_Taken'].sum().reset_index()
        fig_table = px.bar(table_totals, x='Table', y='Money_Taken',
                           title="Money Taken per Table (Today)",
                           labels={'Money_Taken': 'PKR'})
        fig_table.update_traces(marker_color='#64ffda')
        fig_table.update_layout(margin=dict(l=20, r=20, t=40, b=20),
                                plot_bgcolor='rgba(17,34,64,0.5)',
                                paper_bgcolor='rgba(17,34,64,0.5)',
                                font=dict(color='#e6f1ff'),
                                title_font_color='#e6f1ff')
        st.plotly_chart(fig_table, use_container_width=True)
    else:
        st.info("No games recorded for today yet.")

    with st.expander("View games from another day"):
        selected_date = st.date_input("Select date to view", value=today)
        selected_games = st.session_state.games_df[
            st.session_state.games_df['Date'].dt.date == selected_date
        ] if not st.session_state.games_df.empty else pd.DataFrame()

        if not selected_games.empty:
            st.dataframe(
                selected_games[['Time', 'Game', 'Table', 'Balls', 'Minutes', 'Player', 'Money_Taken']],
                use_container_width=True,
                hide_index=True
            )
            st.metric(f"Total money taken on {selected_date.strftime('%Y-%m-%d')}",
                      f"{selected_games['Money_Taken'].sum():,.0f} PKR")
        else:
            st.info("No games recorded for that date.")