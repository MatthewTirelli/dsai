# 04_agent_query.py
# Agent with REST Tool Call
# Pairs with 04_agent_query.R
# Tim Fraser

# Run the FastAPI app (12_end/03_fastapi) and set API_PUBLIC_URL in 12_end/.env.
# Uses Ollama function-calling so the model must call predict_vehicle_count; we normalize odd arg shapes below.

import argparse
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "08_function_calling"))

from dotenv import load_dotenv
from functions import agent

import requests

# 1. CONFIG ###################################

load_dotenv(ROOT_DIR / "12_end" / ".env")

ENDPOINT_URL = os.getenv("API_PUBLIC_URL", "http://localhost:8000").rstrip("/")
MODEL = os.getenv("OLLAMA_MODEL", "smollm2:1.7b")

UNIT_NOTE = "vehicles observed in one representative minute (1m/t1 interval) within the requested hour and day of week"

# 2. DEFINE TOOL FUNCTION ###################################

def _normalize_hours_of_day(raw):
    """
    Ollama small models sometimes pass one hour as a bare int/str or malformed list.
    String "21" must become [21], not ['2','1'] from iterating the string.
    """
    if raw is None:
        return []

    # Single numeric hour without a list wrapper
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        h = int(raw)
        return [h] if 0 <= h <= 23 else []

    # JSON-encoded list/int in a string, e.g. "[21]" or "21"
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        if s.isdigit():
            h = int(s)
            return [h] if 0 <= h <= 23 else []
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            parsed = None
            parts = [p.strip() for p in s.replace(";", ",").split(",") if p.strip()]
            out = []
            for p in parts:
                if p.isdigit():
                    h = int(p)
                    if 0 <= h <= 23:
                        out.append(h)
            return out
        # Recurse so we accept JSON numbers/lists from the model
        return _normalize_hours_of_day(parsed)

    out = []
    if isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                h = int(item)
                if 0 <= h <= 23:
                    out.append(h)
            elif isinstance(item, str) and item.strip().isdigit():
                h = int(item.strip())
                if 0 <= h <= 23:
                    out.append(h)
    return out


def predict_vehicle_count(day_of_week, hours_of_day):
    # Normalize day (models may send strings)
    dow = int(day_of_week) if day_of_week is not None else None
    if dow is None:
        raise ValueError("day_of_week is required.")

    hours = _normalize_hours_of_day(hours_of_day)
    if not hours:
        raise ValueError(
            "hours_of_day must resolve to at least one hour 0–23 (e.g. [21] for 21:00)."
        )

    predictions = []
    for hour in hours:
        resp = requests.get(
            f"{ENDPOINT_URL}/predict",
            params={"day_of_week": dow, "hour_of_day": hour},
            timeout=10,
        )
        resp.raise_for_status()
        predictions.append(
            {
                "hour_of_day": hour,
                "predicted_vehicle_count": float(resp.json()["predicted_vehicle_count"]),
            }
        )

    return {
        "day_of_week": dow,
        "unit": "vehicles_observed_in_one_minute",
        "interval": "1m_t1",
        "note": "Each prediction is for one representative minute within that hour and day of week.",
        "predictions": predictions,
    }

# 3. DEFINE TOOL METADATA ###################################

tool_predict_vehicle_count = {
    "type": "function",
    "function": {
        "name": "predict_vehicle_count",
        "description": (
            "Predict Brussels vehicle count for a weekday and one or more hours. "
            "You MUST call this for every vehicle-count question instead of guessing. "
            "day_of_week: integer 1=Monday through 7=Sunday. "
            "hours_of_day: JSON array of 24-hour integers. "
            'Example Monday 21:00 (9 PM): day_of_week=1, hours_of_day=[21]. '
            "Example Monday 09:00: day_of_week=1, hours_of_day=[9]."
        ),
        "parameters": {
            "type": "object",
            "required": ["day_of_week", "hours_of_day"],
            "properties": {
                "day_of_week": {"type": "integer", "description": "1=Monday, ..., 7=Sunday"},
                "hours_of_day": {
                    "type": "array",
                    "description": (
                        "Hours in 24h clock (0–23). For exactly 21:00 use [21]. "
                        "For full day use something like range or list multiple hours."
                    ),
                    "items": {"type": "integer"},
                },
            },
        },
    },
}

# 4. RUN AGENT ###################################

def build_messages(user_text):
    # Strong system prompt improves tool use on smaller local models (e.g. smollm).
    sys_text = (
        "You are a Brussels traffic assistant. "
        "For any question about predicted vehicle counts for a weekday and hour, "
        "you MUST call the tool predict_vehicle_count exactly once when that is sufficient. "
        "Never invent numbers. Monday=1 … Sunday=7. Use 24-hour times: 21:00 means hour 21, so hours_of_day should include 21."
    )
    return [
        {"role": "system", "content": sys_text},
        {"role": "user", "content": user_text},
    ]


parser = argparse.ArgumentParser(description="Agent + predict_vehicle_count (FastAPI /predict).")
parser.add_argument(
    "--question",
    default="How many vehicles does the model predict for Brussels traffic on Monday at 21:00?",
    help="User question (model should call predict_vehicle_count).",
)
args = parser.parse_args()

messages = build_messages(args.question)
tools = [tool_predict_vehicle_count]

result = agent(
    messages=messages,
    model=MODEL,
    output="text",
    tools=tools,
)

print("Agent result:", result)

# Short human-readable line when tool returned structured JSON
if isinstance(result, dict) and result.get("predictions"):
    for p in result["predictions"]:
        print(
            f"  weekday {result.get('day_of_week')} hour {p['hour_of_day']:02d}: "
            f"{p['predicted_vehicle_count']:.6g} ({UNIT_NOTE})"
        )

# 5. VERIFY ###################################

truth = predict_vehicle_count(day_of_week=1, hours_of_day=[21])
truth_val = truth["predictions"][0]["predicted_vehicle_count"]
print("Direct API call predictions returned:", len(truth["predictions"]))
print(f"Reference one-minute vehicle count Monday 21:00: {truth_val} (1m/t1)")
print("Unit:", UNIT_NOTE)
if isinstance(result, dict):
    preds = result.get("predictions") or []
    if preds and preds[0].get("hour_of_day") == 21 and result.get("day_of_week") == 1:
        agent_val = preds[0]["predicted_vehicle_count"]
        print("Match (agent tool vs direct):", abs(agent_val - truth_val) < 1e-6)
    else:
        print("Match: skipped (tool did not return Monday hour 21).")
else:
    print("Match: skipped (no structured tool result — check Ollama model / tool_calls).")
