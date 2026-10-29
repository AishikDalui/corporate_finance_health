from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

# Project root: corporate-financial-health/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

load_dotenv(PROJECT_ROOT / ".env")

# Read database configuration
db_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "corporate_financial_health"),
)

engine = create_engine(db_url, pool_pre_ping=True)

# CSV filename -> MySQL table name
files_to_load = {
    "apple_income_statement.csv": "income_statement",
    "apple_balance_sheet.csv": "balance_sheet",
    "apple_cash_flow.csv": "cash_flow",
}


def load_csv_to_mysql(filename, table_name):
    file_path = CLEANED_DIR / filename

    if not file_path.exists():
        # Check for browser download variants like apple_income_statement(4).csv
        base_stem = Path(filename).stem
        candidates = list(CLEANED_DIR.glob(f"{base_stem}*.csv"))
        if candidates:
            file_path = candidates[0]
        else:
            raise FileNotFoundError(
                f"CSV not found: {file_path}\n"
                "Check the filename and data/cleaned folder."
            )

    # Load CSV. Empty fields remain missing values (NULL in SQL).
    df = pd.read_csv(file_path)
    df = df.where(pd.notna(df), None)

    # Create the table if needed and load the rows.
    # Replaces the table if it already exists.
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=500,
        method="multi",
    )

    print(f"Loaded {filename}")
    print(f"  Table: {table_name}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")


def main():
    # Test the connection before loading data.
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT DATABASE()")
        ).scalar_one()

        print(f"Connected to MySQL database: {database_name}")

    for filename, table_name in files_to_load.items():
        load_csv_to_mysql(filename, table_name)

    print("\nAll CSV files loaded successfully.")


if __name__ == "__main__":
    try:
        main()
    finally:
        engine.dispose()