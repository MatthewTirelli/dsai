# Project Pug

## 📌 Overview

**Project Pug** is a Python application that fetches pug adoption listings in the USA from an external API. It extracts key details for each dog, structures the data, and saves the results to a CSV file for analysis or reporting.

## ✨ Features

- **API integration** — Pulls pug adoption data from a USA-focused API
- **Structured fields** — Breaks down each listing into:
  - Name
  - Age
  - Gender
  - Health conditions
- **CSV export** — Saves all extracted information into a `.csv` file for use in spreadsheets or other tools

## ⚙️ Requirements

- Python 3.7 or higher
- Dependencies (e.g. `requests`, `pandas` or `csv` stdlib) as defined in the project

## 📦 Installation

1. Clone or download the project.
2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

Run the script from the project directory:

```bash
python pug_finder.py
```

Or from the repo root:

```bash
python HW/pug_finder.py
```

Ensure any required API keys or configuration (e.g. `.env`) are set before running.

## 📁 Project Structure

```
HW/
├── pug_finder.py          # Main script: API fetch and CSV export
├── pug_finder_README.md   # This file
└── (output)               # Generated CSV written here (see script)
```

## 📊 Output

- The script produces a **CSV file** (e.g. `pug_adoptions.csv`) containing one row per pug with columns such as:
  - `name`
  - `age`
  - `gender`
  - `health_conditions`
- Open the CSV in Excel, Google Sheets, or any data tool for further analysis.
