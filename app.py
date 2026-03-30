"""
app.py — The Interface
======================
Author : Jai (CS Student)
Purpose: Streamlit dashboard that displays IPL 2026 data from ipl_master_data.json
         and lets the user refresh it via the Gemini-powered data engine.

Run with:
    streamlit run app.py
"""

import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from data_manager import load_from_json, refresh_data

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL 2026 Match Predictor & Tracker",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.4rem;
            font-weight: 700;
            color: #FF6B35;
            text-align: center;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1rem;
            color: #6c757d;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background: #1e1e2e;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }
        .stAlert { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">🏏 IPL 2026 Match Predictor & Tracker</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by Gemini AI · Real-time data bridge</p>', unsafe_allow_html=True)

# ── Load data (cached on first run, refreshed on button click) ────────────────
# We use session_state to avoid reloading the JSON on every Streamlit re-run.
if "ipl_data" not in st.session_state:
    st.session_state["ipl_data"] = load_from_json()

data: dict = st.session_state["ipl_data"]


# ── Today's match banner ──────────────────────────────────────────────────────
match = data.get("todays_match", {})
if match:
    team1 = match.get("team1", "TBD")
    team2 = match.get("team2", "TBD")
    venue = match.get("venue", "TBD")
    time_ist = match.get("time_ist", "TBD")
    status = match.get("status", "")
    score = match.get("score", "")

    status_emoji = {"Live": "🔴", "Completed": "✅", "Upcoming": "🟡"}.get(status, "ℹ️")
    score_str = f" · **{score}**" if score else ""

    st.info(
        f"{status_emoji} **Today's Match** — **{team1} vs {team2}** at {venue} · {time_ist}{score_str}"
    )

# ── Last updated timestamp ────────────────────────────────────────────────────
last_updated = data.get("last_updated")
if last_updated:
    try:
        # Replace 'Z' suffix and strip timezone offset for broad Python 3.7+ compat
        ts = last_updated.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        formatted = dt.strftime("%d %b %Y, %I:%M %p UTC")
    except ValueError:
        formatted = last_updated
    st.caption(f"🕒 Data last refreshed: {formatted}")
else:
    st.caption("🕒 Data not yet fetched. Click **Refresh Data** to load live data.")

# ── Refresh button ────────────────────────────────────────────────────────────
col_btn, col_warn = st.columns([1, 4])
with col_btn:
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

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_points, tab_stats, tab_injuries, tab_pitch = st.tabs(
    ["📊 Points Table", "🏅 Player Stats", "🩹 Injury News", "🏟️ Pitch Report"]
)


# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — Points Table
# ────────────────────────────────────────────────────────────────────────────
with tab_points:
    st.subheader("IPL 2026 — Points Table")

    points_table: list = data.get("points_table", [])

    if not points_table:
        st.warning("No points table data available. Click **Refresh Data** to fetch it.")
    else:
        df_points = pd.DataFrame(points_table)

        # Normalise column names for display
        column_map = {
            "team": "Team",
            "played": "Played",
            "won": "Won",
            "lost": "Lost",
            "nrr": "NRR",
            "points": "Points",
        }
        df_points.rename(columns=column_map, inplace=True)

        # Sort by Points desc, then NRR desc
        if "Points" in df_points.columns and "NRR" in df_points.columns:
            # Strip the leading '+' sign so numeric conversion works cleanly
            df_points["NRR_num"] = (
                df_points["NRR"].astype(str).str.lstrip("+").pipe(pd.to_numeric, errors="coerce")
            )
            df_points.sort_values(["Points", "NRR_num"], ascending=[False, False], inplace=True)
            df_points.drop(columns=["NRR_num"], inplace=True)
            df_points.reset_index(drop=True, inplace=True)
            df_points.index += 1  # rank starts at 1

        st.dataframe(df_points, use_container_width=True)

        # Quick top-3 highlight
        if len(df_points) >= 3:
            st.markdown("#### 🏆 Top 3 Teams")
            cols = st.columns(3)
            medals = ["🥇", "🥈", "🥉"]
            for i, col in enumerate(cols):
                row = df_points.iloc[i]
                team_name = row.get("Team", "—")
                pts = row.get("Points", "—")
                col.metric(label=f"{medals[i]} {team_name}", value=f"{pts} pts")


# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — Player Stats
# ────────────────────────────────────────────────────────────────────────────
with tab_stats:
    st.subheader("IPL 2026 — Player Statistics")

    player_stats: list = data.get("player_stats", [])

    if not player_stats:
        st.warning("No player stats available. Click **Refresh Data** to fetch them.")
    else:
        df_players = pd.DataFrame(player_stats)

        column_map = {
            "name": "Player",
            "team": "Team",
            "runs": "Runs",
            "wickets": "Wickets",
            "matches": "Matches",
        }
        df_players.rename(columns=column_map, inplace=True)

        # Split into batters and bowlers for cleaner display
        has_runs = "Runs" in df_players.columns
        has_wickets = "Wickets" in df_players.columns

        sub_bat, sub_bowl = st.columns(2)

        with sub_bat:
            st.markdown("#### 🏏 Top Run-Scorers")
            if has_runs:
                df_bat = df_players.sort_values("Runs", ascending=False).head(10).reset_index(drop=True)
                df_bat.index += 1
                st.dataframe(df_bat[["Player", "Team", "Runs", "Matches"]], use_container_width=True)
            else:
                st.info("Runs data not available.")

        with sub_bowl:
            st.markdown("#### 🎳 Top Wicket-Takers")
            if has_wickets:
                df_bowl = df_players.sort_values("Wickets", ascending=False).head(10).reset_index(drop=True)
                df_bowl.index += 1
                st.dataframe(df_bowl[["Player", "Team", "Wickets", "Matches"]], use_container_width=True)
            else:
                st.info("Wickets data not available.")


# ────────────────────────────────────────────────────────────────────────────
# TAB 3 — Injury News
# ────────────────────────────────────────────────────────────────────────────
with tab_injuries:
    st.subheader("IPL 2026 — Injury & Availability Updates")

    injury_news: list = data.get("injury_news", [])

    if not injury_news:
        st.warning("No injury news available. Click **Refresh Data** to fetch it.")
    else:
        # Colour-code by status
        status_colors = {
            "out": "🔴",
            "doubtful": "🟡",
            "available": "🟢",
        }

        for item in injury_news:
            player = item.get("player", "Unknown")
            team = item.get("team", "—")
            injury = item.get("injury", "—")
            status = item.get("status", "—")
            icon = status_colors.get(status.lower(), "⚪")

            with st.container():
                st.markdown(
                    f"{icon} **{player}** ({team}) — {injury}  \n"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Status: `{status}`"
                )
                st.divider()


# ────────────────────────────────────────────────────────────────────────────
# TAB 4 — Pitch Report
# ────────────────────────────────────────────────────────────────────────────
with tab_pitch:
    st.subheader("IPL 2026 — Pitch & Stadium Report")

    pitch: dict = data.get("pitch_report", {})

    if not pitch:
        st.warning("No pitch report available. Click **Refresh Data** to fetch it.")
    else:
        venue = pitch.get("venue", "—")
        city = pitch.get("city", "—")
        pitch_type = pitch.get("pitch_type", "—")
        avg_score = pitch.get("avg_first_innings_score", "—")
        dew = pitch.get("dew_factor", "—")
        notes = pitch.get("notes", "—")

        col1, col2, col3 = st.columns(3)
        col1.metric("🏟️ Venue", venue)
        col2.metric("📍 City", city)
        col3.metric("🌿 Pitch Type", pitch_type)

        col4, col5 = st.columns(2)
        col4.metric("📈 Avg 1st Innings Score", str(avg_score))
        col5.metric("💧 Dew Factor", dew)

        st.markdown("#### 📝 Analyst Notes")
        st.info(notes)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#6c757d; font-size:0.85rem;'>"
    "Built by Jai · CS Student · Powered by Google Gemini &amp; Streamlit"
    "</p>",
    unsafe_allow_html=True,
)
