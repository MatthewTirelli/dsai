# 05_acrostic_sentence_tools.py
# Sentence transform + acrostic tools (Ollama function calling)
# Uses the same agent() wrapper and /api/chat pattern as functions.py

# Run from this folder:
#   cd 08_function_calling && python 05_acrostic_sentence_tools.py
# Requires: Ollama on :11434, model smollm2:1.7b (tools-capable), pip install requests

# 0. SETUP ###################################

import json
from collections import defaultdict

from functions import agent

## 0.1 Configuration #################################

MODEL = "smollm2:1.7b"

# Demo sentence (change if you like)
SAMPLE_SENTENCE = "Poetry hides where language opens every secret heart silently."

# 1. TOOL IMPLEMENTATIONS ###################################

# These names must match the "name" field in the tool metadata below.


def remove_every_fifth_letter(sentence: str) -> dict:
    """
    Remove every 5th character from sentence (1-based positions 5, 10, 15, ...).
    Returns the shortened text and the list of removed characters in order.
    """
    if not isinstance(sentence, str):
        sentence = str(sentence)
    removed: list[str] = []
    kept: list[str] = []
    for i, ch in enumerate(sentence, start=1):
        if i % 5 == 0:
            removed.append(ch)
        else:
            kept.append(ch)
    return {
        "filtered_sentence": "".join(kept),
        "removed_letters": removed,
        "removed_count": len(removed),
    }


# First word of each line starts with this letter (used for acrostic lines).
# Multiple entries per letter rotate when the same letter appears twice in ``removed_letters``.
LETTER_LINES: dict[str, list[str]] = {
    "A": [
        "Always the quiet ink remembers the page,",
        "After rain, the pavement breathes glass,",
    ],
    "B": [
        "Beneath every roof a different weather waits,",
        "Bright thresholds lean toward the road,",
    ],
    "C": [
        "Curious hands unroll the brittle map,",
        "Cold stars rehearse an older grammar,",
    ],
    "D": [
        "Dawn threads the keyhole with pale insistence,",
        "Deep in the well the echo trades names,",
    ],
    "E": [
        "Every sentence owes a debt to silence,",
        "Evening folds the hills like linen,",
    ],
    "F": [
        "Fragile vows keep time with the kettle,",
        "Far from the harbor the gulls still argue,",
    ],
    "G": [
        "Gentle as fog, the news arrives,",
        "Gray light inventories the orchard,",
    ],
    "H": [
        "Hinges remember the weight of leaving,",
        "Hollow stones return the river’s vowels,",
    ],
    "I": [
        "Ink is a small door you paint by hand,",
        "In the margin a moth rehearses snow,",
    ],
    "J": [
        "Just so, the morning leans its shoulder in,",
        "Jasmine and iron trade the same window,",
    ],
    "K": [
        "Keen edges soften where thumbs have worn them,",
        "Kindness is a draft you proofread aloud,",
    ],
    "L": [
        "Language opens a borrowed coat,",
        "Late trains braid the city’s copper hair,",
    ],
    "M": [
        "Morning invents another name for blue,",
        "Maps are prayers the road corrects,",
    ],
    "N": [
        "No single bell can ring both dusk and tide,",
        "Narrow boats carry the sky in parcels,",
    ],
    "O": [
        "Often the porch light outlives the story,",
        "Old keys still fit a door that moved,",
    ],
    "P": [
        "Paper holds the ghost of rain,",
        "Pale footsteps salt the frozen pier,",
    ],
    "Q": [
        "Quiet rooms hoard the loudest fractions,",
        "Quicksilver grammar slips the lock,",
    ],
    "R": [
        "Right you are when daylight thumbs the diary,",
        "Rivers rehearse the same forgiving curve,",
    ],
    "S": [
        "Slow clocks teach a patient alphabet,",
        "Salt and vowels agree along the tongue,",
    ],
    "T": [
        "Turn where the fence gives up its splinters,",
        "Thin ice rehearses a braver paragraph,",
    ],
    "U": [
        "Under the lintel a draft rehearses home,",
        "Unlikely sparks still nurse the kindling,",
    ],
    "V": [
        "Velvet dusk unbuttons the horizon,",
        "Voices fray where the wires pretend dawn,",
    ],
    "W": [
        "Waking, we translate the bird’s rough news,",
        "Windows loan their glass to other weather,",
    ],
    "X": [
        "Exacting light trials every narrow step,",
        "Xeric wind files the canyon smooth,",
    ],
    "Y": [
        "You were the draft that taught the door to hum,",
        "Yellow leaves apostrophe the quiet street,",
    ],
    "Z": [
        "Zero is not the finish of counting,",
        "Zinc sky hoards a coin of unspent thunder,",
    ],
}


def acrostic_from_letters(letters: list) -> str:
    """
    One poem line per alphabetic letter in order. Each line is a full phrase whose **first
    word** begins with that letter (e.g. ``R`` → "Right you are..."). Non-letters are
    skipped. Repeated letters take the next variant from :data:`LETTER_LINES`.
    """
    if isinstance(letters, str):
        s = letters.strip()
        letters = json.loads(s) if s else []
    if not isinstance(letters, list):
        letters = list(letters)
    pick = defaultdict(int)  # per-letter index into variants
    lines: list[str] = []
    for raw in letters:
        token = str(raw).strip()
        if not token:
            continue
        letter_char = token[0]
        if not letter_char.isalpha():
            continue
        letter = letter_char.upper()
        pool = LETTER_LINES.get(letter)
        if not pool:
            lines.append(
                f"(Add a LETTER_LINES['{letter}'] list—first word of each line must start with {letter}.)"
            )
            continue
        i = pick[letter] % len(pool)
        pick[letter] += 1
        line = pool[i]
        lines.append(line[0].upper() + line[1:] if line else line)
    if not lines:
        return "(no letters — empty acrostic)"
    return "\n".join(lines)


# 2. TOOL METADATA (Ollama / OpenAI-style tool schema) ################


tool_remove_every_fifth_letter = {
    "type": "function",
    "function": {
        "name": "remove_every_fifth_letter",
        "description": (
            "Remove every 5th character (positions 5, 10, 15, ...) from a sentence. "
            "Returns filtered text and the removed letters as a list."
        ),
        "parameters": {
            "type": "object",
            "required": ["sentence"],
            "properties": {
                "sentence": {
                    "type": "string",
                    "description": "The input sentence to transform",
                }
            },
        },
    },
}

tool_acrostic_from_letters = {
    "type": "function",
    "function": {
        "name": "acrostic_from_letters",
        "description": (
            "Given an ordered list of letters (characters), build a short poem "
            "with one line per letter, each line beginning with that letter."
        ),
        "parameters": {
            "type": "object",
            "required": ["letters"],
            "properties": {
                "letters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ordered letters to begin each line, e.g. [\"P\", \"t\", \"y\"]",
                }
            },
        },
    },
}


def _first_tool_output(resp):
    """Extract Python object from first tool call on this stack (or None)."""
    if isinstance(resp, list) and resp:
        return resp[0].get("output")
    return None


# 3. DEMO: agent + tools ###################################


def main():
    print("Sentence:", SAMPLE_SENTENCE)
    print()

    # --- Step 1: remove every 5th letter ---
    messages1 = [
        {
            "role": "user",
            "content": (
                "Call remove_every_fifth_letter exactly once. "
                f"The sentence argument must be this exact string: {json.dumps(SAMPLE_SENTENCE)}"
            ),
        }
    ]
    resp1 = agent(
        messages=messages1,
        model=MODEL,
        output="tools",
        tools=[tool_remove_every_fifth_letter],
    )
    print("--- Tool 1 (remove every 5th letter) — raw tool_calls ---")
    print(resp1)
    print()

    removal = _first_tool_output(resp1)
    if not isinstance(removal, dict):
        removal = remove_every_fifth_letter(SAMPLE_SENTENCE)
        print(
            "(Note: model did not return a dict payload; using direct remove_every_fifth_letter.)"
        )

    removed_letters = removal.get("removed_letters", [])
    print("Filtered sentence:", removal.get("filtered_sentence", ""))
    print("Removed letters (in order):", removed_letters)
    print()

    # --- Step 2: acrostic from those letters ---
    letters_json = json.dumps(removed_letters)
    messages2 = [
        {
            "role": "user",
            "content": (
                "Call acrostic_from_letters exactly once. "
                f"The letters argument must be this JSON array: {letters_json}"
            ),
        }
    ]
    resp2 = agent(
        messages=messages2,
        model=MODEL,
        output="tools",
        tools=[tool_acrostic_from_letters],
    )
    print("--- Tool 2 (acrostic) — poem from tool output ---")
    poem = _first_tool_output(resp2)
    if isinstance(poem, str) and poem.strip():
        print(poem)
    else:
        poem = acrostic_from_letters(removed_letters)
        print(poem)
        print(
            "\n(Note: model did not return poem text; used acrostic_from_letters in Python.)"
        )
    print()

    # --- Ground truth without LLM (for comparison) ---
    print("--- Same pipeline entirely in Python (no Ollama) ---")
    r = remove_every_fifth_letter(SAMPLE_SENTENCE)
    print(acrostic_from_letters(r["removed_letters"]))


if __name__ == "__main__":
    main()
