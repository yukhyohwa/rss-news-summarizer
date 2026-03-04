
# main.py
import time
import sys
import argparse
from datetime import datetime, timezone
from tqdm import tqdm

# Import utilities
from config.settings import RSS_FEEDS
from app.core.fetcher import fetch_all_feeds
from app.core.translator import translate_articles
from app.core.processor import (
    deduplicate_and_merge_articles, 
    filter_articles, 
    apply_keyword_categorization,
    load_categories
)
from app.core.db import init_db
from app.core.news_db import save_news_articles
from app.core.unified_reporter import generate_unified_report
from app.core.mailer import send_report_email

# Import Arb Collectors
from app.collectors.lof_funds import main as run_jisilu_lof
from app.collectors.a_share_arbitrage import main as run_a_share_arbitrage
from app.collectors.bond_issuance import main as run_bond_issuance
from app.collectors.forex import main as run_forex_rates
from app.collectors.commodities import main as run_commodities
from app.collectors.spac_arbitrage import main as run_spac_arbitrage
from app.collectors.cef_arbitrage import main as run_cef_arbitrage
from app.collectors.qdii_arbitrage import main as run_qdii_arbitrage
from app.collectors.cbond_monitor import main as run_cbond_monitor
from app.collectors.market_indices import main as run_market_indices

def run_news_pipeline(days=1, start_date=None, end_date=None):
    """Fetches and processes news, returns categorized articles."""
    print("\n>>> Running News Aggregation Task...")
    raw_articles = fetch_all_feeds(RSS_FEEDS)
    if not raw_articles:
        return {}
    filtered = filter_articles(raw_articles, days=days, start_date=start_date, end_date=end_date)
    if not filtered:
        return {}
    translated = translate_articles(filtered)
    unique = deduplicate_and_merge_articles(translated)
    categorized_data = apply_keyword_categorization(unique)
    
    # Save to News Database
    save_news_articles(categorized_data)
    
    # Organize into categories
    keyword_map = load_categories()
    categorized = {cat: [] for cat in keyword_map.keys()}
    if "Others" not in categorized: categorized["Others"] = []
    
    for article in categorized_data:
        cat = article.get('category', 'Others')
        if cat in categorized:
            categorized[cat].append(article)
        else:
            categorized['Others'].append(article)
    return categorized

def run_arb_pipeline():
    """Runs all market arbitrage collectors."""
    print("\n>>> Running Market Arbitrage Tasks...")
    init_db()
    
    tasks = [
        ("LOF/IOF", run_jisilu_lof),
        ("Bond Issuance", run_bond_issuance),
        ("A-share Arbitrage", run_a_share_arbitrage),
        ("Forex Rates", run_forex_rates),
        ("Commodities", run_commodities),
        ("SPAC Arbitrage", run_spac_arbitrage),
        ("CEF Arbitrage", run_cef_arbitrage),
        ("QDII Arbitrage", run_qdii_arbitrage),
        ("Cbond Monitor", run_cbond_monitor),
        ("Market Indices", run_market_indices)
    ]
    
    for name, task in tasks:
        print(f"  -> Processing {name}...")
        try:
            task()
        except Exception as e:
            print(f"  !!! Error in {name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Market & News Intelligence System")
    parser.add_argument('--all', action='store_true', help="Run both news and arb (default)")
    parser.add_argument('--news', action='store_true', help="Run only news task")
    parser.add_argument('--arb', action='store_true', help="Run only market arb task")
    parser.add_argument('--days', type=int, default=1, help="News: Fetch from last N days")
    parser.add_argument('--mail', action='store_true', help="Send final report via email")
    
    args = parser.parse_args()
    
    if not (args.news or args.arb):
        args.all = True
        
    start_time = time.time()
    print("===========================================")
    print("=== Global News & Market Digest ===")
    print("===========================================\n")
    
    categorized_news = None
    if args.all or args.news:
        categorized_news = run_news_pipeline(days=args.days)
        
    if args.all or args.arb:
        run_arb_pipeline()
        
    print("\n>>> Generating Unified Intelligence Report...")
    report_path = generate_unified_report(categorized_news, include_arb=(args.all or args.arb))
    
    if report_path:
        print(f"[OK] Report generated: {report_path}")
        if args.mail:
            print(">>> Sending report via email...")
            try:
                send_report_email(report_path)
                print("[SUCCESS] Email sent successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to send email: {e}")
    else:
        print("[FAIL] Failed to generate report.")
        
    print(f"\nTotal Time: {time.time() - start_time:.2f} seconds")
    print("===========================================")

if __name__ == "__main__":
    main()