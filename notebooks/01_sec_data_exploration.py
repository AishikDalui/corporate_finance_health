# %% [markdown]
# # Apple SEC Financial Data Cleaning & Exploration
# Goal: Extract, clean, and validate Apple Inc.'s annual revenue, operating income, and net income from raw SEC XBRL data to create a consolidated income statement table.

# %% [markdown]
# ### Step 1: Load Environment & Modules
# Load the SEC user-agent header from `.env` and import our cleaning functions from `sec_cleaning.py`.

# %%
# Step 1: Imports and setup
# Thought Process:
# We need helper libraries to make web requests, read JSON files, manipulate tables,
# and securely read our credentials from a hidden .env file.
import os
import json
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Allow importing our custom cleaning helper functions from the 'src' directory
import sys
sys.path.insert(0, "../src")

from cleaning.sec_cleaning import (
    add_period_days,
    filter_annual_periods,
    apply_filing_priority,
    select_one_record_per_period,
    select_one_record_per_date
)

# Load secret API settings (like our user-agent email) from the .env file
load_dotenv()

user_agent = os.getenv("SEC_EDGAR_USER_AGENT")

# Safety check: if user_agent isn't configured, stop immediately with an informative message
if not user_agent:
    raise ValueError("SEC_EDGAR_USER_AGENT is not configured in .env")

# %% [markdown]
# ### Step 2: Fetch Apple Data from SEC API
# Download all historical financial facts for Apple (CIK `0000320193`) from the SEC EDGAR API.

# %%
# Step 2: API request
# Thought Process:
# The SEC requires us to identify ourselves via the User-Agent header.
# Apple's unique SEC identifier (CIK) is 0000320193. We request all historical numbers in one go.
headers = {
    "User-Agent": user_agent,          # Who is asking for data (required by SEC)
    "Accept-Encoding": "gzip, deflate", # Download compressed file for speed
    "Host": "data.sec.gov"
}

cik = "0000320193"  # Apple's official SEC CIK code
url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# Make the network call to SEC EDGAR
response = requests.get(url, headers=headers, timeout=30)
print("Status code:", response.status_code)

# Check if the download was successful (raises error if 404 or 403)
response.raise_for_status()

# Parse the raw JSON response into Python objects
data = response.json()
print("Company:", data["entityName"])
print("Number of facts:", len(data["facts"]))

# %% [markdown]
# ### Step 3: Save Raw Data Locally
# Save the downloaded JSON file to disk so we do not need to call the SEC API again.

# %%
# Step 3: Cache data
# Thought Process:
# SEC data can take time to download and has rate limits. 
# Saving it locally on disk ensures we can work offline and re-run experiments without delays.
raw_data_path = Path("../data/raw/apple_companyfacts.json")
raw_data_path.parent.mkdir(parents=True, exist_ok=True)  # Create folders if they don't exist yet

# Write data as formatted JSON
with open(raw_data_path, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

print(f"Raw data saved to: {raw_data_path}")

# %% [markdown]
# ### Step 4: Check Revenue Concept Metadata
# Look up the `SalesRevenueNet` concept under US-GAAP to verify label, description, and currency.

# %%
# Step 4: Concept details
# Thought Process:
# Public companies report accounting items under standardized US-GAAP tags.
# We inspect 'SalesRevenueNet' to make sure it represents Apple's net sales/revenue.
revenue_data = data["facts"]["us-gaap"]["SalesRevenueNet"]

print("Concept: SalesRevenueNet")
print("Label:", revenue_data["label"])
print("Description:", revenue_data["description"])
print("Available units:", list(revenue_data["units"].keys()))

# %% [markdown]
# ### Step 5: Get USD Revenue Observations
# Extract all USD revenue data points from the JSON.

# %%
# Step 5: Extract observations
# Thought Process:
# Financial facts can be reported in multiple currencies or units (like shares or USD).
# We pull out the list of entries measured specifically in US Dollars (USD).
revenue_observations = revenue_data["units"]["USD"]
print("Number of revenue observations:", len(revenue_observations))

# %% [markdown]
# ### Step 6: Convert to DataFrame
# Put the raw observations into a pandas DataFrame and see the first 5 rows.

# %%
# Step 6: Create DataFrame
# Thought Process:
# A list of dictionaries is clumsy to manipulate.
# Converting it into a DataFrame creates a spreadsheet-style table with columns and rows.
revenue_df = pd.DataFrame(revenue_observations)
revenue_df.head()

# %% [markdown]
# ### Step 7: Inspect Rows, Columns & Form Types
# Check the shape, column names, and count how many of each form type (10-K, 10-Q, 8-K) exist.

# %%
# Step 7: Form & period breakdown
# Thought Process:
# Check the table dimensions and see which filing forms are present.
# 10-K is the annual report, 10-Q is quarterly, and 8-K is special announcements.
print("Shape:", revenue_df.shape)
print("Columns:", revenue_df.columns.tolist())

# Breakdown of filing form types
print("\nForm counts:")
print(revenue_df["form"].value_counts())

# Breakdown of fiscal period tags (e.g. FY = Full Year, Q1/Q2/Q3 = Quarters)
print("\nFiscal period counts:")
print(revenue_df["fp"].value_counts())

# %% [markdown]
# ### Step 8: Find Duplicate Reporting Periods
# Check if multiple rows share the exact same start and end dates.

# %%
# Step 8: Find duplicates
# Thought Process:
# Companies often re-report prior year numbers in future annual reports for comparison.
# This creates duplicate rows covering the exact same time window (start and end dates).
duplicate_periods = revenue_df[
    revenue_df.duplicated(subset=["start", "end"], keep=False)
]

# View the duplicate rows sorted by dates to see which numbers changed or repeated
duplicate_periods[
    ["start", "end", "val", "form", "filed"]
].sort_values(["start", "end", "filed"])

# %% [markdown]
# ### Step 9: Cross-Tabulate Form vs. Fiscal Period
# See which form types report full year (FY) versus quarterly periods (Q1, Q2, Q3).

# %%
# Step 9: Form vs FP cross-tab
# Thought Process:
# Let's cross-reference forms with fiscal periods to verify if 10-K only reports 'FY'
# and 10-Q only reports quarters.
pd.crosstab(revenue_df["form"], revenue_df["fp"])

# %% [markdown]
# ### Step 10: Preview Rows Marked as FY
# Notice that some rows tagged with `fp == 'FY'` are only 90 days long, not full years.

# %%
# Step 10: Preview FY rows
# Thought Process:
# Discovery: Some rows labeled with fiscal period 'FY' only span 3 months!
# We cannot simply trust the 'fp' label to find full-year annual figures.
revenue_df[
    revenue_df["fp"] == "FY"
][["start", "end", "val", "form", "filed", "fy", "fp"]].head(10)

# %% [markdown]
# ### Step 11: Calculate Period Length in Days
# Use `add_period_days` from `sec_cleaning.py` to calculate the real number of days between start and end dates.

# %%
# Step 11: Add period_days column
# Thought Process:
# Instead of trusting labels, we compute the real elapsed duration: end date minus start date.
revenue_df = add_period_days(revenue_df)

# Preview to inspect the newly created period_days column alongside other fields
revenue_df[
    revenue_df["fp"] == "FY"
][["start", "end", "period_days", "val", "form", "filed", "fy", "fp"]].head(20)

# %% [markdown]
# ### Step 12: Summary Statistics of Period Length
# Check minimum, maximum, and average period duration.

# %%
# Step 12: Stats for period_days
# Thought Process:
# Inspect the distribution of durations to see the minimum, maximum, and typical period lengths.
revenue_df["period_days"].describe()

# %% [markdown]
# ### Step 13: Plot Distribution of Period Lengths
# Plot a bar chart showing the two main groups: quarterly reports (~90 days) and annual reports (~365 days).

# %%
# Step 13: Plot period distribution
# Thought Process:
# A quick visual check shows the data naturally divides into two big clusters:
# 1) Quarterly reports around ~90 days
# 2) Full annual reports around ~365 days
revenue_df["period_days"].value_counts().sort_index().plot(
    kind="bar",
    figsize=(10, 5),
    title="Distribution of SEC Revenue Reporting Periods"
)

# %% [markdown]
# ### Step 14: Filter for Annual Periods (350 to 380 Days)
# Use `filter_annual_periods` from `sec_cleaning.py` to keep only observations between 350 and 380 days.

# %%
# Step 14: Keep only ~1-year periods
# Thought Process:
# Apple's fiscal year is usually 52 or 53 weeks (roughly 364-371 days).
# Keeping rows between 350 and 380 days isolates all true annual reports and drops quarters.
annual_candidates = filter_annual_periods(revenue_df)

# Preview the filtered annual candidate rows
annual_candidates[
    ["start", "end", "period_days", "val", "form", "filed", "fy", "fp"]
].head(20)

# %% [markdown]
# ### Step 15: Count Records Per Period
# Count how many records exist for each unique year to see where duplicates remain.

# %%
# Step 15: Group by period
# Thought Process:
# For each 1-year period, count how many duplicate records exist.
# Some years will have 2 or 3 records because of subsequent comparative filings.
period_counts = (
    annual_candidates
    .groupby(["start", "end"])
    .size()
    .reset_index(name="record_count")
)
period_counts

# %% [markdown]
# ### Step 16: Check Comparative Filings (FY2009 Example)
# See how Apple re-reported FY2009 in 2009, 2010, and 2011 filings.

# %%
# Step 16: FY2009 duplicates
# Thought Process:
# Why do duplicates exist? When companies file their 10-K, they usually include the 
# past 2-3 years for side-by-side comparison. For example, FY2009 was reported in 2009,
# 2010, and 2011. Let's see all entries for that single period to understand the differences.
annual_candidates[
    (annual_candidates["start"] == "2008-09-28") &
    (annual_candidates["end"] == "2009-09-26")
][["start", "end", "val", "form", "filed", "fy", "fp", "frame"]].sort_values("filed")

# %% [markdown]
# ### Step 17: View All Annual Candidates Sorted by Date
# Sort by start date and filing date to see all candidates chronologically.

# %%
# Step 17: Sort candidates
# Thought Process:
# Order the records by date so we can inspect how filings evolved over time.
annual_candidates[
    ["start", "end", "val", "form", "filed", "fy", "fp"]
].sort_values(["start", "filed"])

# %% [markdown]
# ### Step 18: Deduplication (Keep Latest Filing Date)
# Sort by start, end, and filed date, keeping only the most recent record for each period.

# %%
# Step 18: Deduplicate by latest filing
# Thought Process:
# First simple deduplication attempt: For any given financial year, if there are multiple filings,
# keep the most recently filed one (since newer filings often contain corrections or restatements).
annual_clean = (
    annual_candidates
    .sort_values(["start", "end", "filed"])
    .drop_duplicates(subset=["start", "end"], keep="last")
    .copy()
)

# %% [markdown]
# ### Step 19: Inspect Cleaned Annual Data
# Check the cleaned annual table and see row reduction.

# %%
# Step 19: Verify cleaned data
# Thought Process:
# Validate our first deduplication: confirm row count dropped to exactly 1 record per year,
# and check which forms were preserved.
print("Rows before cleaning:", len(annual_candidates))
print("Rows after cleaning:", len(annual_clean))
print("\nForm distribution:")
print(annual_clean["form"].value_counts())

# Preview the clean table sorted from oldest to newest year
annual_clean[["start", "end", "val", "form", "filed"]].sort_values("start")

# %% [markdown]
# ### Step 20: Apply Form Priority Hierarchy
# Use `apply_filing_priority` and `select_one_record_per_period` from `sec_cleaning.py` to give highest priority to 10-K/A (amendments), then 10-K, then 8-K.

# %%
# Step 20: Form priority selection
# Thought Process:
# A more robust deduplication rule:
# 1. 10-K/A (amended report) is most trusted (Rank 1).
# 2. 10-K (official audited annual report) is next (Rank 2).
# 3. 8-K is lowest priority (Rank 3).
# If tied, pick the latest filing date.
annual_candidates = apply_filing_priority(annual_candidates)
annual_clean = select_one_record_per_period(annual_candidates)

# Check the final deduplicated revenue records with their assigned form priority
annual_clean[["start", "end", "val", "form", "filed", "form_priority"]]

# %% [markdown]
# ### Step 21: Convert Revenue to Billions & Calculate YoY Growth
# Convert nominal values to billions ($B) and compute year-over-year revenue growth percentage.

# %%
# Step 21: Revenue in billions & growth %
# Thought Process:
# Raw numbers like $394,328,000,000 are hard to read at a glance.
# Dividing by 1 billion converts them into clean, human-readable numbers (e.g. $394.33B).
# Then calculate Year-over-Year (YoY) percentage change to see how fast Apple grew each year.
annual_clean["revenue_billion"] = annual_clean["val"] / 1_000_000_000
annual_clean = annual_clean.sort_values("end").copy()

# YoY growth = (current year - previous year) / previous year * 100
annual_clean["revenue_growth_pct"] = annual_clean["revenue_billion"].pct_change() * 100

# Preview end dates, revenue in billions, and growth rate rounded to 2 decimal places
annual_clean[["end", "revenue_billion", "revenue_growth_pct"]].round({"revenue_billion": 2, "revenue_growth_pct": 2})

# %% [markdown]
# ### Step 22: Plot Annual Revenue Trend
# Plot a line chart of Apple's historical annual revenue.

# %%
# Step 22: Plot revenue trend
# Thought Process:
# Visualize the growth trajectory over the past decade or two with a clean line chart.
annual_clean.plot(
    x="end",
    y="revenue_billion",
    kind="line",
    marker="o",
    figsize=(10, 5),
    title="Apple Annual Revenue Trend ($ Billions)"
)

# %% [markdown]
# ### Step 23: Save Cleaned Data to CSV
# Save the final cleaned DataFrame to `data/cleaned/apple_annual_revenue.csv`.

# %%
# Step 23: Export to CSV
# Thought Process:
# Save the polished, deduplicated revenue table to CSV for downstream reporting (e.g. Power BI, dashboards).
export_path = "../data/cleaned/apple_annual_revenue.csv"
annual_clean.to_csv(export_path, index=False)
print("Saved to CSV:", os.path.exists(export_path))

# %% [markdown]
# ### Step 24: Search Other Financial Concepts in XBRL Data
# Search all accounting concepts in the data for revenue, cost, gross profit, operating income, and net income.

# %%
# Step 24: Concept search
# Thought Process:
# To build a full Income Statement, we need more than just Revenue.
# We also want Operating Income and Net Income (bottom line profit).
# Let's search all tags in the SEC file to find the official accounting names.
for namespace, concepts in data["facts"].items():
    print(f"\n--- {namespace} ---")
    for concept_name, concept_data in concepts.items():
        label = concept_data.get("label") or ""
        search_text = (str(concept_name) + " " + str(label)).lower()
        # Look for key financial keywords
        if any(k in search_text for k in ["revenue", "cost", "gross profit", "operating income", "net income"]):
            print(f"{concept_name} -> {label}")

# %% [markdown]
# ### Step 25: Extract Net Income & Operating Income DataFrames
# Extract the raw USD observations for both Net Income (`NetIncomeLoss`) and Operating Income (`OperatingIncomeLoss`).

# %%
# Step 25: Net Income and Operating Income DataFrames
# Thought Process:
# From Step 24, we identified the two standard US-GAAP concepts:
# 1. 'NetIncomeLoss' for Apple's bottom-line net profit.
# 2. 'OperatingIncomeLoss' for Apple's core operational profit.
# We extract their USD observations and put each into its own DataFrame.
net_income_data = data["facts"]["us-gaap"]["NetIncomeLoss"]
net_income_df = pd.DataFrame(net_income_data["units"]["USD"])

operating_income_data = data["facts"]["us-gaap"]["OperatingIncomeLoss"]
operating_income_df = pd.DataFrame(operating_income_data["units"]["USD"])

print("Net income rows:", len(net_income_df))
print("Operating income rows:", len(operating_income_df))

# %% [markdown]
# ### Step 26: Add Period Days to Operating Income & Net Income
# Calculate period duration in days for both datasets using `add_period_days`.

# %%
# Step 26: Add period_days to other concepts
# Thought Process:
# Just like we did with Revenue, calculate the real number of days between start and end
# to separate annual periods from quarterly periods.
operating_income_df = add_period_days(operating_income_df)
net_income_df = add_period_days(net_income_df)

# %% [markdown]
# ### Step 27: Check Period Distribution for Operating Income & Net Income
# Verify that reporting period lengths for operating income and net income also cluster around 90 days and 365 days.

# %%
# Step 27: Check period distribution
# Thought Process:
# Confirm that operating income and net income follow the exact same period patterns
# (clusters around ~90 days for quarters and ~365 days for full fiscal years).
print("Operating Income:")
print(
    operating_income_df["period_days"]
    .value_counts()
    .sort_index()
)

print("\nNet Income:")
print(
    net_income_df["period_days"]
    .value_counts()
    .sort_index()
)

# %% [markdown]
# ### Step 28: Filter Annual Periods for Operating Income & Net Income
# Filter for ~1-year periods (350 to 380 days) on both datasets using `filter_annual_periods`.

# %%
# Step 28: Keep only annual periods (~365 days)
# Thought Process:
# Filter rows between 350 and 380 days so we only keep full-year annual financial numbers.
annual_operating_income = filter_annual_periods(
    operating_income_df
)

annual_net_income = filter_annual_periods(
    net_income_df
)

# %% [markdown]
# ### Step 29: Count Annual Candidate Rows
# Check how many annual candidate rows were extracted for Operating Income and Net Income.

# %%
# Step 29: Check candidate row counts
# Thought Process:
# Check the raw candidate counts before deduplicating.
print("Annual Operating Income records:",
      len(annual_operating_income))

print("Annual Net Income records:",
      len(annual_net_income))

# %% [markdown]
# ### Step 30: Count Unique Annual Reporting Periods
# Count unique `(start, end)` periods to verify how many distinct years exist before deduplication.

# %%
# Step 30: Count unique periods
# Thought Process:
# Count how many unique financial years exist in the data.
# This tells us the expected row count once duplicates are removed.
print(
    "Unique Operating Income periods:",
    annual_operating_income[["start", "end"]]
    .drop_duplicates()
    .shape[0]
)

print(
    "Unique Net Income periods:",
    annual_net_income[["start", "end"]]
    .drop_duplicates()
    .shape[0]
)

# %% [markdown]
# ### Step 31: Assign Form Priority to Candidates
# Map form priority (10-K/A = 1, 10-K = 2, 8-K = 3) using `apply_filing_priority`.

# %%
# Step 31: Apply form priority
# Thought Process:
# Use the exact same trust ranking rules as Revenue:
# Priority 1: 10-K/A (amendments/corrections)
# Priority 2: 10-K (official audited annual report)
# Priority 3: 8-K (interim filings)
annual_operating_income = apply_filing_priority(
    annual_operating_income
)

annual_net_income = apply_filing_priority(
    annual_net_income
)

# %% [markdown]
# ### Step 32: Inspect Form Breakdown for Annual Candidates
# Check how many 10-K, 10-K/A, and 8-K filings exist in the annual candidate datasets.

# %%
# Step 32: Check forms in candidates
# Thought Process:
# Review which filing types are present in both candidate pools.
print("Operating Income:")
print(
    annual_operating_income["form"]
    .value_counts()
)

print("\nNet Income:")
print(
    annual_net_income["form"]
    .value_counts()
)

# %% [markdown]
# ### Step 33: Preview Annual Operating Income Candidates
# Inspect the first 20 records of annual Operating Income with form priorities.

# %%
# Step 33: Preview Operating Income candidates
# Thought Process:
# Visually check the first 20 rows of Operating Income before deduplication.
annual_operating_income[
    ["start", "end", "val", "form", "filed", "form_priority"]
].head(20)

# %% [markdown]
# ### Step 34: Preview Annual Net Income Candidates
# Inspect the first 20 records of annual Net Income with form priorities.

# %%
# Step 34: Preview Net Income candidates
# Thought Process:
# Visually check the first 20 rows of Net Income before deduplication.
annual_net_income[
    ["start", "end", "val", "form", "filed", "form_priority"]
].head(20)

# %% [markdown]
# ### Step 35: Deduplicate Operating Income & Net Income
# Use `select_one_record_per_period` to select exactly one authoritative record per financial period.

# %%
# Step 35: Deduplicate using priority rules
# Thought Process:
# For every annual period (start to end), keep only the single best record
# (highest filing priority, newest filing date).
annual_operating_income_clean = select_one_record_per_period(
    annual_operating_income
)

annual_net_income_clean = select_one_record_per_period(
    annual_net_income
)

# %% [markdown]
# ### Step 36: Check Cleaned Record Counts
# Verify the final cleaned row counts for Operating Income and Net Income.

# %%
# Step 36: Verify row counts
# Thought Process:
# Confirm that each dataset now has one row per year, matching our expected unique periods.
print(
    "Operating Income records:",
    len(annual_operating_income_clean)
)

print(
    "Net Income records:",
    len(annual_net_income_clean)
)

# %% [markdown]
# ### Step 37: Verify Zero Duplicate Periods
# Check that there are 0 duplicate `(start, end)` pairs remaining in both cleaned datasets.

# %%
# Step 37: Sanity check for duplicates
# Thought Process:
# Verify that the duplicate count is strictly 0. 
# If duplicates remained, downstream merges would create incorrect duplicate rows.
print(
    "Duplicate Operating Income periods:",
    annual_operating_income_clean
    .duplicated(subset=["start", "end"])
    .sum()
)

print(
    "Duplicate Net Income periods:",
    annual_net_income_clean
    .duplicated(subset=["start", "end"])
    .sum()
)

# %% [markdown]
# ### Step 38: Compare Cleaned Period Counts Across All 3 Metrics
# Check total periods available for Revenue, Operating Income, and Net Income.

# %%
# Step 38: Compare total periods
# Thought Process:
# Before combining tables, check how many years each metric spans.
# We want to know if all three metrics cover the exact same number of years.
print("Revenue periods:",
      len(annual_clean))

print("Operating Income periods:",
      len(annual_operating_income_clean))

print("Net Income periods:",
      len(annual_net_income_clean))

# %% [markdown]
# ### Step 39: Check Period Alignment (Intersection of Periods)
# Use set intersections to verify that all three metrics share the exact same annual reporting periods.

# %%
# Step 39: Check set overlap
# Thought Process:
# Even if counts match, do they represent the *exact same* fiscal years?
# Using set intersection (comparing (start, end) pairs) proves that all three metrics align perfectly.
revenue_periods = set(
    zip(annual_clean["start"], annual_clean["end"])
)

operating_income_periods = set(
    zip(
        annual_operating_income_clean["start"],
        annual_operating_income_clean["end"]
    )
)

net_income_periods = set(
    zip(
        annual_net_income_clean["start"],
        annual_net_income_clean["end"]
    )
)

print(
    "Revenue & Operating Income overlap:",
    len(revenue_periods & operating_income_periods)
)

print(
    "Revenue & Net Income overlap:",
    len(revenue_periods & net_income_periods)
)

print(
    "Operating Income & Net Income overlap:",
    len(
        operating_income_periods
        & net_income_periods
    )
)

# %% [markdown]
# ### Step 40: Prepare Final Revenue Table
# Select only `start`, `end`, and rename `val` to `revenue`.

# %%
# Step 40: Clean Revenue subset
# Thought Process:
# Strip away metadata columns (like form, frame, filed) and keep only the essentials:
# start date, end date, and the dollar amount renamed cleanly to 'revenue'.
revenue_final = annual_clean[
    ["start", "end", "val"]
].copy()

revenue_final = revenue_final.rename(
    columns={"val": "revenue"}
)

# %% [markdown]
# ### Step 41: Prepare Final Operating Income Table
# Select only `start`, `end`, and rename `val` to `operating_income`.

# %%
# Step 41: Clean Operating Income subset
# Thought Process:
# Keep start date, end date, and rename the value to 'operating_income'.
operating_income_final = annual_operating_income_clean[
    ["start", "end", "val"]
].copy()

operating_income_final = operating_income_final.rename(
    columns={"val": "operating_income"}
)

# %% [markdown]
# ### Step 42: Prepare Final Net Income Table
# Select only `start`, `end`, and rename `val` to `net_income`.

# %%
# Step 42: Clean Net Income subset
# Thought Process:
# Keep start date, end date, and rename the value to 'net_income'.
net_income_final = annual_net_income_clean[
    ["start", "end", "val"]
].copy()

net_income_final = net_income_final.rename(
    columns={"val": "net_income"}
)

# %% [markdown]
# ### Step 43: Merge Metrics into Consolidated Income Statement Table
# Perform inner joins on `start` and `end` dates to combine Revenue, Operating Income, and Net Income into `income_statement_df`.

# %%
# Step 43: Merge all 3 tables
# Thought Process:
# Now combine all 3 clean tables together:
# 1. Match Revenue with Operating Income using start and end dates.
# 2. Match the result with Net Income using start and end dates.
# 3. Sort chronologically by the fiscal year end date.
# Result: A single row for each year with Revenue, Operating Income, and Net Income side-by-side.
income_statement_df = (
    revenue_final
    .merge(
        operating_income_final,
        on=["start", "end"],
        how="inner"
    )
    .merge(
        net_income_final,
        on=["start", "end"],
        how="inner"
    )
    .sort_values("end")
    .reset_index(drop=True)
)

# %% [markdown]
# ### Step 44: View Consolidated Income Statement Table
# Display the final combined income statement dataset.

# %%
# Step 44: Preview final table
# Thought Process:
# Inspect our final consolidated Income Statement dataset.
income_statement_df

# %% [markdown]
# ### Step 45: Check Final Table Dimensions
# Verify total row count and column names of the merged table.

# %%
# Step 45: Final validation
# Thought Process:
# Final check to verify total number of years covered and confirm all expected columns are present.
print("Rows:", len(income_statement_df))
print("Columns:", income_statement_df.columns.tolist())

