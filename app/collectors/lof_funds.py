import time
import random
import os
from dotenv import load_dotenv
from app.core.db import save_data
from app.core.jsl_session import get_jsl_session
from config.settings import STRATEGY_CONFIG

# Load environment variables
load_dotenv()

config = STRATEGY_CONFIG['lof']

# Configuration
STOCK_LOF_URL = "https://www.jisilu.cn/data/lof/stock_lof_list/"
INDEX_LOF_URL = "https://www.jisilu.cn/data/lof/index_lof_list/"

# Thresholds from settings
PREMIUM_THRESHOLD = config['min_premium_rate']
MIN_AMOUNT_THRESHOLD = config['min_fund_share'] / 10000.0  # Convert to 'Wan'
MIN_VOLUME_THRESHOLD = config['min_turnover'] / 10000.0    # Convert to 'Wan'

def fetch_data(url, fund_type):
    """Fetch data from the given URL and return filtered list."""
    print(f"Fetching {fund_type} data from {url}...")
    
    # Simulate user browsing behavior with random sleep
    sleep_time = random.uniform(3, 8)
    print(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)
    
    # Get session (ensures active login)
    session = get_jsl_session()
    
    try:
        # Add timestamp to params to prevent caching
        params = {
            'rp': 500,
            'page': 1,
            '___jsl': f'LST___t={int(time.time() * 1000)}'
        }
        
        # Use simple POST instead of session.post with custom headers if session already handles it
        response = session.post(url, data=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return []
            
        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to decode JSON. Response text preview: {response.text[:200]}")
            return []
            
        rows = data.get('rows', [])
        
        results = []
        for row in rows:
            cell = row.get('cell', {})
            try:
                # Extract Price and NAV for manual calculation (robust to guest/missing fields)
                price_val = cell.get('price')
                fund_nav = cell.get('fund_nav') # Some endpoints use fund_nav
                
                # Check for valid price and NAV (especially for guest users or hidden rows)
                if price_val in (None, '-', '登录查看') or fund_nav in (None, '-', '登录查看'):
                    continue
                
                price = float(price_val)
                nav = float(fund_nav)
                
                # Formula: (Price - NAV) / NAV * 100
                premium_rate = ((price - nav) / nav) * 100
                
                # Liquidity/Size Filter
                amount = float(str(cell.get('amount', 0)).replace(',', ''))
                volume = float(str(cell.get('volume', 0)).replace(',', ''))
                
                is_liquid = (amount > MIN_AMOUNT_THRESHOLD) or (volume > MIN_VOLUME_THRESHOLD)
                
                if premium_rate > PREMIUM_THRESHOLD and is_liquid:
                    fund_info = {
                        'fund_id': cell.get('fund_id'),
                        'fund_name': cell.get('fund_nm'),
                        'price': price,
                        'nav': nav,
                        'premium_rate': premium_rate,
                        'amount': amount,
                        'volume': volume,
                        'fund_type': fund_type,
                        'apply_status': cell.get('apply_status', '-')
                    }
                    results.append(fund_info)
            except (ValueError, TypeError):
                continue
                
        print(f"Found {len(results)} {fund_type} funds with premium > {PREMIUM_THRESHOLD}%")
        return results
        
    except Exception as e:
        print(f"Error occurred while fetching {fund_type}: {e}")
        return []

def main():
    print("Starting Jisilu LOF/IOF Scraper...")
    
    # 1. Fetch Stock LOF
    stock_records = fetch_data(STOCK_LOF_URL, "Stock LOF")
    
    # 2. Fetch Index LOF
    index_records = fetch_data(INDEX_LOF_URL, "Index LOF")

    all_records = stock_records + index_records
    
    # Save to centralized DB
    save_data('lof_funds', all_records)
    
    print("\nLOF Task Complete.")

if __name__ == "__main__":
    main()
