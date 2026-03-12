import time
import random
import os
from dotenv import load_dotenv
from app.core.db import save_data
from app.core.jsl_session import get_jsl_session
from config.settings import STRATEGY_CONFIG

# Load environment variables
load_dotenv()

config = STRATEGY_CONFIG.get('qdii', {
    'min_premium_rate': 2.0,
    'min_fund_share': 100000,
    'min_turnover': 10000
})

# Configuration
URLS = {
    'APAC': 'https://www.jisilu.cn/data/qdii/qdii_list/A',
    'Europe/America': 'https://www.jisilu.cn/data/qdii/qdii_list/E',
    'Commodities': 'https://www.jisilu.cn/data/qdii/qdii_list/C'
}

# Thresholds from settings
PREMIUM_THRESHOLD = config.get('min_premium_rate', 2.0)
MIN_AMOUNT_THRESHOLD = config.get('min_fund_share', 100000) / 10000.0  # Convert to 'Wan'
MIN_VOLUME_THRESHOLD = config.get('min_turnover', 10000) / 10000.0    # Convert to 'Wan'

def fetch_qdii_data(market_name, url):
    """Fetch QDII data from the given URL and return filtered list."""
    print(f"Fetching {market_name} QDII data from {url}...")
    
    # Simulate user browsing behavior
    sleep_time = random.uniform(2, 5)
    print(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)
    
    session = get_jsl_session()
    
    try:
        params = {
            'rp': 500,
            'only_lof': 'y',
            'only_etf': 'n',
            '___jsl': f'LST___t={int(time.time() * 1000)}'
        }
        
        response = session.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return []
            
        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to decode JSON: {e}")
            return []
            
        rows = data.get('rows', [])
        results = []
        
        for row in rows:
            cell = row.get('cell', {})
            try:
                fund_id = cell.get('fund_id')
                fund_name = cell.get('fund_nm')
                
                if 'ETF' in fund_name.upper():
                    continue

                # Price and NAV/Estimate for calculation
                price_val = cell.get('price')
                # T-1 NAV (fund_nav) and Realtime Estimate (estimate_value2)
                nav_val = cell.get('fund_nav') 
                est2_val = cell.get('estimate_value2')
                
                # Manual Premium Calculation (Guest-proof and account-robust)
                premium_rate = 0.0
                if price_val not in (None, '-', 'buy', '登录查看') and nav_val not in (None, '-', 'buy', '登录查看'):
                    premium_rate = (float(price_val) - float(nav_val)) / float(nav_val) * 100
                
                realtime_premium_rate = 0.0
                if price_val not in (None, '-', 'buy', '登录查看') and est2_val not in (None, '-', 'buy', '登录查看'):
                    realtime_premium_rate = (float(price_val) - float(est2_val)) / float(est2_val) * 100
                
                # Liquidity/Size Filter
                amount = float(str(cell.get('total_share', cell.get('amount', 0))).replace(',', '') or 0)
                volume = float(str(cell.get('volume', 0)).replace(',', '') or 0)
                
                is_liquid = (amount > MIN_AMOUNT_THRESHOLD) or (volume > MIN_VOLUME_THRESHOLD)
                
                # Use max of T-1 and Realtime premium for filtering
                max_premium = max(premium_rate, realtime_premium_rate)
                
                apply_status = cell.get('apply_status', '')
                
                # Filter: Premium > Threshold AND Liquid AND Not Suspended
                if max_premium > PREMIUM_THRESHOLD and is_liquid and apply_status != '暂停申购':
                    fund_info = {
                        'fund_id': fund_id,
                        'fund_name': fund_name,
                        'price': float(price_val) if price_val not in (None, '-', 'buy') else 0,
                        'premium_rate': premium_rate,
                        'realtime_premium_rate': realtime_premium_rate,
                        'volume': volume,
                        'amount': amount,
                        'index_name': cell.get('index_nm'),
                        'apply_status': cell.get('apply_status'),
                        'market_type': market_name
                    }
                    results.append(fund_info)
            except (ValueError, TypeError):
                continue
                
        print(f"Found {len(results)} QDII funds in {market_name} with premium > {PREMIUM_THRESHOLD}%")
        return results
        
    except Exception as e:
        print(f"Error occurred while fetching {market_name}: {e}")
        return []

def main():
    print("Starting Jisilu QDII Arbitrage Scraper...")
    
    all_records = []
    for market, url in URLS.items():
        records = fetch_qdii_data(market, url)
        all_records.extend(records)
    
    if all_records:
        save_data('qdii_arbitrage', all_records)
        print(f"Total {len(all_records)} QDII records saved.")
    else:
        print("No QDII arbitrage opportunities found.")
    
    print("\nQDII Task Complete.")

if __name__ == "__main__":
    main()
