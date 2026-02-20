import os
import requests
from dotenv import load_dotenv

"""
API name: Socrata Open Data API (SODA) via data.cdc.gov
Dataset ID: nt65-c7a7
Endpoint: https://data.cdc.gov/resource/nt65-c7a7.json

Query purpose:
- Analyze pediatric suicides
- Filter to injury_intent = 'Suicide'
- Filter to age_years = '< 15'
- Group by year and injury mechanism (method)
- Return 20 aggregated rows
- Display the first 10 rows for reporting
-This will return the number of deaths by year and injury mechanism for pediatric suicides.
"""

def main():
    # Load environment variables from .env
    load_dotenv()

    app_token = os.getenv("SOCRATA_APP_TOKEN")
    if not app_token:
        raise ValueError("Missing SOCRATA_APP_TOKEN in .env file")

    url = "https://data.cdc.gov/resource/nt65-c7a7.json"

    # API query parameters
    params = {
        "$select": "year, injury_mechanism, sum(deaths) as total_deaths",
        "$where": "injury_intent = 'Suicide' AND age_years = '< 15'",
        "$group": "year, injury_mechanism",
        "$order": "year ASC, total_deaths DESC",
        "$limit": 20
    }

    headers = {
        "X-App-Token": app_token
    }

    # Make API request
    response = requests.get(url, headers=headers, params=params, timeout=30)

    # Print HTTP status code (required)
    print("HTTP status code:", response.status_code)

    # Stop if request failed
    response.raise_for_status()

    data = response.json()

    # Document results
    print("Number of records returned:", len(data))
    print("Keys in first record:", list(data[0].keys()))

    # Display first 10 rows
    print("\nFirst 10 rows:")
    for row in data[:10]:
        print(row)

if __name__ == "__main__":
    main()