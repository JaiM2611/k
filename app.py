"""
app.py — The Interface  (Professional Redesign)
================================================
Author : Jai (CS Student)
Purpose: Industry-level Streamlit dashboard for IPL 2026 data.
         Displays points table, player stats, injury news, and pitch reports
         with a modern dark theme, Plotly charts, and professional card layouts.

Run with:
    streamlit run app.py
"""

import json
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_manager import load_from_json, refresh_data

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL 2026 · Match Predictor & Tracker",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── IPL Team Branding ─────────────────────────────────────────────────────────
TEAM_META = {
    "MI":   {"full": "Mumbai Indians",          "primary": "#004BA0", "secondary": "#1A73E8", "emoji": "💙"},
    "CSK":  {"full": "Chennai Super Kings",     "primary": "#F9CD28", "secondary": "#F5A623", "emoji": "💛"},
    "RCB":  {"full": "Royal Challengers Bengaluru", "primary": "#D71920", "secondary": "#FF4444", "emoji": "❤️"},
    "KKR":  {"full": "Kolkata Knight Riders",   "primary": "#3A225D", "secondary": "#7B2D8B", "emoji": "💜"},
    "SRH":  {"full": "Sunrisers Hyderabad",     "primary": "#F26522", "secondary": "#FF8C00", "emoji": "🧡"},
    "RR":   {"full": "Rajasthan Royals",        "primary": "#E91E8C", "secondary": "#FF69B4", "emoji": "🩷"},
    "DC":   {"full": "Delhi Capitals",          "primary": "#17479E", "secondary": "#EF1B23", "emoji": "💙"},
    "GT":   {"full": "Gujarat Titans",          "primary": "#1B4A7A", "secondary": "#A0C4FF", "emoji": "🔵"},
    "LSG":  {"full": "Lucknow Super Giants",    "primary": "#1BAADF", "secondary": "#A0E1E1", "emoji": "🩵"},
    "PBKS": {"full": "Punjab Kings",            "primary": "#AF1E2E", "secondary": "#DD3A4B", "emoji": "❤️"},
}

def get_team_color(team_abbr: str) -> str:
    return TEAM_META.get(team_abbr, {}).get("primary", "#FF6B35")

def get_team_full(team_abbr: str) -> str:
    return TEAM_META.get(team_abbr, {}).get("full", team_abbr)

def get_team_emoji(team_abbr: str) -> str:
    return TEAM_META.get(team_abbr, {}).get("emoji", "🏏")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* ── Import Google Fonts ── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ── Base & Reset ── */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        /* ── Hero Header ── */
        .hero-header {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 30%, #0a1a2e 60%, #0a0a1a 100%);
            border: 1px solid rgba(255, 107, 53, 0.3);
            border-radius: 20px;
            padding: 2.5rem 2rem;
            text-align: center;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        .hero-header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 50% 50%, rgba(255, 107, 53, 0.08) 0%, transparent 60%);
            animation: pulse-glow 4s ease-in-out infinite;
        }

        @keyframes pulse-glow {
            0%, 100% { opacity: 0.5; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.05); }
        }

        .hero-title {
            font-size: clamp(1.8rem, 4vw, 3rem);
            font-weight: 900;
            background: linear-gradient(135deg, #FF6B35, #FF9A5C, #FFD700);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
            position: relative;
            z-index: 1;
        }

        .hero-subtitle {
            font-size: 1rem;
            color: rgba(255,255,255,0.55);
            font-weight: 400;
            letter-spacing: 0.5px;
            position: relative;
            z-index: 1;
        }

        .hero-badges {
            display: flex;
            gap: 0.75rem;
            justify-content: center;
            margin-top: 1rem;
            flex-wrap: wrap;
            position: relative;
            z-index: 1;
        }

        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.3px;
        }

        .badge-orange {
            background: rgba(255, 107, 53, 0.2);
            color: #FF8C5A;
            border: 1px solid rgba(255, 107, 53, 0.4);
        }

        .badge-green {
            background: rgba(0, 255, 150, 0.15);
            color: #00FF96;
            border: 1px solid rgba(0, 255, 150, 0.3);
        }

        .badge-blue {
            background: rgba(0, 200, 255, 0.15);
            color: #5ACFFF;
            border: 1px solid rgba(0, 200, 255, 0.3);
        }

        /* ── Match Banner ── */
        .match-banner {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 4px solid #FF6B35;
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.25rem;
        }

        .match-banner-live {
            border-left-color: #FF4444;
            animation: border-pulse 1.5s ease-in-out infinite;
        }

        @keyframes border-pulse {
            0%, 100% { border-left-color: #FF4444; }
            50% { border-left-color: #FF8888; }
        }

        .match-teams {
            font-size: clamp(1.1rem, 2.5vw, 1.6rem);
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.3px;
        }

        .match-info {
            font-size: 0.88rem;
            color: rgba(255,255,255,0.5);
            margin-top: 0.35rem;
        }

        .live-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #FF4444;
            border-radius: 50%;
            margin-right: 6px;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.2; }
        }

        .status-pill {
            display: inline-block;
            padding: 0.2rem 0.7rem;
            border-radius: 50px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        .status-live    { background: rgba(255,68,68,0.2);   color: #FF6B6B; border: 1px solid rgba(255,68,68,0.4); }
        .status-upcoming{ background: rgba(255,200,0,0.15);  color: #FFD700; border: 1px solid rgba(255,200,0,0.3); }
        .status-completed{background: rgba(0,200,100,0.15); color: #00C864; border: 1px solid rgba(0,200,100,0.3); }

        /* ── Stat Cards ── */
        .stat-card {
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 1.25rem 1rem;
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
            cursor: default;
        }

        .stat-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 107, 53, 0.3);
        }

        .stat-icon {
            font-size: 1.8rem;
            margin-bottom: 0.4rem;
        }

        .stat-value {
            font-size: 1.7rem;
            font-weight: 800;
            color: #FF6B35;
            line-height: 1;
        }

        .stat-label {
            font-size: 0.78rem;
            color: rgba(255,255,255,0.45);
            font-weight: 500;
            margin-top: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* ── Section Titles ── */
        .section-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .section-title::after {
            content: '';
            flex: 1;
            height: 1px;
            background: linear-gradient(to right, rgba(255,107,53,0.4), transparent);
            margin-left: 0.5rem;
        }

        /* ── Team Rank Row ── */
        .rank-card {
            background: linear-gradient(135deg, #161b22, #0d1117);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 12px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: all 0.2s ease;
        }

        .rank-card:hover {
            border-color: rgba(255,107,53,0.25);
            transform: translateX(4px);
        }

        .rank-num {
            font-size: 1.1rem;
            font-weight: 800;
            color: rgba(255,255,255,0.3);
            min-width: 24px;
        }

        .rank-num.top { color: #FFD700; }

        .team-abbr {
            font-size: 1rem;
            font-weight: 800;
            min-width: 48px;
        }

        .team-full {
            font-size: 0.82rem;
            color: rgba(255,255,255,0.45);
        }

        .rank-pts {
            margin-left: auto;
            font-size: 1.1rem;
            font-weight: 800;
            color: #ffffff;
        }

        .rank-nrr {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.4);
            min-width: 60px;
            text-align: right;
        }

        .pts-bar-outer {
            flex: 1;
            background: rgba(255,255,255,0.06);
            border-radius: 4px;
            height: 6px;
            min-width: 80px;
            max-width: 200px;
        }

        .pts-bar-inner {
            height: 100%;
            border-radius: 4px;
        }

        /* ── Player Card ── */
        .player-card {
            background: linear-gradient(135deg, #161b22, #0d1117);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .player-rank {
            font-size: 1.1rem;
            font-weight: 800;
            color: rgba(255,255,255,0.3);
            min-width: 24px;
        }

        .player-name {
            font-size: 0.95rem;
            font-weight: 600;
            color: #ffffff;
        }

        .player-team {
            font-size: 0.78rem;
            color: rgba(255,255,255,0.45);
        }

        .player-stat {
            margin-left: auto;
            font-size: 1.2rem;
            font-weight: 800;
            color: #FF6B35;
        }

        /* ── Injury Cards ── */
        .injury-card {
            background: linear-gradient(135deg, #161b22, #0d1117);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 0.75rem;
        }

        .injury-card:hover { border-color: rgba(255,255,255,0.15); }

        .inj-out       { border-left: 4px solid #FF4444; }
        .inj-doubtful  { border-left: 4px solid #FFD700; }
        .inj-available { border-left: 4px solid #00C864; }

        .inj-status-out       { background: rgba(255,68,68,0.15);  color: #FF6B6B; border: 1px solid rgba(255,68,68,0.3); }
        .inj-status-doubtful  { background: rgba(255,208,0,0.15); color: #FFD700; border: 1px solid rgba(255,208,0,0.3); }
        .inj-status-available { background: rgba(0,200,100,0.15); color: #00C864; border: 1px solid rgba(0,200,100,0.3); }

        .inj-player { font-size: 1rem; font-weight: 700; color: #ffffff; }
        .inj-team   { font-size: 0.8rem; color: rgba(255,255,255,0.45); }
        .inj-desc   { font-size: 0.88rem; color: rgba(255,255,255,0.6); margin-top: 0.3rem; }

        /* ── Pitch Cards ── */
        .pitch-stat-card {
            background: linear-gradient(135deg, #161b22, #0d1117);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 1.4rem 1.2rem;
            text-align: center;
        }

        .pitch-stat-label {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.4);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 0.5rem;
        }

        .pitch-stat-value {
            font-size: 1.4rem;
            font-weight: 800;
            color: #ffffff;
        }

        .pitch-stat-icon {
            font-size: 1.6rem;
            margin-bottom: 0.4rem;
        }

        /* ── Notes Box ── */
        .notes-box {
            background: rgba(255,107,53,0.07);
            border: 1px solid rgba(255,107,53,0.2);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            color: rgba(255,255,255,0.8);
            font-size: 0.92rem;
            line-height: 1.6;
        }

        /* ── Timestamp / Last Updated ── */
        .last-updated {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.8rem;
            color: rgba(255,255,255,0.35);
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 50px;
            padding: 0.25rem 0.75rem;
        }

        /* ── Refresh Button override ── */
        div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, #FF6B35, #FF9A5C) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
            padding: 0.55rem 1.5rem !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3) !important;
        }

        div[data-testid="stButton"] > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255, 107, 53, 0.45) !important;
        }

        /* ── Tab styling ── */
        div[data-testid="stTabs"] > div > div > button {
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }

        div[data-testid="stTabs"] > div > div > button[aria-selected="true"] {
            color: #FF6B35 !important;
        }

        /* ── Dataframe ── */
        div[data-testid="stDataFrame"] {
            border-radius: 12px !important;
            overflow: hidden;
        }

        /* ── Divider ── */
        hr { border-color: rgba(255,255,255,0.07) !important; }

        /* ── Footer ── */
        .footer {
            text-align: center;
            padding: 1.5rem;
            color: rgba(255,255,255,0.2);
            font-size: 0.82rem;
        }

        .footer a {
            color: rgba(255,107,53,0.6);
            text-decoration: none;
        }

        .footer-divider {
            height: 1px;
            background: linear-gradient(to right, transparent, rgba(255,107,53,0.2), transparent);
            margin: 0.5rem 0 1rem;
        }

        /* ── Medal top 3 ── */
        .medal-card {
            background: linear-gradient(135deg, #161b22, #0d1117);
            border-radius: 16px;
            padding: 1.5rem 1rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.07);
        }

        .medal-card.gold   { border-top: 3px solid #FFD700; }
        .medal-card.silver { border-top: 3px solid #C0C0C0; }
        .medal-card.bronze { border-top: 3px solid #CD7F32; }

        .medal-emoji { font-size: 2rem; }
        .medal-team  { font-size: 1.1rem; font-weight: 800; color: #ffffff; margin-top: 0.3rem; }
        .medal-pts   { font-size: 0.85rem; color: rgba(255,255,255,0.45); margin-top: 0.15rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
if "ipl_data" not in st.session_state:
    st.session_state["ipl_data"] = load_from_json()

data: dict = st.session_state["ipl_data"]

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-header">
        <div class="hero-title">🏏 IPL 2026 Match Predictor &amp; Tracker</div>
        <div class="hero-subtitle">Real-time cricket intelligence · Powered by Gemini AI &amp; Google Search</div>
        <div class="hero-badges">
            <span class="badge badge-orange">⚡ Live Data</span>
            <span class="badge badge-green">✓ Gemini AI</span>
            <span class="badge badge-blue">🔍 Google Search Grounding</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Top control bar (timestamp + refresh) ────────────────────────────────────
ctrl_left, ctrl_mid, ctrl_right = st.columns([3, 1, 1])

with ctrl_left:
    last_updated = data.get("last_updated")
    if last_updated:
        try:
            ts = last_updated.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
            formatted = dt.strftime("%d %b %Y · %I:%M %p UTC")
        except ValueError:
            formatted = last_updated
        st.markdown(
            f'<span class="last-updated">🕒 Last refreshed: {formatted}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="last-updated">🕒 No data yet — click Refresh</span>',
            unsafe_allow_html=True,
        )

with ctrl_right:
    refresh_clicked = st.button("🔄 Refresh Data", use_container_width=True)

if refresh_clicked:
    with st.spinner("Fetching live IPL 2026 data from Gemini …"):
        try:
            new_data = refresh_data()
            st.session_state["ipl_data"] = new_data
            data = new_data
            st.success("✅ Data refreshed successfully!")
            st.rerun()
        except EnvironmentError as e:
            st.error(f"⚙️ Configuration error: {e}")
        except json.JSONDecodeError as e:
            st.error(f"🔧 Failed to parse Gemini response as JSON: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error while refreshing data: {e}")

# ── Today's Match Banner ──────────────────────────────────────────────────────
match = data.get("todays_match", {})
if match:
    team1      = match.get("team1", "TBD")
    team2      = match.get("team2", "TBD")
    venue      = match.get("venue", "TBD")
    time_ist   = match.get("time_ist", "TBD")
    status     = match.get("status", "Upcoming")
    score      = match.get("score", "")

    status_lower = status.lower()
    if status_lower == "live":
        status_class = "status-live"
        banner_class = "match-banner match-banner-live"
        status_html  = '<span class="live-dot"></span>LIVE'
    elif status_lower == "completed":
        status_class = "status-completed"
        banner_class = "match-banner"
        status_html  = "✅ COMPLETED"
    else:
        status_class = "status-upcoming"
        banner_class = "match-banner"
        status_html  = "🟡 UPCOMING"

    t1_color = get_team_color(team1)
    t2_color = get_team_color(team2)
    score_html = f" &nbsp;·&nbsp; <strong style='color:#fff'>{score}</strong>" if score else ""

    st.markdown(
        f"""
        <div class="{banner_class}">
            <div style="display:flex; align-items:center; gap:1rem; flex-wrap:wrap;">
                <div>
                    <div class="match-teams">
                        <span style="color:{t1_color}">{team1}</span>
                        <span style="color:rgba(255,255,255,0.3)"> vs </span>
                        <span style="color:{t2_color}">{team2}</span>
                    </div>
                    <div class="match-info">📍 {venue} &nbsp;·&nbsp; 🕐 {time_ist}{score_html}</div>
                </div>
                <div style="margin-left:auto;">
                    <span class="status-pill {status_class}">{status_html}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Quick Summary Metrics ─────────────────────────────────────────────────────
points_table: list = data.get("points_table", [])
player_stats: list = data.get("player_stats", [])
injury_news:  list = data.get("injury_news", [])

total_teams   = len(points_table)
total_matches = sum(int(t.get("played", 0)) for t in points_table) // 2 if points_table else 0

top_scorer = "—"
top_runs   = "—"
if player_stats:
    try:
        best = max(player_stats, key=lambda p: int(p.get("runs", 0)))
        name_parts = best.get("name", "—").split()
        top_scorer = name_parts[-1] if name_parts else "—"   # last name for brevity
        top_runs   = str(best.get("runs", "—"))
    except (ValueError, TypeError):
        pass

top_wicket_taker = "—"
top_wickets      = "—"
if player_stats:
    try:
        best_w = max(player_stats, key=lambda p: int(p.get("wickets", 0)))
        w_name_parts = best_w.get("name", "—").split()
        top_wicket_taker = w_name_parts[-1] if w_name_parts else "—"
        top_wickets      = str(best_w.get("wickets", "—"))
    except (ValueError, TypeError):
        pass

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f'<div class="stat-card"><div class="stat-icon">🏟️</div>'
        f'<div class="stat-value">{total_teams}</div>'
        f'<div class="stat-label">Teams</div></div>',
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f'<div class="stat-card"><div class="stat-icon">🏏</div>'
        f'<div class="stat-value">{total_matches}</div>'
        f'<div class="stat-label">Matches Played</div></div>',
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f'<div class="stat-card"><div class="stat-icon">🏅</div>'
        f'<div class="stat-value">{top_runs}</div>'
        f'<div class="stat-label">Top Scorer · {top_scorer}</div></div>',
        unsafe_allow_html=True,
    )
with m4:
    st.markdown(
        f'<div class="stat-card"><div class="stat-icon">🎯</div>'
        f'<div class="stat-value">{top_wickets}</div>'
        f'<div class="stat-label">Top Wickets · {top_wicket_taker}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab_points, tab_stats, tab_injuries, tab_pitch = st.tabs(
    ["📊  Points Table", "🏅  Player Stats", "🩹  Injury News", "🏟️  Pitch Report"]
)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Points Table
# ─────────────────────────────────────────────────────────────────────────────
with tab_points:
    if not points_table:
        st.warning("No points table data available. Click **Refresh Data** to fetch it.")
    else:
        df_points = pd.DataFrame(points_table)

        column_map = {
            "team": "Team", "played": "Played", "won": "Won",
            "lost": "Lost", "nrr": "NRR", "points": "Points",
        }
        df_points.rename(columns=column_map, inplace=True)

        if "Points" in df_points.columns and "NRR" in df_points.columns:
            df_points["NRR_num"] = (
                df_points["NRR"].astype(str).str.lstrip("+").pipe(pd.to_numeric, errors="coerce")
            )
            df_points.sort_values(["Points", "NRR_num"], ascending=[False, False], inplace=True)
            df_points.drop(columns=["NRR_num"], inplace=True)
            df_points.reset_index(drop=True, inplace=True)
            df_points.index += 1

        try:
            max_pts = int(pd.to_numeric(df_points["Points"], errors="coerce").max()) if "Points" in df_points.columns else 1
        except (ValueError, TypeError):
            max_pts = 1
        max_pts = max_pts or 1  # guard against 0

        # ── Top 3 Medals ──────────────────────────────────────────────────────
        if len(df_points) >= 3:
            medal_styles = [
                ("🥇", "gold",   "#FFD700"),
                ("🥈", "silver", "#C0C0C0"),
                ("🥉", "bronze", "#CD7F32"),
            ]
            mc1, mc2, mc3 = st.columns(3)
            for i, (col, (emoji, css_class, color)) in enumerate(zip([mc1, mc2, mc3], medal_styles)):
                row = df_points.iloc[i]
                tname = row.get("Team", "—")
                pts   = row.get("Points", "—")
                won   = row.get("Won", "—")
                full  = get_team_full(tname)
                t_col = get_team_color(tname)
                col.markdown(
                    f"""
                    <div class="medal-card {css_class}">
                        <div class="medal-emoji">{emoji}</div>
                        <div class="medal-team" style="color:{t_col}">{tname}</div>
                        <div style="font-size:0.78rem;color:rgba(255,255,255,0.35);margin-top:2px">{full}</div>
                        <div style="font-size:1.5rem;font-weight:900;color:#fff;margin-top:0.4rem">{pts} pts</div>
                        <div class="medal-pts">{won} wins</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

        # ── Rankings List ─────────────────────────────────────────────────────
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.markdown('<div class="section-title">📋 Full Standings</div>', unsafe_allow_html=True)
            for i, row in df_points.iterrows():
                tname = row.get("Team", "—")
                pts   = row.get("Points", 0)
                won   = row.get("Won", 0)
                lost  = row.get("Lost", 0)
                nrr   = row.get("NRR", "—")
                played= row.get("Played", 0)
                t_col = get_team_color(tname)
                full  = get_team_full(tname)
                rank_cls = "top" if i <= 3 else ""
                try:
                    bar_pct = int((float(pts) / max_pts) * 100)
                except (ValueError, TypeError):
                    bar_pct = 0

                st.markdown(
                    f"""
                    <div class="rank-card">
                        <span class="rank-num {rank_cls}">{i}</span>
                        <div>
                            <div class="team-abbr" style="color:{t_col}">{tname}</div>
                            <div class="team-full">{full}</div>
                        </div>
                        <div style="flex:1;padding:0 0.5rem">
                            <div class="pts-bar-outer">
                                <div class="pts-bar-inner" style="width:{bar_pct}%;background:{t_col}"></div>
                            </div>
                        </div>
                        <span class="rank-nrr">{nrr}</span>
                        <span class="rank-pts">{pts}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with right_col:
            st.markdown('<div class="section-title">📈 Points Comparison</div>', unsafe_allow_html=True)

            chart_teams  = [row.get("Team", "") for _, row in df_points.iterrows()]
            chart_pts    = [row.get("Points", 0) for _, row in df_points.iterrows()]
            chart_colors = [get_team_color(t) for t in chart_teams]

            fig = go.Figure(
                go.Bar(
                    x=chart_pts[::-1],
                    y=chart_teams[::-1],
                    orientation="h",
                    marker=dict(
                        color=chart_colors[::-1],
                        line=dict(width=0),
                    ),
                    text=[f"{p} pts" for p in chart_pts[::-1]],
                    textposition="auto",
                    textfont=dict(color="#ffffff", size=11, family="Inter"),
                    hovertemplate="<b>%{y}</b><br>Points: %{x}<extra></extra>",
                )
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="rgba(255,255,255,0.7)", size=12),
                xaxis=dict(
                    gridcolor="rgba(255,255,255,0.05)",
                    zeroline=False,
                    title=None,
                ),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False, title=None),
                margin=dict(l=10, r=20, t=10, b=10),
                height=380,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Player Stats
# ─────────────────────────────────────────────────────────────────────────────
with tab_stats:
    if not player_stats:
        st.warning("No player stats available. Click **Refresh Data** to fetch them.")
    else:
        df_players = pd.DataFrame(player_stats)
        col_map = {
            "name": "Player", "team": "Team",
            "runs": "Runs", "wickets": "Wickets", "matches": "Matches",
        }
        df_players.rename(columns=col_map, inplace=True)

        has_runs    = "Runs"    in df_players.columns
        has_wickets = "Wickets" in df_players.columns

        bat_col, bowl_col = st.columns(2)

        # ── Batters ───────────────────────────────────────────────────────────
        with bat_col:
            st.markdown('<div class="section-title">🏏 Top Run-Scorers</div>', unsafe_allow_html=True)
            if has_runs:
                df_bat = (
                    df_players.sort_values("Runs", ascending=False)
                    .head(10)
                    .reset_index(drop=True)
                )
                try:
                    max_runs = int(pd.to_numeric(df_bat["Runs"], errors="coerce").max())
                except (ValueError, TypeError):
                    max_runs = 1
                max_runs = max_runs or 1

                for i, row in df_bat.iterrows():
                    p_name = row.get("Player", "—")
                    p_team = row.get("Team", "—")
                    p_runs = row.get("Runs", 0)
                    p_mch  = row.get("Matches", "—")
                    t_col  = get_team_color(p_team)
                    try:
                        pct = int((int(p_runs) / max_runs) * 100)
                    except (ValueError, TypeError):
                        pct = 0
                    if i == 0:
                        rank_lbl = "🥇"
                    elif i == 1:
                        rank_lbl = "🥈"
                    elif i == 2:
                        rank_lbl = "🥉"
                    else:
                        rank_lbl = f"#{i+1}"

                    st.markdown(
                        f"""
                        <div class="player-card">
                            <span class="player-rank">{rank_lbl}</span>
                            <div style="flex:1">
                                <div class="player-name">{p_name}</div>
                                <div class="player-team" style="color:{t_col}">{p_team} · {p_mch} matches</div>
                                <div style="margin-top:6px;background:rgba(255,255,255,0.06);border-radius:4px;height:4px">
                                    <div style="width:{pct}%;height:100%;background:{t_col};border-radius:4px"></div>
                                </div>
                            </div>
                            <span class="player-stat">{p_runs}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Plotly bar chart
                fig_bat = go.Figure(
                    go.Bar(
                        x=df_bat["Player"],
                        y=df_bat["Runs"],
                        marker=dict(
                            color=[get_team_color(t) for t in df_bat["Team"]],
                            line=dict(width=0),
                        ),
                        text=df_bat["Runs"],
                        textposition="auto",
                        textfont=dict(color="#fff", size=10),
                        hovertemplate="<b>%{x}</b><br>Runs: %{y}<extra></extra>",
                    )
                )
                fig_bat.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="rgba(255,255,255,0.65)", size=11),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, tickangle=-30),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, title="Runs"),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=260,
                    showlegend=False,
                )
                st.plotly_chart(fig_bat, use_container_width=True)
            else:
                st.info("Runs data not available.")

        # ── Bowlers ───────────────────────────────────────────────────────────
        with bowl_col:
            st.markdown('<div class="section-title">🎳 Top Wicket-Takers</div>', unsafe_allow_html=True)
            if has_wickets:
                df_bowl = (
                    df_players.sort_values("Wickets", ascending=False)
                    .head(10)
                    .reset_index(drop=True)
                )
                try:
                    max_wkts = int(pd.to_numeric(df_bowl["Wickets"], errors="coerce").max())
                except (ValueError, TypeError):
                    max_wkts = 1
                max_wkts = max_wkts or 1

                for i, row in df_bowl.iterrows():
                    p_name = row.get("Player", "—")
                    p_team = row.get("Team", "—")
                    p_wkts = row.get("Wickets", 0)
                    p_mch  = row.get("Matches", "—")
                    t_col  = get_team_color(p_team)
                    try:
                        pct = int((int(p_wkts) / max_wkts) * 100)
                    except (ValueError, TypeError):
                        pct = 0
                    if i == 0:
                        rank_lbl = "🥇"
                    elif i == 1:
                        rank_lbl = "🥈"
                    elif i == 2:
                        rank_lbl = "🥉"
                    else:
                        rank_lbl = f"#{i+1}"

                    st.markdown(
                        f"""
                        <div class="player-card">
                            <span class="player-rank">{rank_lbl}</span>
                            <div style="flex:1">
                                <div class="player-name">{p_name}</div>
                                <div class="player-team" style="color:{t_col}">{p_team} · {p_mch} matches</div>
                                <div style="margin-top:6px;background:rgba(255,255,255,0.06);border-radius:4px;height:4px">
                                    <div style="width:{pct}%;height:100%;background:{t_col};border-radius:4px"></div>
                                </div>
                            </div>
                            <span class="player-stat">{p_wkts}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                fig_bowl = go.Figure(
                    go.Bar(
                        x=df_bowl["Player"],
                        y=df_bowl["Wickets"],
                        marker=dict(
                            color=[get_team_color(t) for t in df_bowl["Team"]],
                            line=dict(width=0),
                        ),
                        text=df_bowl["Wickets"],
                        textposition="auto",
                        textfont=dict(color="#fff", size=10),
                        hovertemplate="<b>%{x}</b><br>Wickets: %{y}<extra></extra>",
                    )
                )
                fig_bowl.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="rgba(255,255,255,0.65)", size=11),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, tickangle=-30),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, title="Wickets"),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=260,
                    showlegend=False,
                )
                st.plotly_chart(fig_bowl, use_container_width=True)
            else:
                st.info("Wickets data not available.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Injury News
# ─────────────────────────────────────────────────────────────────────────────
with tab_injuries:
    if not injury_news:
        st.warning("No injury news available. Click **Refresh Data** to fetch it.")
    else:
        # Summary counts
        counts = {"out": 0, "doubtful": 0, "available": 0}
        for item in injury_news:
            s = item.get("status", "").lower()
            if s in counts:
                counts[s] += 1
            else:
                counts["doubtful"] += 1   # catch any unknown status

        sc1, sc2, sc3 = st.columns(3)
        sc1.markdown(
            f'<div class="stat-card" style="border-top:3px solid #FF4444">'
            f'<div class="stat-icon">🔴</div>'
            f'<div class="stat-value" style="color:#FF6B6B">{counts["out"]}</div>'
            f'<div class="stat-label">Out / Injured</div></div>',
            unsafe_allow_html=True,
        )
        sc2.markdown(
            f'<div class="stat-card" style="border-top:3px solid #FFD700">'
            f'<div class="stat-icon">🟡</div>'
            f'<div class="stat-value" style="color:#FFD700">{counts["doubtful"]}</div>'
            f'<div class="stat-label">Doubtful</div></div>',
            unsafe_allow_html=True,
        )
        sc3.markdown(
            f'<div class="stat-card" style="border-top:3px solid #00C864">'
            f'<div class="stat-icon">🟢</div>'
            f'<div class="stat-value" style="color:#00C864">{counts["available"]}</div>'
            f'<div class="stat-label">Available</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 Player Availability</div>', unsafe_allow_html=True)

        for item in injury_news:
            player  = item.get("player", "Unknown")
            team    = item.get("team", "—")
            injury  = item.get("injury", "—")
            status  = item.get("status", "—")
            s_lower = status.lower()

            if s_lower == "out":
                css_class  = "injury-card inj-out"
                badge_cls  = "inj-status-out"
                icon       = "🔴"
            elif s_lower == "available":
                css_class  = "injury-card inj-available"
                badge_cls  = "inj-status-available"
                icon       = "🟢"
            else:
                css_class  = "injury-card inj-doubtful"
                badge_cls  = "inj-status-doubtful"
                icon       = "🟡"

            t_col  = get_team_color(team)
            t_full = get_team_full(team)

            st.markdown(
                f"""
                <div class="{css_class}">
                    <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; flex-wrap:wrap">
                        <div>
                            <div class="inj-player">{icon} {player}</div>
                            <div class="inj-team" style="color:{t_col}">{team} · {t_full}</div>
                            <div class="inj-desc">🩹 {injury}</div>
                        </div>
                        <span class="status-pill {badge_cls}">{status.upper()}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Pitch Report
# ─────────────────────────────────────────────────────────────────────────────
with tab_pitch:
    pitch: dict = data.get("pitch_report", {})

    if not pitch:
        st.warning("No pitch report available. Click **Refresh Data** to fetch it.")
    else:
        venue      = pitch.get("venue", "—")
        city       = pitch.get("city", "—")
        pitch_type = pitch.get("pitch_type", "—")
        avg_score  = pitch.get("avg_first_innings_score", "—")
        dew        = pitch.get("dew_factor", "—")
        notes      = pitch.get("notes", "—")

        # Hero venue card
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(255,107,53,0.12) 0%, rgba(0,0,0,0) 60%),
                            linear-gradient(135deg, #0d1117, #161b22);
                border: 1px solid rgba(255,107,53,0.25);
                border-radius: 18px;
                padding: 2rem 2rem 1.5rem;
                margin-bottom: 1.5rem;
                text-align: center;
            ">
                <div style="font-size:2.5rem; margin-bottom:0.4rem">🏟️</div>
                <div style="font-size:1.6rem; font-weight:800; color:#ffffff">{venue}</div>
                <div style="font-size:0.9rem; color:rgba(255,255,255,0.4); margin-top:0.2rem">📍 {city}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pc1, pc2, pc3, pc4, pc5 = st.columns(5)

        def pitch_card(col, icon, label, value, color="#ffffff"):
            col.markdown(
                f'<div class="pitch-stat-card">'
                f'<div class="pitch-stat-icon">{icon}</div>'
                f'<div class="pitch-stat-label">{label}</div>'
                f'<div class="pitch-stat-value" style="color:{color}">{value}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Determine colours for contextual metrics
        pitch_color = {"batting": "#FFD700", "bowling": "#FF4444", "balanced": "#00C864"}.get(
            str(pitch_type).lower(), "#ffffff"
        )
        dew_color   = {"high": "#FF4444", "medium": "#FFD700", "low": "#00C864"}.get(
            str(dew).lower(), "#ffffff"
        )

        pitch_card(pc1, "📍", "City",       city)
        pitch_card(pc2, "🌿", "Pitch Type", pitch_type, pitch_color)
        pitch_card(pc3, "📈", "Avg 1st Inn Score", str(avg_score), "#FF6B35")
        pitch_card(pc4, "💧", "Dew Factor", dew, dew_color)

        # Pitch type gauge chart
        gauge_val = {"batting": 85, "balanced": 50, "bowling": 20}.get(str(pitch_type).lower(), 50)
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=gauge_val,
                number={"suffix": "%", "font": {"size": 20, "color": "#fff", "family": "Inter"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "rgba(255,255,255,0.2)", "tickfont": {"color": "rgba(255,255,255,0.4)", "size": 9}},
                    "bar":  {"color": pitch_color, "thickness": 0.25},
                    "bgcolor": "rgba(255,255,255,0.05)",
                    "bordercolor": "rgba(255,255,255,0.1)",
                    "steps": [
                        {"range": [0,  33], "color": "rgba(255,68,68,0.2)"},
                        {"range": [33, 66], "color": "rgba(0,200,100,0.2)"},
                        {"range": [66, 100],"color": "rgba(255,200,0,0.2)"},
                    ],
                    "threshold": {"line": {"color": pitch_color, "width": 3}, "thickness": 0.8, "value": gauge_val},
                },
                title={"text": "Batting Friendliness", "font": {"size": 12, "color": "rgba(255,255,255,0.5)", "family": "Inter"}},
            )
        )
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="rgba(255,255,255,0.7)"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=200,
        )
        with pc5:
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">📝 Analyst Notes</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="notes-box">💬 {notes}</div>', unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="footer-divider"></div>
    <div class="footer">
        Built with ❤️ by <strong>Jai</strong> · CS Student &nbsp;|&nbsp;
        Powered by <strong>Google Gemini AI</strong> &amp; <strong>Streamlit</strong> &nbsp;|&nbsp;
        Data via Google Search Grounding
    </div>
    """,
    unsafe_allow_html=True,
)

