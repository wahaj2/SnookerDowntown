import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
from supabase import create_client

# ------------------------------
# PAGE CONFIG
st.set_page_config(page_title="Snooker Dashboard", layout="wide")

# ------------------------------
# MODERN UI CSS
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: #e2e8f0;
}

h1 {
    text-align: center;
    font-weight: 700;
}

[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.7);
    padding: 20px;
    border-radius: 14px;
}

.stButton button {
    background: linear-gradient(135deg, #16a34a, #22c55e);
    color: white;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
}

.stTextInput input, .stNumberInput input, .stDateInput input {
    background-color: #020617;
    color: #e2e8f0;
    border-radius: 8px;
    border: 1px solid #1e293b;
}

[data-testid="stDataFrame"] {
    background-color: #020617;
    border-radius: 10px;
}

.stTabs [aria-selected="true"] {
    color: #22c55e;
    border-bottom: 2px solid #22c55e;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# HEADER
st.markdown("""
<h1>🎱 Snooker Downtown Dashboard</h1>
<p style='text-align:center; color:#94a3b8;'>
Modern Sales & Game Tracking System
</p>
""", unsafe_allow_html=True)

# ------------------------------
# SUPABASE
SUPABASE_URL = "https://szfwabxombagxpodppcu.supabase.co"
SUPABASE_KEY = "YOUR_KEY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------
# HELPERS
def get_time():
    return datetime.now(pytz.timezone('Asia/Karachi')).time()

# ------------------------------
# LOAD SALES
def load_sales():
    res = supabase.table("sales").select("*").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["date","sale"])
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def save_sales(df):
    supabase.table("sales").delete().neq("id", 0).execute()
    for _, r in df.iterrows():
        supabase.table("sales").insert({
            "date": r["date"].strftime("%Y-%m-%d"),
            "sale": int(r["sale"])
        }).execute()

# ------------------------------
# LOAD GAMES
def load_games():
    res = supabase.table("games").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def save_games(df):
    supabase.table("games").delete().neq("id", 0).execute()
    for _, r in df.iterrows():
        supabase.table("games").insert(r.to_dict()).execute()

# ------------------------------
# SESSION
if "df" not in st.session_state:
    st.session_state.df = load_sales()

if "games" not in st.session_state:
    st.session_state.games = load_games()

# ------------------------------
# TABS
tab1, tab2, tab3 = st.tabs(["Data Entry", "Performance", "Games"])

# ==============================
# TAB 1 — SALES
# ==============================
with tab1:
    st.subheader("Add Sale")

    with st.form("sale_form"):
        date = st.date_input("Date", value=datetime.today())
        sale = st.number_input("Sale", min_value=0)

        if st.form_submit_button("Save"):
            new = pd.DataFrame({"date":[pd.to_datetime(date)],"sale":[sale]})
            st.session_state.df = pd.concat([st.session_state.df,new],ignore_index=True)
            save_sales(st.session_state.df)
            st.success("Saved")
            st.rerun()

    st.divider()
    st.subheader("Records")

    if not st.session_state.df.empty:
        df_show = st.session_state.df.copy()
        df_show['date'] = df_show['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_show, use_container_width=True)

# ==============================
# TAB 2 — PERFORMANCE
# ==============================
with tab2:
    st.subheader("Performance")

    df = st.session_state.df.copy()
    if df.empty:
        st.warning("No data")
        st.stop()

    total = df['sale'].sum()
    avg = df['sale'].mean()

    c1, c2 = st.columns(2)
    c1.metric("Total Sales", f"{total:,.0f} PKR")
    c2.metric("Average", f"{avg:,.0f} PKR")

    fig = px.line(df, x="date", y="sale", markers=True)

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# TAB 3 — GAMES
# ==============================
with tab3:
    st.subheader("Record Game")

    with st.form("game_form"):
        date = st.date_input("Date", value=datetime.today())
        time = st.time_input("Time", value=get_time())
        player = st.text_input("Player Name")

        game = st.selectbox("Game Type", ["Single", "Double", "Century"])
        table = st.selectbox("Table", [1,2,3])

        balls = st.selectbox("Balls", [1,6,10,15])
        minutes = st.number_input("Minutes", min_value=0)

        discount = st.number_input("Discount", min_value=0)

        # Pricing
        if game == "Century":
            subtotal = minutes * 8
        else:
            price_map = {1:100,6:120,10:150,15:200}
            subtotal = price_map[balls]
            if game == "Double":
                subtotal *= 2

        total = subtotal - discount

        st.markdown(f"**Subtotal:** {subtotal}")
        st.markdown(f"**Total:** {total}")

        if st.form_submit_button("Save Game"):
            new = pd.DataFrame([{
                "date": str(date),
                "time": str(time),
                "game": game,
                "table": table,
                "player": player,
                "balls": balls,
                "minutes": minutes,
                "total": total
            }])

            st.session_state.games = pd.concat([st.session_state.games,new],ignore_index=True)
            save_games(st.session_state.games)
            st.success("Game saved")
            st.rerun()

    st.divider()
    st.subheader("Games List")

    if not st.session_state.games.empty:
        st.dataframe(st.session_state.games, use_container_width=True)