import os
import requests
from sodapy import Socrata
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get the Socrata App Token from the environment
APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

# Create Socrata client
client = Socrata(
    "data.cdc.gov",
    APP_TOKEN
)

# Make API call: get the first record only
results = client.get(
    "nt65-c7a7",   # dataset ID
    limit=1
)

# Print the first entry
print(results[0])
print(list(results[0].keys()))

#To get status Check


url = "https://data.cdc.gov/resource/nt65-c7a7.json"

headers = {
    "X-App-Token": os.getenv("SOCRATA_APP_TOKEN")
}

response = requests.get(url, headers=headers, params={"$limit": 1})

print("HTTP status code:", response.status_code)
print(results[0])