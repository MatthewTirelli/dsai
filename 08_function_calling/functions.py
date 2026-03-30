# functions.py
# Function Calling Helper Functions
# Pairs with functions.R
# Tim Fraser

# This script contains functions used for multi-agent orchestration with function calling in Python.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import inspect
import json  # for working with JSON
from pathlib import Path

import pandas as pd  # for data manipulation
import requests  # for HTTP requests

# If you haven't already, install these packages...
# pip install requests pandas

## 0.2 Configuration #################################

# Default model and Ollama connection
DEFAULT_MODEL = "smollm2:1.7b"
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
CHAT_URL = f"{OLLAMA_HOST}/api/chat"

_FUNCTIONS_FILE = Path(__file__).resolve()


def _globals_for_tool_dispatch():
    """
    Tool callables live in the script that invoked agent() or agent_run().
    f_back from agent() alone is correct when students call agent() directly (e.g. 03 script).
    When they use agent_run(), an extra frame in this module would break lookup unless we
    walk the stack until we leave functions.py.
    """
    frame = inspect.currentframe().f_back
    while frame is not None:
        gpath = frame.f_globals.get("__file__")
        if gpath:
            try:
                if Path(gpath).resolve() != _FUNCTIONS_FILE:
                    return frame.f_globals
            except OSError:
                pass
        frame = frame.f_back
    return globals()


def _parse_tool_arguments(raw_args):
    if raw_args is None:
        return {}
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        s = raw_args.strip() or "{}"
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return {}
    return {}


def _resolve_tool_function(caller_globals, func_name):
    if not func_name:
        return None
    fn = caller_globals.get(func_name) or globals().get(func_name)
    if fn is not None:
        return fn
    for key, val in caller_globals.items():
        if callable(val) and key.lower() == func_name.strip().lower():
            return val
    return None


# 1. AGENT FUNCTION ###################################

def agent(messages, model=DEFAULT_MODEL, output="text", tools=None, all=False):
    """
    Agent wrapper function that runs a single agent, with or without tools.
    
    Parameters:
    -----------
    messages : list
        List of message dictionaries with 'role' and 'content' keys.
        Must follow format: [{"role": "system", "content": "..."}, ...]
    model : str
        The model to be used for the agent (default: "smollm2:1.7b")
    output : str
        The output format (default: "text")
    tools : list, optional
        List of tool metadata dictionaries for function calling
    all : bool
        If True, return all responses. If False, return only the last response.
    
    Returns:
    --------
    str or list
        The agent's response(s)
    """
    
    # If the agent has NO tools, perform a standard chat
    if tools is None:
        body = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(CHAT_URL, json=body)
        response.raise_for_status()
        result = response.json()
        
        return result["message"]["content"]
    else:
        # If the agent has tools, perform a tool call
        body = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "stream": False
        }
        
        response = requests.post(CHAT_URL, json=body)
        response.raise_for_status()
        result = response.json()
        
        msg = result.get("message") or {}
        tool_calls = msg.get("tool_calls") or []

        if tool_calls:
            caller_globals = _globals_for_tool_dispatch()
            for tool_call in tool_calls:
                fn_block = tool_call.get("function") or {}
                func_name = fn_block.get("name") or tool_call.get("name")
                raw_args = fn_block.get("arguments", {})
                func_args = _parse_tool_arguments(raw_args)

                func = _resolve_tool_function(caller_globals, func_name)
                if func is None:
                    raise RuntimeError(
                        f"Model requested unknown tool {func_name!r}. "
                        "Define a same-named function in the script that calls agent() or agent_run()."
                    )
                tool_result = func(**func_args)
                tool_call["output"] = tool_result

        if all:
            return result

        if tool_calls:
            if output == "tools":
                return tool_calls
            last_out = tool_calls[-1].get("output")
            if last_out is not None:
                return last_out
            return msg.get("content") or ""

        return result["message"]["content"]


def agent_run(role, task, tools=None, output="text", model=DEFAULT_MODEL):
    """
    Run an agent with a specific role and task.
    
    Parameters:
    -----------
    role : str
        The system prompt defining the agent's role
    task : str
        The user message/task for the agent
    tools : list, optional
        List of tool metadata for function calling
    output : str
        Output format (default: "text")
    model : str
        Model to use (default: DEFAULT_MODEL)
    
    Returns:
    --------
    str
        The agent's response
    """
    
    # Define the messages to be sent to the agent
    messages = [
        {"role": "system", "content": role},
        {"role": "user", "content": task}
    ]
    
    # Run the agent
    resp = agent(messages=messages, model=model, output=output, tools=tools)
    return resp


# 2. DATA CONVERSION FUNCTION ###################################

def df_as_text(df):
    """
    Convert a pandas DataFrame to a markdown table string.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to convert to text
    
    Returns:
    --------
    str
        A markdown-formatted table string
    """
    
    # Convert DataFrame to markdown table
    # pandas to_markdown() method creates markdown tables
    tab = df.to_markdown(index=False)
    return tab
