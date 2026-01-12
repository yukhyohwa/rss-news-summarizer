# fetcher.py
import feedparser
from urllib.parse import urlparse
from datetime import datetime
from time import mktime

def get_source_name(feed_url):
    """Extracts a readable source name from the feed URL."""
    parsed_url = urlparse(feed_url)
    domain = parsed_url.netloc.replace("www.", "")
    try:
        return domain.split('.')[-2] if domain.count('.') > 1 else domain.split('.')[0]
    except IndexError:
        return domain

def fetch_feed(feed_url):
    """
    Fetches and parses a single RSS/Atom feed.
    Returns a list of article dictionaries.
    """
    print(f"  - Fetching: {feed_url}")
    try:
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            print(f"    ⚠️ Warning: Potential feed format issue: {feed_url}, Bozo Error: {feed.bozo_exception}")

        source_name = get_source_name(feed_url)
        articles = []
        
        for entry in feed.entries:
            published_dt = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_dt = datetime.fromtimestamp(mktime(entry.published_parsed))
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_dt = datetime.fromtimestamp(mktime(entry.updated_parsed))

            summary = entry.get('summary', entry.get('description', ''))

            articles.append({
                'title': entry.get('title', 'N/A'),
                'link': entry.get('link', 'N/A'),
                'summary': summary,
                'published': published_dt,
                'source_name': source_name,
            })
            
        print(f"    => Successfully fetched {len(articles)} articles.")
        return articles
        
    except Exception as e:
        print(f"    ❌ Fetch failed: {feed_url}, Error: {e}")
        return []

def fetch_all_feeds(feed_urls):
    """
    Fetches all RSS feeds in the list and returns a consolidated article list.
    """
    all_articles = []
    print("\n[Stage 1/5] Starting RSS feed aggregation...")
    for url in feed_urls:
        articles_from_feed = fetch_feed(url)
        if articles_from_feed:
            all_articles.extend(articles_from_feed)
    print(f"[Stage 1/5] Complete! Total articles aggregated: {len(all_articles)}")
    return all_articles
