import time
import random
import os
from dotenv import load_dotenv
from app.core.db import save_data
from app.core.jsl_session import get_jsl_session
from config.settings import STRATEGY_CONFIG

load_dotenv()
config = STRATEGY_CONFIG['lof']

# Configuration
URLS = {
    "Stock LOF": "https://www.jisilu.cn/data/lof/stock_lof_list/",
    "Index LOF": "https://www.jisilu.cn/data/lof/index_lof_list/"
}

# Thresholds
PREMIUM_THRESHOLD = config.get('min_premium_rate', 3.5)
MIN_SHARE = config.get('min_fund_share', 5000000) / 10000.0  # 转为'万份'
MIN_TURNOVER = config.get('min_turnover', 500000) / 10000.0    # 转为'万元'
ONLY_OPEN = config.get('only_open_apply', True)

def fetch_data(url, fund_type):
    print(f"\n[+] 正在抓取 {fund_type} (URL: {url})...")
    session = get_jsl_session()
    
    try:
        params = {
            'rp': 500,  # 登录状态下 rp=500 是有效的，可一次拿全量
            'page': 1,
            '___jsl': f'LST___t={int(time.time() * 1000)}'
        }
        
        response = session.post(url, data=params)
        if response.status_code != 200:
            print(f"[!] 请求失败: {response.status_code}")
            return []
            
        data = response.json()
        rows = data.get('rows', [])
        print(f"[*] 接口返回原始数据：{len(rows)} 条")
        
        results = []
        for row in rows:
            cell = row.get('cell', {})
            fund_id = cell.get('fund_id')
            
            # 提取价格和净值 (兼容不同的字段名)
            price_val = cell.get('price')
            nav_val = cell.get('fund_nav') or cell.get('nav')
            
            if price_val in (None, '-', '登录查看') or nav_val in (None, '-', '登录查看'):
                continue
                
            price = float(price_val)
            nav = float(nav_val)
            
            # 1. 优先提取盘中实时估值 (IOPV)
            est_val_str = cell.get('estimate_value')
            try:
                est_real = float(str(est_val_str).replace(',', '')) if est_val_str not in (None, '-', '登录查看', '') else 0.0
            except:
                est_real = 0.0
                
            # 2. 若无实时估值，使用 T-1 或 T-2 净值配合指数涨幅估算
            ref_inc_rt_str = str(cell.get('ref_increase_rt', '0')).replace('%', '')
            try:
                ref_inc_rt = float(ref_inc_rt_str)
            except:
                ref_inc_rt = 0.0
                
            nav_with_idx = nav * (1 + ref_inc_rt / 100.0) if ref_inc_rt != 0 else nav
            
            # 3. 优先使用实时估值，没有再用参考估值
            est_nav = est_real if est_real > 0 else nav_with_idx
            
            if est_nav <= 0: continue
            premium = ((price - est_nav) / est_nav) * 100
            
            # 申购状态筛选
            apply_status = cell.get('apply_status', '-')
            is_open = '开放' in apply_status or apply_status in ('-', '')
            
            # 规模与流动性
            amount = float(str(cell.get('amount', 0)).replace(',', '')) # 万份
            volume = float(str(cell.get('volume', 0)).replace(',', '')) # 万元
            
            if abs(premium) > PREMIUM_THRESHOLD and (amount >= MIN_SHARE or volume >= MIN_TURNOVER):
                if ONLY_OPEN and not is_open:
                    continue
                
                results.append({
                    'fund_id': fund_id,
                    'fund_name': cell.get('fund_nm'),
                    'price': price,
                    'nav': round(est_nav, 4),
                    'premium_rate': round(premium, 2),
                    'is_estimated_nav': ref_inc_rt != 0,
                    'amount': amount,
                    'volume': volume,
                    'fund_type': fund_type,
                    'apply_status': apply_status
                })
                
        print(f"[OK] 符合条件的 {fund_type}：{len(results)} 只")
        return results
        
    except Exception as e:
        print(f"[!] 抓取异常: {e}")
        return []

def main():
    all_results = []
    for fund_type, url in URLS.items():
        all_results.extend(fetch_data(url, fund_type))
    
    if all_results:
        save_data('lof_funds', all_results)
    print("\n[DONE] LOF 抓取任务完成。")

if __name__ == "__main__":
    main()
