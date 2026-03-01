# 02_ollama.py
# Query Ollama LLM
# Pairs with 02_ollama.R
# Tim Fraser

# This script demonstrates how to query a local Ollama LLM instance using Python.
# Students will learn how to make HTTP POST requests to interact with language models
# running locally on their machine.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import requests  # for HTTP requests
import json      # for working with JSON

# Starting message
print("\n🚀 Sending LLM query in Python...\n")

# If you haven't already, install the requests package...
# pip install requests

## 0.2 Configure Connection #########################

# Set the port where Ollama is running
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
url = f"{OLLAMA_HOST}/api/generate"

## 0.3 Construct Request Body #######################

# Build the request body as a dictionary
# This tells Ollama which model to use and what prompt to send
# Use a model you have pulled: ollama pull smollm2:1.7b  or  ollama pull llama3.2:3b
# Run "ollama list" to see installed models.
body = {
    "model": "smollm2:1.7b",  # Small, fast model; must be pulled first: ollama pull smollm2:1.7b
    "prompt": "Is model working?",  # User prompt
    "stream": False  # Non-streaming response
}

# 1. SEND REQUEST ###################################

# Build and send the POST request to the Ollama REST API
# The requests library makes it easy to send HTTP requests
# Timeout so we don't hang if Ollama isn't running
try:
    response = requests.post(url, json=body, timeout=120)
except requests.exceptions.ConnectionError:
    print("Connection failed. Is Ollama running? Start it with: ollama serve")
    exit(1)
except requests.exceptions.Timeout:
    print("Request timed out. Ollama may be loading the model.")
    exit(1)

# 2. PARSE RESPONSE ################################

# Ollama returns 200 even for some errors; check JSON for "error" key
response_data = response.json()

# Check for API error (e.g. model not found)
if "error" in response_data:
    print("Ollama error:", response_data["error"])
    print("Tip: Pull the model first, e.g.  ollama pull smollm2:1.7b")
    exit(1)

# Extract the model's reply (key is "response" for /api/generate)
output = response_data.get("response", "")
if output:
    print(output)
else:
    print("No 'response' in reply. Keys:", list(response_data.keys()))

# Closing message
print("\n✅ LLM query complete. Exiting Python...\n")
