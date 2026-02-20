# Pediatric Suicide Methods — Script Documentation

## Overview

`pediatric_suicide_methods.py` queries the **CDC injury mortality** dataset via the Socrata Open Data API (SODA). It fetches up to 20 records of **pediatric suicides** (age &lt; 15) and returns selected fields including **injury intent**, **injury mechanism** (method), demographics, and death/population metrics. Output is printed to the console for inspection and reporting.

---

## API Endpoint and Parameters

| Item | Value |
|------|--------|
| **Base URL** | `https://data.cdc.gov/resource/nt65-c7a7.json` |
| **Method** | GET |
| **Auth** | App token in header (see [Usage](#usage)) |

### Query Parameters (SoQL)

| Parameter | Value | Description |
|-----------|--------|-------------|
| `$select` | `year, sex, age_years, race, injury_intent, injury_mechanism, deaths, population, age_specific_rate, unit` | Columns to return |
| `$where` | `injury_intent = 'Suicide' AND age_years = '< 15'` | Filter: suicide, age under 15 |
| `$order` | `year DESC` | Newest years first |
| `$limit` | `20` | Max records returned |

### Headers

| Header | Value | Description |
|--------|--------|-------------|
| `X-App-Token` | *(from `.env`)* | Socrata app token; required for higher rate limits and stable access |

---

## Data Structure

The response is a **JSON array** of record objects. Each record has the following fields (as specified by `$select`):

| Field | Type | Description |
|-------|------|-------------|
| `year` | string/number | Year of the data |
| `sex` | string | Sex (e.g. Male, Female) |
| `age_years` | string | Age group (e.g. `< 15`) |
| `race` | string | Race category |
| `injury_intent` | string | Intent (e.g. Suicide) |
| `injury_mechanism` | string | Mechanism/method of injury |
| `deaths` | number | Number of deaths |
| `population` | number | Population for rate denominator |
| `age_specific_rate` | number | Age-specific rate |
| `unit` | string | Unit for rate (e.g. per 100,000) |

Example record (structure only):

```json
{
  "year": "2020",
  "sex": "Male",
  "age_years": "< 15",
  "race": "...",
  "injury_intent": "Suicide",
  "injury_mechanism": "...",
  "deaths": 123,
  "population": 12345678,
  "age_specific_rate": 0.99,
  "unit": "per 100,000"
}
```

---

## Flow Diagram

Diagrams are rendered as images so they show in any viewer (preview, PDF, GitHub) without the Mermaid extension.

**Flow: setup → request → output**

![Flow diagram](https://mermaid.ink/svg/Z3JhcGggTFIKICAgIHN1YmdyYXBoIFNldHVwCiAgICAgICAgQVtMb2FkIC5lbnZdIC0tPiBCW1JlYWQgU09DUkFUQV9BUFBfVE9LRU5dCiAgICAgICAgQiAtLT4gQ3tUb2tlbiBwcmVzZW50fQogICAgICAgIEMgLS0-fE5vfCBEW1JhaXNlIFZhbHVlRXJyb3JdCiAgICAgICAgQyAtLT58WWVzfCBFW0J1aWxkIFVSTCArIHBhcmFtc10KICAgIGVuZAoKICAgIHN1YmdyYXBoIFJlcXVlc3QKICAgICAgICBFIC0tPiBGW0dFVCB3aXRoIFgtQXBwLVRva2VuXQogICAgICAgIEYgLS0-IEdbUGFyc2UgSlNPTl0KICAgIGVuZAoKICAgIHN1YmdyYXBoIE91dHB1dAogICAgICAgIEcgLS0-IEhbUHJpbnQgc3RhdHVzLCBjb3VudCwga2V5c10KICAgICAgICBIIC0tPiBJW1ByaW50IGZpcnN0IDMgcmVjb3Jkc10KICAgIGVuZA)

**Sequence: Script ↔ Env ↔ API**

![Sequence diagram](https://mermaid.ink/svg/c2VxdWVuY2VEaWFncmFtCiAgICBwYXJ0aWNpcGFudCBTY3JpcHQKICAgIHBhcnRpY2lwYW50IEVudgogICAgcGFydGljaXBhbnQgQVBJCgogICAgU2NyaXB0LT4-RW52OiBsb2FkX2RvdGVudigpCiAgICBTY3JpcHQtPj5FbnY6IGdldCBTT0NSQVRBX0FQUF9UT0tFTgogICAgRW52LS0-PlNjcmlwdDogYXBwX3Rva2VuCiAgICBTY3JpcHQtPj5BUEk6IEdFVCBudDY1LWM3YTcuanNvbiB3aXRoIFNvUUwgcGFyYW1zCiAgICBOb3RlIG92ZXIgQVBJOiBTT0RBIGFwcGxpZXMgZmlsdGVycyBhbmQgcmV0dXJucyBKU09OCiAgICBBUEktLT4-U2NyaXB0OiBKU09OIGFycmF5IG9mIHJlY29yZHMKICAgIFNjcmlwdC0-PlNjcmlwdDogUHJpbnQgc3RhdHVzLCBjb3VudCwgc2FtcGxlIHJlY29yZHM)

<details>
<summary>Mermaid source (edit at <a href="https://mermaid.live">mermaid.live</a>)</summary>

Flow:

```mermaid
graph LR
    subgraph Setup
        A[Load .env] --> B[Read SOCRATA_APP_TOKEN]
        B --> C{Token present}
        C -->|No| D[Raise ValueError]
        C -->|Yes| E[Build URL + params]
    end

    subgraph Request
        E --> F[GET with X-App-Token]
        F --> G[Parse JSON]
    end

    subgraph Output
        G --> H[Print status, count, keys]
        H --> I[Print first 3 records]
    end
```

Sequence:

```mermaid
sequenceDiagram
    participant Script
    participant Env
    participant API

    Script->>Env: load_dotenv()
    Script->>Env: get SOCRATA_APP_TOKEN
    Env-->>Script: app_token
    Script->>API: GET nt65-c7a7.json with SoQL params
    Note over API: SODA applies filters and returns JSON
    API-->>Script: JSON array of records
    Script->>Script: Print status, count, sample records
```

</details>

---

## Usage

### Prerequisites

- Python 3 with `requests` and `python-dotenv` installed:

  ```bash
  pip install requests python-dotenv
  ```

- A **Socrata app token** for `data.cdc.gov`. Request one at [https://data.cdc.gov/profile/edit/developer_settings](https://data.cdc.gov/profile/edit/developer_settings).

### Configuration

1. In the same directory as the script (or project root), create a `.env` file.
2. Add your app token:

   ```env
   SOCRATA_APP_TOKEN=your_token_here
   ```

3. Do not commit `.env`; keep it in `.gitignore`.

### Run the script

From the repo root or from `01_query_api/`:

```bash
python 01_query_api/pediatric_suicide_methods.py
```

Or from inside `01_query_api/`:

```bash
python pediatric_suicide_methods.py
```

### Expected output

- `HTTP status code: 200`
- `Number of records returned: 20` (or fewer if fewer matches)
- `Keys in first record: ['year', 'sex', ...]`
- First 3 records printed as dictionaries

If the token is missing, the script raises `ValueError: Missing SOCRATA_APP_TOKEN in .env`. If the request fails, it prints a truncated error body and re-raises the exception.
