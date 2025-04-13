import sqlite3
import pandas as pd
import requests # or httpx
import os
import logging

logging.basicConfig(level=logging.INFO)

DATA_DIR = "../data" # Relative to script location
DB_PATH = os.path.join(DATA_DIR, "eve_data.sqlite")
DOWNLOAD_DIR = os.path.join(DATA_DIR, "everef_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- URLs for EveRef Data ---
# Replace with actual, current URLs from docs.everef.net
MARKET_ORDERS_URL = "https://data.everef.net/market-orders/market-orders-latest.parquet.bz2" # Example
INV_TYPES_URL = "https://data.everef.net/sde/invTypes.csv.bz2" # Example

def download_file(url, target_path):
    logging.info(f"Downloading {url} to {target_path}...")
    # Add error handling, potentially use streaming download for large files
    response = requests.get(url, stream=True)
    response.raise_for_status() # Raise exception for bad status codes
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logging.info("Download complete.")

def load_parquet_to_sqlite(parquet_path, table_name, conn):
    logging.info(f"Loading {parquet_path} into table '{table_name}'...")
    df = pd.read_parquet(parquet_path)
    # Optional: Clean column names if needed (e.g., remove spaces, special chars)
    df.columns = df.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    logging.info(f"Table '{table_name}' created/replaced.")

def load_csv_to_sqlite(csv_path, table_name, conn, compression='bz2'):
    logging.info(f"Loading {csv_path} into table '{table_name}'...")
    # Adjust chunksize based on available memory
    chunk_iter = pd.read_csv(csv_path, compression=compression, chunksize=50000)
    first_chunk = True
    for chunk in chunk_iter:
         # Optional: Clean column names
        chunk.columns = chunk.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)
        write_mode = 'replace' if first_chunk else 'append'
        chunk.to_sql(table_name, conn, if_exists=write_mode, index=False)
        first_chunk = False
    logging.info(f"Table '{table_name}' created/replaced.")


def create_indexes(conn):
    cursor = conn.cursor()
    logging.info("Creating indexes...")
    # Example Indexes (adjust table/column names based on actual data)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_orders_type_region ON market_orders (type_id, region_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_orders_type_system ON market_orders (type_id, system_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invTypes_typeID ON invTypes (typeID);")
    # Add more indexes as needed
    conn.commit()
    logging.info("Indexes created.")

if __name__ == "__main__":
    # 1. Download Files
    market_orders_file = os.path.join(DOWNLOAD_DIR, "market-orders-latest.parquet.bz2")
    inv_types_file = os.path.join(DOWNLOAD_DIR, "invTypes.csv.bz2")
    # download_file(MARKET_ORDERS_URL, market_orders_file) # Uncomment to run download
    # download_file(INV_TYPES_URL, inv_types_file) # Uncomment to run download

    # 2. Connect to DB
    conn = sqlite3.connect(DB_PATH)

    # 3. Load Data into Tables
    try:
        # Note: Adjust paths if files are not compressed or are parquet
        load_csv_to_sqlite(inv_types_file, "invTypes", conn, compression='bz2')
        # For parquet:
        # import pyarrow # or fastparquet - ensure installed
        # market_orders_parquet = os.path.join(DOWNLOAD_DIR, "market-orders-latest.parquet") # Assuming decompressed
        # load_parquet_to_sqlite(market_orders_parquet, "market_orders", conn)

        # 4. Create Indexes
        create_indexes(conn)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        conn.close()
        logging.info("Database connection closed.")