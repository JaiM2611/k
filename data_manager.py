"""
data_manager.py — The Engine
============================
Author : Jai (CS Student)
Purpose: Use the Gemini API (with its built-in Google Search tool) to fetch
         real-time IPL 2026 data and persist it in ipl_master_data.json.

How "Function Calling / Tool Use" works here
---------------------------------------------
1. We create a Gemini Client and configure a generation request with the
   `google_search` tool enabled.
2. We send a detailed prompt asking Gemini to *search* for live IPL data.
3. Gemini internally decides to call the Google Search tool, fetches results,
   and synthesises a structured JSON response.
4. We parse that JSON and save it to ipl_master_data.json so the UI never
   has to call the API directly — it just reads from the local file.
"""

import json
import os
from datetime import datetime, timezone

from google import genai
from google.genai import types

# ── Configuration ────────────────────────────────────────────────────────────
# Set your Gemini API key via the environment variable GEMINI_API_KEY.
# Example (Linux/Mac):  export GEMINI_API_KEY="your-key-here"
# Example (Windows):    set GEMINI_API_KEY=your-key-here
API_KEY = os.environ.get("AIzaSyBNX9Z9uhzKjvxBOckg-SBFw8yzS0aWlvg", "")

# Path where all fetched data will be stored.
JSON_FILE = os.path.join(os.path.dirname(__file__), "ipl_master_data.json")

# Gemini model that supports the Google Search grounding tool.
MODEL_NAME = "gemini-2.0-flash"

# ── Prompt template ──────────────────────────────────────────────────────────
_PROMPT_TEMPLATE = """
You are a cricket data assistant. Today is {today}.

Using your Google Search tool, find the LATEST real-time data for IPL 2026 and
return it as a single, valid JSON object with EXACTLY this structure
(no extra keys, no markdown fences, just raw JSON):

{{
  "points_table": [
    {{
      "team": "Team Name",
      "played": 0,
      "won": 0,
      "lost": 0,
      "nrr": "+0.000",
      "points": 0
    }}
  ],
  "player_stats": [
    {{
      "name": "Player Name",
      "team": "Team Name",
      "runs": 0,
      "wickets": 0,
      "matches": 0
    }}
  ],
  "injury_news": [
    {{
      "player": "Player Name",
      "team": "Team Name",
      "injury": "Description",
      "status": "Doubtful / Available / Out"
    }}
  ],
  "pitch_report": {{
    "venue": "Venue Name",
    "city": "City",
    "pitch_type": "Batting / Bowling / Balanced",
    "avg_first_innings_score": 0,
    "dew_factor": "High / Medium / Low",
    "notes": "Short description"
  }},
  "todays_match": {{
    "team1": "Team 1 abbreviation",
    "team2": "Team 2 abbreviation",
    "venue": "Full venue name",
    "time_ist": "HH:MM AM/PM IST",
    "status": "Upcoming / Live / Completed",
    "score": ""
  }}
}}

Rules:
- Include all 10 IPL 2026 teams in points_table (RCB, MI, KKR, SRH, RR, CSK, DC, GT, LSG, PBKS).
- Include at least 5 top run-scorers and 5 top wicket-takers in player_stats.
- Include the latest injury updates for players (include MS Dhoni, Ajinkya Rahane, and any others found).
- Pitch report should be for today's match venue as found via search.
- Populate todays_match with the actual match scheduled for today per the IPL 2026 fixtures.
- Return ONLY the raw JSON. No explanations, no markdown.
"""


def _build_fetch_prompt() -> str:
    """Return the fetch prompt with today's UTC date injected."""
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    return _PROMPT_TEMPLATE.format(today=today)


# ── Core Functions ────────────────────────────────────────────────────────────

def _make_client() -> genai.Client:
    """Create and return a configured Gemini Client."""
    if not API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please export it before running the app."
        )
    return genai.Client(api_key=API_KEY)


def fetch_ipl_updates() -> dict:
    """
    Ask Gemini (with Google Search enabled) for live IPL 2026 data.

    Function-Calling / Tool-Use Flow
    ---------------------------------
    Step 1 — We create a Gemini Client and build a Tool with google_search.
    Step 2 — We call client.models.generate_content() with that tool attached.
    Step 3 — Gemini's planner realises it needs fresh data, so it internally
              invokes the Google Search tool (this is the "function call").
    Step 4 — The search results are fed back to Gemini, which then synthesises
              the final structured JSON answer for us.
    Step 5 — We extract the text, parse it as JSON, and return the dict.

    Returns
    -------
    dict
        Parsed JSON data with keys: points_table, player_stats, injury_news,
        pitch_report, todays_match.
    """
    client = _make_client()

    # Enable the built-in Google Search grounding tool so Gemini can look up
    # real-time data instead of relying solely on its training knowledge.
    google_search_tool = types.Tool(google_search=types.GoogleSearch())

    print("[data_manager] Sending request to Gemini API …")
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=_build_fetch_prompt(),
        config=types.GenerateContentConfig(tools=[google_search_tool]),
    )

    raw_text = response.text.strip()

    # Strip accidental markdown fences that some model versions still emit.
    # e.g. ```json\n{...}\n``` or ```\n{...}\n```
    if raw_text.startswith("```"):
        # Remove the first line (the fence opener) and the last line if it's "```"
        lines = raw_text.splitlines()
        raw_text = "\n".join(lines[1:] if len(lines) > 1 else lines)
    if raw_text.endswith("```"):
        raw_text = raw_text[: raw_text.rfind("```")].rstrip()

    data = json.loads(raw_text)
    print("[data_manager] Data received and parsed successfully.")
    return data


def save_to_json(data: dict) -> None:
    """
    Persist *data* to ipl_master_data.json, adding a timestamp.

    Parameters
    ----------
    data : dict
        The structured IPL data returned by fetch_ipl_updates().
    """
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[data_manager] Data saved to {JSON_FILE}")


def load_from_json() -> dict:
    """
    Load the cached IPL data from ipl_master_data.json.

    If the file does not exist or is empty/corrupt, return a safe default
    structure so the UI can still render without crashing.

    Returns
    -------
    dict
        IPL data dict (possibly empty defaults if file is missing/corrupt).
    """
    default = {
        "last_updated": None,
        "points_table": [],
        "player_stats": [],
        "injury_news": [],
        "pitch_report": {},
        "todays_match": {},
    }

    if not os.path.exists(JSON_FILE):
        return default

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return default
        loaded = json.loads(content)
        # Merge with defaults so missing keys don't cause KeyErrors in the UI.
        default.update(loaded)
        return default
    except (json.JSONDecodeError, OSError):
        return default


# ── Convenience entry-point ───────────────────────────────────────────────────

def refresh_data() -> dict:
    """
    Fetch fresh data from Gemini and save it. Returns the new data dict.

    This is the single function the UI's "Refresh Data" button calls.
    """
    data = fetch_ipl_updates()
    save_to_json(data)
    return data


# ── CLI usage ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Fetching IPL 2026 data via Gemini …")
    result = refresh_data()
    print(json.dumps(result, indent=2))
