# 03_agents_with_function_calling.py
# Agents with Function Calling
# Pairs with 03_agents_with_function_calling.R
# Tim Fraser

# This script demonstrates how to build agents that can use function calling.
# Students will learn how to create agent wrapper functions and use multiple tools.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import ast
import json  # for working with JSON

import pandas as pd  # for data manipulation
import requests  # for HTTP requests

# If you haven't already, install these packages...
# pip install requests pandas

## 0.2 Load Functions #################################

# Load helper functions for agent orchestration
from functions import agent

## 0.3 Configuration #################################

# Select model of interest
MODEL = "smollm2:1.7b"

# 1. DEFINE FUNCTIONS TO BE USED AS TOOLS ###################################

# Define a function to be used as a tool
def add_two_numbers(x, y):
    """Add two numbers together."""
    return x + y

# Define another function to be used as a tool
def get_table(df):
    """
    Convert a pandas DataFrame into a markdown table.

    The LLM usually passes ``df`` as JSON (dict/list); coerce to DataFrame when needed.
    Tool APIs may send ``df`` as an empty string or Python-literal-ish text; parse defensively.
    """
    if isinstance(df, str):
        s = df.strip()
        if not s:
            return pd.DataFrame({"note": ["(empty df argument from model)"]}).to_markdown(
                index=False
            )
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(s)
            except (ValueError, SyntaxError) as exc:
                raise ValueError(
                    f"get_table: could not parse df as JSON or Python literal: {s!r}"
                ) from exc
        df = _dataframe_from_parsed(parsed)
    elif isinstance(df, dict):
        df = _dataframe_from_parsed(df)
    elif not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    return df.to_markdown(index=False)


def _dataframe_from_parsed(parsed):
    """Build a DataFrame from dict, list, or scalar."""
    if isinstance(parsed, dict):
        try:
            return pd.DataFrame(parsed)
        except ValueError:
            return pd.DataFrame([parsed])
    if isinstance(parsed, list):
        return pd.DataFrame(parsed)
    return pd.DataFrame([{"value": parsed}])

# 2. DEFINE TOOL METADATA ###################################

# Define the tool metadata for add_two_numbers
tool_add_two_numbers = {
    "type": "function",
    "function": {
        "name": "add_two_numbers",
        "description": "Add two numbers",
        "parameters": {
            "type": "object",
            "required": ["x", "y"],
            "properties": {
                "x": {
                    "type": "number",
                    "description": "first number"
                },
                "y": {
                    "type": "number",
                    "description": "second number"
                }
            }
        }
    }
}

# Define the tool metadata for get_table
tool_get_table = {
    "type": "function",
    "function": {
        "name": "get_table",
        "description": "Convert a data.frame into a markdown table",
        "parameters": {
            "type": "object",
            "required": ["df"],
            "properties": {
                "df": {
                    "type": "object",
                    "description": "The data.frame to convert to a markdown table using pandas to_markdown()"
                }
            }
        }
    }
}

# 3. EXAMPLE 1: STANDARD CHAT (NO TOOLS) ###################################

# Trying to call a standard chat without tools
# The agent() function from functions.py handles this automatically
messages = [
    {"role": "user", "content": "Write a haiku about cheese."}
]

resp = agent(messages=messages, model=MODEL, output="text")
print("📝 Standard Chat Response:")
print(resp)
print()

# 4. EXAMPLE 2: TOOL CALL #1 ###################################

# Try calling tool #1 (add_two_numbers)
messages = [
    {"role": "user", "content": "Add 3 + 5."}
]

resp = agent(messages=messages, model=MODEL, output="tools", tools=[tool_add_two_numbers])
print("🔧 Tool Call #1 Result:")
print(resp)
print()

# Access the output from the tool call
if isinstance(resp, list) and len(resp) > 0:
    print(f"Tool output: {resp[0].get('output', 'No output')}")
    print()

# 5. EXAMPLE 3: TOOL CALL #2 ###################################

# Try calling tool #2 (get_table)
# First, create a simple DataFrame with the result from tool #1
result_value = resp[0].get("output", 0) if isinstance(resp, list) else 0
df = pd.DataFrame({"x": [result_value]})

# Be explicit: small models often skip tools or send empty df unless the JSON payload is spelled out.
df_json = json.dumps({"x": [result_value]})
messages = [
    {
        "role": "user",
        "content": (
            "Call the get_table tool once. Set argument df to a string that is exactly this JSON: "
            f"{df_json}"
        ),
    }
]

resp2 = agent(messages=messages, model=MODEL, output="tools", tools=[tool_get_table])
print("🔧 Tool Call #2 Result (markdown table from tool):")
# If the model returns plain text or an empty tool output, show fallback using the same df as "Manual" below.
md_from_tool = None
if isinstance(resp2, list) and len(resp2) > 0:
    _o = resp2[0].get("output")
    if isinstance(_o, str) and _o.strip():
        md_from_tool = _o
if md_from_tool:
    print(md_from_tool)
else:
    print(get_table({"x": [result_value]}))
    print(
        "\n(Note: No non-empty markdown from the model’s tool call — showing get_table() "
        "on the pipeline DataFrame so you still see the expected table.)"
    )
print()

# Compare against manual approach
print("📊 Manual Table Creation:")
manual_table = df.to_markdown(index=False)
print(manual_table)
print()

# Note: We can use the agent() function to rapidly build and test out agents with or without tools.
