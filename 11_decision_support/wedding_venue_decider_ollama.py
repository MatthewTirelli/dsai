# wedding_venue_decider_ollama.py
# AI decider: wedding venue comparison via local Ollama /api/chat
# Pairs with ACTIVITY_decider.md
# Tim Fraser
#
# Calls your local Ollama server (default http://127.0.0.1:11434) with a system + user prompt,
# the 16-venue text from the activity, and the Stage 1 or Stage 2 couple priorities. Prints the
# model's markdown (table, shortlist, caveats). No API key is required for local Ollama.
#
# Prereq: ollama serve running, and a model pulled (e.g. ollama pull llama3.2).
# Optional: pip install httpx
#
# Run from repo root:
#   python 11_decision_support/wedding_venue_decider_ollama.py
#   python 11_decision_support/wedding_venue_decider_ollama.py --stage 2
#   OLLAMA_MODEL=llama3.2:latest python 11_decision_support/wedding_venue_decider_ollama.py

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

# Local Ollama; override with OLLAMA_HOST (e.g. if you use a custom port)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2").strip() or "llama3.2"

SYSTEM_PROMPT = """You are a structured data extractor and decision analyst.
Your job is to extract key attributes from unstructured venue descriptions,
build a comparison table, and recommend the top 3 venues based on the client's priorities. Please look at all of the priorities, including price.

Always return:
1. A markdown table with columns: Venue, Capacity, Approx. Price/Night, Catering, Outdoor, Parking, Vibe (1 word)
2. A ranked shortlist of top 3 venues with 1-sentence justification each
3. One sentence noting any venues you had to exclude due to missing information

Be concise. Do not invent data that is not in the descriptions.
"""

# Full venue block copied from 11_decision_support/ACTIVITY_decider.md
VENUE_DATA = """
Venue 1 — The Rosewood Estate
A sprawling property in the Hudson Valley with manicured gardens and a restored barn.
Capacity up to 175 guests. Rental fee is $17,500 Friday–Sunday. They have a preferred
catering list with 4 approved vendors. Outdoor ceremony space available with a rain
backup tent. Parking for ~80 cars on site.

Venue 2 — The Grand Metropolitan Hotel
Downtown ballroom, seats up to 300. In-house catering only. Pricing starts at $12,000
for the ballroom rental, catering packages extra. Valet parking. No outdoor space.

Venue 3 — Lakeview Pavilion
Outdoor lakeside pavilion. No indoor backup. BYOB catering. Fits about 90 people
comfortably, 110 at a squeeze. Very affordable — around $2,500 for a weekend.

Venue 4 — Thornfield Manor
Historic manor house, 8 acres. Exclusive use for the weekend. Price: $18,000.
In-house catering team. Ceremony can be held on the grounds or in the chapel.
Capacity 150. Featured in several bridal magazines.

Venue 5 — The Foundry at Millworks
Industrial-chic converted factory. Very trendy. Capacity 250. Bring your own vendors.
Rental is $5,000. Rooftop available for cocktail hour. No on-site parking — street
parking and nearby garage only.

Venue 6 — Sunrise Farm & Vineyard
Working vineyard with barn and outdoor ceremony terrace. Stunning views. Capacity 130.
Weekend rental $9,800. Catering through their in-house team or 2 approved vendors.
Ample parking. Very popular — books 18 months out.

Venue 7 — The Atrium Club
Corporate event space that does weddings on weekends. Very flexible on catering.
Fits 300+. Located downtown. Pricing on request — sales team says "typically $9,000–$14,000
depending on date." Not particularly romantic but very professional.

Venue 8 — Cedar Hollow Retreat
Rustic woodland lodge. Intimate and cozy. Max 60 guests. $3,200 for a Saturday.
Outside catering allowed. No formal parking lot — guests park in a field.

Venue 9 — The Belvedere
Upscale rooftop venue with skyline views. Indoor/outdoor setup. Capacity 180.
In-house catering required. Rental + minimum catering spend is $28,000.
Very elegant. Valet only.

Venue 10 — Harborside Event Center
Waterfront venue, brand new. Capacity 220. Pricing TBD — still finalizing packages.
Flexible on catering. Outdoor terrace available. Large parking lot.

Venue 11 — The Ivy House
Garden venue in a residential neighborhood. Permits outdoor ceremonies.
Capacity 100. $4,500 rental. BYOB catering. Street parking only — coordinator
recommends a shuttle from a nearby lot.

Venue 12 — Maple Ridge Country Club
Classic country club setting. Capacity 160. In-house catering only, known for
being very good. Rental from $28,500. Golf course backdrop for photos.
Ample parking. Private feel.

Venue 13 — The Glasshouse Conservatory
All-glass event space surrounded by botanical gardens. Very dramatic.
Capacity 140. $18,000 rental, catering open. Outdoor garden available for ceremonies.
Parking on site. Popular for spring weddings.

Venue 14 — Millbrook Inn
Country inn with event lawn. Venue rental $10,500. Capacity 120. Outside catering
allowed. Some overnight rooms available for wedding party. Very charming.

Venue 15 — The Warehouse District Loft
Raw, urban space. Very minimal. No catering kitchen. Capacity 200.
$8,800 rental. Not ideal for traditional weddings.

Venue 16 — Cloverfield Farms
Family-owned working farm. Barn + outdoor space. Capacity 135.
$6,000 Friday–Sunday. Preferred caterer list (3 vendors).
Casual, warm atmosphere. Lots of parking. Dogs welcome.
""".strip()

# Stage 1 — ACTIVITY_decider.md
PRIORITIES_STAGE1 = """
- Budget: under $8,000 for venue rental
- Guest count: ~120 people
- Vibe: romantic, not too corporate
- Must have outdoor ceremony option
- Catering must be in-house or on an approved vendor list
""".strip()

# Stage 2 — shifted priorities
PRIORITIES_STAGE2 = """
- Budget: flexible, up to $15,000
- Guest count: ~200 people
- Vibe: elegant, grand
- Outdoor is a nice-to-have but not required
- No catering constraint
""".strip()


def build_user_message(priorities_block: str) -> str:
    """Assemble the user turn: priorities + instruction + raw venue text."""
    return f"""Here are the couple's priorities:
{priorities_block}

Here are descriptions of 16 venues. Please analyze and recommend.

{VENUE_DATA}
"""


def ollama_chat(
    system: str,
    user: str,
    *,
    base_url: str = OLLAMA_HOST,
    model: str = OLLAMA_MODEL,
) -> str:
    """One non-streaming POST to Ollama /api/chat; returns assistant message text."""
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("Install httpx: pip install httpx") from exc

    url = f"{base_url}/api/chat"
    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    with httpx.Client(timeout=300.0) as client:
        r = client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
    msg = data.get("message") or {}
    text = msg.get("content")
    if text is None or not isinstance(text, str):
        return json.dumps(data, indent=2)[:8000]
    return text


def run_stage(label: str, priorities: str, *, base_url: str, model: str) -> None:
    print("\n" + "=" * 72)
    print(label)
    print("=" * 72 + "\n")
    user = build_user_message(priorities)
    try:
        reply = ollama_chat(SYSTEM_PROMPT, user, base_url=base_url, model=model)
    except Exception as e:
        print(f"Error calling Ollama: {e}", file=sys.stderr)
        print(
            f"Is `ollama serve` running? Is the model installed? try: ollama pull {model}",
            file=sys.stderr,
        )
        raise
    print(reply)
    print()


def main() -> None:
    p = argparse.ArgumentParser(description="Wedding venue decider (local Ollama) — see ACTIVITY_decider.md")
    p.add_argument(
        "--stage",
        type=int,
        choices=(1, 2),
        default=None,
        help="Run only stage 1 or 2 priorities (default: run both in order).",
    )
    p.add_argument("--host", default=OLLAMA_HOST, help="Ollama base URL (default: env OLLAMA_HOST or 127.0.0.1:11434)")
    p.add_argument("--model", default=OLLAMA_MODEL, help="Model name (default: env OLLAMA_MODEL or llama3.2)")
    args = p.parse_args()

    base = args.host.rstrip("/")
    model = args.model.strip()

    if args.stage == 1:
        run_stage("STAGE 1 — Base couple priorities", PRIORITIES_STAGE1, base_url=base, model=model)
    elif args.stage == 2:
        run_stage("STAGE 2 — Shifted priorities", PRIORITIES_STAGE2, base_url=base, model=model)
    else:
        run_stage("STAGE 1 — Base couple priorities", PRIORITIES_STAGE1, base_url=base, model=model)
        run_stage("STAGE 2 — Shifted priorities", PRIORITIES_STAGE2, base_url=base, model=model)


if __name__ == "__main__":
    main()
