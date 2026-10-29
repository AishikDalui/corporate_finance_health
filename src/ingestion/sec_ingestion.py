"""
SEC Data Ingestion Script

Thought Process:
To analyze Apple's financial health, we need official, audited financial data.
The U.S. Securities and Exchange Commission (SEC) provides an API called EDGAR 
with all company disclosures in XBRL (standardized digital accounting) format.

This script:
1. Connects to the SEC API safely using required credentials.
2. Downloads Apple's complete historical financial facts.
3. Caches the raw data locally so we don't keep hitting the SEC servers.
4. Explores the Revenue ('SalesRevenueNet') data to inspect its raw structure.
"""

import os
import json
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# ==============================================================================
# 1. Load Environment Variables & Security Setup
# Thought Process:
# The SEC strictly requires every API request to include a User-Agent header with 
# the user's name and email. If you don't provide this, the SEC blocks your IP.
# We store this safely in a private `.env` file instead of hardcoding it in the code.
# ==============================================================================
load_dotenv()

user_agent = os.getenv("SEC_EDGAR_USER_AGENT")

# Stop immediately if user agent is missing, before making a failed request
if not user_agent:
    raise ValueError("SEC_EDGAR_USER_AGENT is not configured in .env")


# ==============================================================================
# 2. Request Financial Data from SEC EDGAR API
# Thought Process:
# Every public company has a unique SEC identifier called a CIK (Central Index Key).
# Apple's CIK is 0000320193. We call the SEC company facts endpoint to get all
# historical XBRL facts Apple has ever reported.
# ==============================================================================
headers = {
    "User-Agent": user_agent,          # SEC compliance: tells SEC who is requesting
    "Accept-Encoding": "gzip, deflate", # Ask for compressed data to download faster
    "Host": "data.sec.gov"
}

# Apple's 10-digit SEC identifier
cik = "0000320193"

# Official SEC endpoint for company facts
url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# Send the HTTP GET request with a 30-second timeout so the script won't hang indefinitely
response = requests.get(url, headers=headers, timeout=30)

print("Status code:", response.status_code)

# If the request failed (e.g. 403 Forbidden or 404 Not Found), throw an error
response.raise_for_status()

# Convert the received JSON text into a Python dictionary
data = response.json()

# Quick sanity check: verify company name and number of recorded financial concepts
print("Company:", data["entityName"])
print("Number of facts:", len(data["facts"]))


# ==============================================================================
# 3. Save Raw Data Locally (Caching)
# Thought Process:
# The SEC limits request frequency (max 10 requests/sec), and downloading entire 
# company facts repeatedly is slow. We save the raw JSON to disk once so our team 
# can work offline or re-run analyses instantly without re-downloading.
# ==============================================================================
raw_data_path = Path("data/raw/apple_companyfacts.json")

# Ensure the parent folder (data/raw) exists; if not, create it automatically
raw_data_path.parent.mkdir(parents=True, exist_ok=True)

# Save the full data as pretty-printed JSON (indent=2 makes it human-readable)
with open(raw_data_path, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

print(f"Raw data saved to: {raw_data_path}")


# ==============================================================================
# 4. Extract Revenue Concept Metadata
# Thought Process:
# Under US GAAP accounting rules, companies report top-line revenue using standard tags.
# Apple reports net sales under the concept 'SalesRevenueNet'. Let's look up its 
# official description and how units are measured.
# ==============================================================================
revenue_data = data["facts"]["us-gaap"]["SalesRevenueNet"]

print("Concept:", "SalesRevenueNet")
print("Label:", revenue_data["label"])
print("Description:", revenue_data["description"])

# Show available currencies/units (e.g., 'USD')
print("\nAvailable units:")
print(revenue_data["units"].keys())


# ==============================================================================
# 5. Extract USD Revenue Observations
# Thought Process:
# We only care about monetary figures reported in US Dollars (USD).
# We pull out the list of all historical revenue observations.
# ==============================================================================
revenue_observations = revenue_data["units"]["USD"]

print("\nNumber of revenue observations:", len(revenue_observations))

# Preview the first 5 records to understand the dictionary structure (dates, form, value)
print("\nFirst 5 observations:")
for observation in revenue_observations[:5]:
    print(observation)


# ==============================================================================
# 6. Convert Observations to a Tabular DataFrame
# Thought Process:
# Raw nested dictionaries are hard to slice and filter.
# Converting to a pandas DataFrame gives us an organized spreadsheet-like table.
# ==============================================================================
revenue_df = pd.DataFrame(revenue_observations)

print("\nDataFrame:")
print(revenue_df.head())

print("\nColumns:")
print(revenue_df.columns)


# ==============================================================================
# 7. Basic Data Inspection & Duplicate Detection
# Thought Process:
# Before using any data, we need to inspect it to discover data quality issues:
# - What forms are included? (10-K annuals, 10-Q quarterlies, 8-K events)
# - What fiscal periods exist? (FY = full year, Q1/Q2/Q3 = quarters)
# - Are there duplicate records for the same time period? (Yes! Companies re-report past numbers)
# ==============================================================================
print("\nShape:")
print(revenue_df.shape)

print("\nColumn names:")
print(revenue_df.columns.tolist())

# Count how many records come from each SEC form type
print("\nFiling type counts:")
print(revenue_df["form"].value_counts())

# Count how many records belong to each fiscal period tag
print("\nFiscal period counts:")
print(revenue_df["fp"].value_counts())

# Check for duplicate reporting periods:
# Find rows where the start date and end date are identical.
# This proves that the raw data contains overlapping entries that need deduplication.
print("\nDuplicate reporting periods:")
print(
    revenue_df[
        revenue_df.duplicated(
            subset=["start", "end"],
            keep=False
        )
    ][["start", "end", "val", "form", "filed"]]
    .sort_values(["start", "end", "filed"])
)