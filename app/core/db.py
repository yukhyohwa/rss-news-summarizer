
import sqlite3
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
DB_DIR = DATA_DIR  # Move DB to data directory
DB_NAME = 'finance_data.db'
DB_PATH = os.path.join(DB_DIR, DB_NAME)

def get_db_connection():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # LOF Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lof_funds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_id TEXT,
            fund_name TEXT,
            price REAL,
            nav REAL,
            premium_rate REAL,
            amount REAL,
            volume REAL,
            fund_type TEXT,
            apply_status TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')
    
    # Simple migration for existing lof_funds table missing 'nav' column
    try:
        cursor.execute("SELECT nav FROM lof_funds LIMIT 1")
    except sqlite3.OperationalError:
        print("[DB] Adding 'nav' column to lof_funds table...")
        cursor.execute("ALTER TABLE lof_funds ADD COLUMN nav REAL")
    
    # Bond Issuance Table (New Bonds)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bond_issuance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bond_code TEXT,
            bond_name TEXT,
            subscription_date TEXT,
            listing_date TEXT,
            details TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')
    
    # A-share Arbitrage Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_arbitrage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT,
            stock_name TEXT,
            price REAL,
            choose_price REAL,
            type_cd TEXT,
            descr TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')
    
    # Forex Rates Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forex_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT,
            bank TEXT,
            spot_buy REAL,
            cash_buy REAL,
            spot_sell REAL,
            cash_sell REAL,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Market Indices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_indices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            name TEXT,
            price REAL,
            change REAL,
            change_pct REAL,
            prev_close REAL,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Commodities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commodities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            name TEXT,
            price REAL,
            change REAL,
            change_pct REAL,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # SPAC Arbitrage Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spac_arbitrage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            name TEXT,
            ipo_date TEXT,
            price REAL,
            nav REAL,
            yield REAL,
            remaining_days INTEGER,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # CEF Arbitrage Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cef_arbitrage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            name TEXT,
            category TEXT,
            sponsor TEXT,
            price REAL,
            nav REAL,
            discount REAL,
            discount_52wk_avg REAL,
            z_score REAL,
            avg_daily_volume REAL,
            dist_status TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')
    
    # QDII Arbitrage Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qdii_arbitrage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_id TEXT,
            fund_name TEXT,
            price REAL,
            premium_rate REAL,
            estimate_value REAL,
            realtime_premium_rate REAL,
            realtime_estimate_value REAL,
            volume REAL,
            amount REAL,
            index_name TEXT,
            apply_status TEXT,
            market_type TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Cbond Double Low Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cbond_double_low (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bond_id TEXT,
            bond_name TEXT,
            price REAL,
            premium_rate REAL,
            dblow REAL,
            year_left REAL,
            type TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Cbond Put-back Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cbond_putback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bond_id TEXT,
            bond_name TEXT,
            price REAL,
            premium_rate REAL,
            dblow REAL,
            put_dt TEXT,
            year_left REAL,
            type TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    
    conn.commit()
    conn.close()

def clear_todays_data(table_name):
    """
    Removes data for the current date to ensure idempotency (latest data only).
    """
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE date = ?", (today,))
    conn.commit()
    deleted_count = cursor.rowcount
    conn.close()
    if deleted_count > 0:
        print(f"Cleared {deleted_count} old records from {table_name} for today ({today}).")
    return today

def save_data(table_name, records):
    """
    Saves a list of dictionaries to the specified table.
    Assumes records have keys matching column names (except id, date, timestamp).
    """
    if not records:
        print(f"No records to save for {table_name}.")
        return

    init_db()
    today = clear_todays_data(table_name)
    timestamp = datetime.now().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not records: return
    
    processed_records = []
    for r in records:
        r_copy = r.copy()
        r_copy['date'] = today
        r_copy['timestamp'] = timestamp
        processed_records.append(r_copy)
    
    columns = list(processed_records[0].keys())
    placeholders = ', '.join(['?' for _ in columns])
    col_names = ', '.join(columns)
    
    values = [tuple(r[c] for c in columns) for r in processed_records]
    
    query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
    
    try:
        cursor.executemany(query, values)
        conn.commit()
        print(f"Saved {len(records)} records to {table_name}.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
