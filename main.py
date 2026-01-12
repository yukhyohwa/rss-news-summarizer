# main.py
import time
import sys
import argparse
from datetime import datetime, timezone
from tqdm import tqdm

# Catch import errors with clear guidance
try:
    from app.core.fetcher import fetch_all_feeds
    from app.core.translator import translate_articles
except ImportError as e:
    if "feedparser" in str(e) or "deep_translator" in str(e):
        print(f"❌ Error: Missing core dependencies: {e}")
        print("   Please run the following command in your terminal to install requirements:")
        print("\n   pip install -r requirements.txt\n")
        sys.exit(1)
    else:
        raise e

# Import functions from project modules
from config.settings import RSS_FEEDS
from app.core.processor import (
    deduplicate_and_merge_articles, 
    filter_articles, 
    apply_keyword_categorization,
    load_categories
)
from app.core.renderer import write_markdown_file

def run_pipeline(days=None, start_date=None, end_date=None):
    """
    Executes the full pipeline: Fetching, Translation, Keyword Categorization, and Report Generation.
    """
    start_time = time.time()
    
    # Check configuration
    if not RSS_FEEDS:
        print("❌ Error: RSS_FEEDS list in 'config/settings.py' is empty.")
        return

    # Pipeline Start
    print("===================================")
    print("=== RSS News Aggregator (Free Version) ===")
    print("===================================\n")

    # Step 1: Fetch articles from RSS feeds
    raw_articles = fetch_all_feeds(RSS_FEEDS)
    if not raw_articles:
        print("\nNo articles fetched. Terminating script.")
        return

    # Step 2: Filter articles by date
    filtered_articles = filter_articles(raw_articles, days=days, start_date=start_date, end_date=end_date)
    if not filtered_articles:
        print("\nNo articles remain after filtering. Terminating script.")
        return
        
    # Step 3: Translate articles using free API
    translated_articles = translate_articles(filtered_articles)
    if not translated_articles:
        print("\nTranslation failed. Terminating script.")
        return

    # Step 4: De-duplicate and merge articles
    unique_articles = deduplicate_and_merge_articles(translated_articles)
    
    # Step 4.5: Categorize articles based on keywords
    unique_articles = apply_keyword_categorization(unique_articles)

    # Step 5: Organize categories and generate Markdown
    print("\n[Stage 5/5] Organizing categories and generating report...")
    
    # Load category map
    keyword_map = load_categories()
    categorized = {cat: [] for cat in keyword_map.keys()}
    if "Others" not in categorized:
        categorized["Others"] = []

    for article in tqdm(unique_articles, desc="Organizing"):
        cat = article.get('category', 'Others')
        if cat in categorized:
            categorized[cat].append(article)
        else:
            categorized['Others'].append(article)
            
    # Generate Markdown file
    output_file = write_markdown_file(categorized)
    
    print("[Stage 5/5] Categorization and report generation complete!")
    for category, items in categorized.items():
        print(f"  - {category}: {len(items)} items")
    
    # Pipeline End
    end_time = time.time()
    print("\n==============================")
    if output_file:
        print(f"🎉 Pipeline completed successfully!")
        print(f"   Report: {output_file}")
    else:
        print(f"❗ Pipeline finished, but report was not generated.")
        
    print(f"   Total Time: {end_time - start_time:.2f} seconds")
    print("==============================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RSS News Aggregator (Free Translation Version)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=1,
        help="Fetch articles from the last N days. Default is 1."
    )
    
    date_format = "%Y%m%d"
    parser.add_argument(
        '--range',
        type=str,
        help=f"Specify a date range. Format: 'YYYYMMDD-YYYYMMDD'."
    )

    args = parser.parse_args()

    start_date_obj = None
    end_date_obj = None
    days_arg = args.days

    if args.range:
        try:
            start_str, end_str = args.range.split('-')
            start_date_obj = datetime.strptime(start_str, date_format).replace(tzinfo=timezone.utc)
            end_date_obj = datetime.strptime(end_str, date_format).replace(tzinfo=timezone.utc)
            days_arg = None
            print(f"Mode: Date Range ({start_str} to {end_str})")
        except ValueError:
            print(f"❌ Error: Invalid date range format. Use 'YYYYMMDD-YYYYMMDD'.")
            sys.exit(1)
    else:
        print(f"Mode: Time Window (Past {days_arg} days)")

    run_pipeline(days=days_arg, start_date=start_date_obj, end_date=end_date_obj)