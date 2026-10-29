"""
SEC Financial Data Cleaning Functions

Thought Process / Purpose:
Raw data downloaded from the SEC EDGAR database is notoriously messy. 
A company reports financial numbers multiple times (for example, in quarterly reports, 
annual reports, and revised reports years later). Also, filing tags can be misleading.

These functions provide a reliable cleaning pipeline:
1. Measure true period length in days instead of trusting labels.
2. Filter for actual 1-year financial periods (~365 days).
3. Set a priority hierarchy (e.g. revised reports beat original reports).
4. Remove duplicates so we keep exactly one accurate number per period.
"""

import pandas as pd


def add_period_days(df):
    """
    Calculate the exact number of days in each reporting period.
    
    Why we do this:
    SEC labels like 'FY' (Fiscal Year) can be inaccurate—sometimes a 3-month period 
    is accidentally labeled 'FY'. By subtracting the start date from the end date, 
    we measure the real elapsed days ourselves.
    """
    # Create a copy so we don't accidentally modify the original data outside this function
    df = df.copy()

    # Step 1: Convert date text (e.g., '2023-09-30') into real datetime objects so we can do math
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])

    # Step 2: Calculate the difference between end and start in total days
    df["period_days"] = (
        df["end"] - df["start"]
    ).dt.days

    return df


def filter_annual_periods(df, min_days=350, max_days=380):
    """
    Keep only records that represent roughly one full financial year.
    
    Why we do this:
    A calendar year is 365 days, but companies often use 52-week or 53-week fiscal 
    years (ranging roughly from 350 to 375 days). Any record around ~90 days is quarterly, 
    so filtering between 350 and 380 days cleanly separates full years from quarters.
    """
    # Ensure period_days is present
    if "period_days" not in df.columns:
        df = add_period_days(df)

    # Filter rows where period_days falls between min_days (350) and max_days (380)
    return df[
        df["period_days"].between(min_days, max_days)
    ].copy()


def apply_filing_priority(df):
    """
    Assign a trust score (priority rank) to each SEC filing type.
    
    Why we do this:
    The SEC has different forms:
      - '10-K/A': An amended annual report. If a company filed this, it means they 
                  corrected a previous mistake. This is our most trusted source (Rank 1).
      - '10-K':   The standard annual report audited by professionals (Rank 2).
      - '8-K':    A major event or interim notice, less definitive for yearly totals (Rank 3).
    
    Lower number = higher priority (1 is the best).
    """
    df = df.copy()

    # Map form names to their priority rank
    df["form_priority"] = (
        df["form"]
        .map({
            "10-K/A": 1,  # Best: Official amended/corrected annual report
            "10-K": 2,    # Second best: Standard annual report
            "8-K": 3      # Third: Interim / special announcement
        })
    )

    return df


def select_one_record_per_period(df):
    """
    Select the single most authoritative observation for each financial period (start to end).
    
    Why we do this:
    Income statement items (like Revenue and Net Income) happen over a duration of time.
    If Apple reported FY2020 revenue in 2020, and then restated it in their 2021 report,
    we have duplicate records for the same period.
    
    The decision rule:
    1. Group by the reporting period (same start and end dates).
    2. Prefer higher filing priority (10-K/A first, then 10-K).
    3. If there is a tie, pick the latest filing date (filed last has the newest numbers).
    """
    df = df.copy()

    # Ensure filing priority is assigned
    if "form_priority" not in df.columns:
        df = apply_filing_priority(df)

    # Ensure filing date is a datetime object so we can sort chronologically
    df["filed"] = pd.to_datetime(df["filed"])

    # Sort so that our most preferred record appears at the very top:
    # 1. Group matching periods together ('start', 'end')
    # 2. Put best form priority first (1 before 2 before 3)
    # 3. Put newest filing date first (most recently filed wins)
    df = df.sort_values(
        ["start", "end", "form_priority", "filed"],
        ascending=[True, True, True, False]
    )

    # Keep only the first record for each unique (start, end) period
    df = df.drop_duplicates(
        subset=["start", "end"],
        keep="first"
    )

    return df


def select_one_record_per_date(df):
    """
    Select one Balance Sheet observation per reporting snapshot date.
    
    Why we do this:
    Unlike Revenue (which is earned over a full year), Balance Sheet items 
    (like Cash, Assets, Debt) represent a snapshot in time on a single day ('end' date).
    
    The decision rule:
    1. Group by the snapshot date ('end').
    2. Prefer higher filing priority (10-K/A over 10-K).
    3. If tied, pick the latest filing date ('filed' descending).
    """
    df = df.copy()

    # Ensure filing priority is assigned
    if "form_priority" not in df.columns:
        df = apply_filing_priority(df)

    # Ensure filing date is in datetime format for proper sorting
    df["filed"] = pd.to_datetime(df["filed"])

    # Sort to bring the highest-priority, newest filing to the top for each date
    df = df.sort_values(
        ["end", "form_priority", "filed"],
        ascending=[True, True, False]
    )

    # Keep the first (most trusted) entry for each unique date
    df = df.drop_duplicates(
        subset=["end"],
        keep="first"
    )

    return df