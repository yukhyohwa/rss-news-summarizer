import json
import os
import re
from datetime import datetime, timedelta, timezone
from config.settings import BLOCKED_KEYWORDS, SHOW_IMAGES
from tqdm import tqdm

def load_categories():
    """Loads categorization keyword map from config/categories.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, 'config', 'categories.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load category config: {e}")
    return {}

def apply_keyword_categorization(articles):
    """Categorizes articles based on defined keywords with smart matching."""
    print("\n[Stage 3.5/5] Categorizing articles based on keywords...")
    categories = load_categories()
    if not categories:
        for article in articles:
            article['category'] = 'Others'
        return articles

    for article in tqdm(articles, desc="Categorizing"):
        # Combine original and translated text for maximum matching coverage
        original_text = f"{article.get('title', '')} {article.get('summary', '')}"
        translated_text = f"{article.get('translated_title', '')} {article.get('translated_summary', '')}"
        text_to_search = f"{original_text} {translated_text}".lower()
        
        assigned_category = "Others"
        
        # Priority: Check keyword matches
        found_match = False
        for category, keywords in categories.items():
            if category == "Others": continue
            
            matched = False
            for kw in keywords:
                kw_lower = kw.lower()
                
                # Rule: For very short English alphanumeric keywords (e.g., 'AI', 'AR'), 
                # use whole-word matching. 
                # Note: We use isascii() to ensure this doesn't kill Chinese keyword matching.
                if len(kw_lower) <= 3 and kw_lower.isalnum() and kw_lower.isascii():
                    pattern = rf'\b{re.escape(kw_lower)}\b'
                    if re.search(pattern, text_to_search):
                        matched = True
                        break
                # Rule: Substring match for Chinese or longer English terms
                else:
                    if kw_lower in text_to_search:
                        matched = True
                        break
            
            if matched:
                assigned_category = category
                found_match = True
                break
        
        # Secondary Logic: Special handling for specific sources (BBC, NYT)
        if not found_match and article.get('source_name') in ['anyfeeder', 'nytimes']:
            assigned_category = "Politics & International"

        article['category'] = assigned_category
    
    return articles

def filter_articles(articles, days=None, start_date=None, end_date=None):
    """
    Filters articles within the specified time range and 
    removes articles containing blocked keywords.
    """
    if start_date and end_date:
        start_time = start_date
        end_time = end_date
    else:
        days_to_filter = days if days is not None else 1
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_to_filter)

    filtered_articles = []
    blocked_count = 0

    for article in articles:
        # 1. Blocklist Filtering (Check title and summary)
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        is_blocked = False
        for kw in BLOCKED_KEYWORDS:
            if kw.lower() in title or kw.lower() in summary:
                is_blocked = True
                break
        
        if is_blocked:
            blocked_count += 1
            continue

        # 2. Date Filtering
        published_time = article.get('published')
        if not published_time:
            filtered_articles.append(article)
            continue
        if published_time.tzinfo is None:
            published_time = published_time.replace(tzinfo=timezone.utc)
        
        if start_time <= published_time <= end_time:
            filtered_articles.append(article)
    
    if blocked_count > 0:
        print(f"    🚫 Filtered out {blocked_count} articles based on blocklist.")
    
    # Optional: Cleanup summaries for a cleaner report (and save translation tokens)
    if not SHOW_IMAGES:
        for article in filtered_articles:
            summary = article.get('summary', '')
            if summary:
                # 1. Remove Markdown image syntax: ![alt](url)
                summary = re.sub(r'!\[[^\]]*\]\([^\)]*\)', '', summary)
                # 2. Remove ALL HTML tags (including <b>, <strong>, <img>, <a> etc.)
                # This ensures the report is plain text and not bolded by source styles
                summary = re.sub(r'<[^>]+>', '', summary)
                # 3. Cleanup escaping/excess whitespace
                article['summary'] = summary.strip()
        
    return filtered_articles

def deduplicate_and_merge_articles(articles):
    """Identifies and merges similar articles based on topics."""
    print("\n[Stage 4/5] Merging similar articles...")
    unique_articles = []
    for article in tqdm(articles, desc="Merging"):
        source_info = {'name': article['source_name'], 'link': article['link']}
        current_topic = article.get('topic_key')
        
        is_duplicate = False
        if current_topic:
            for unique_article in unique_articles:
                if current_topic == unique_article.get('topic_key'):
                    if 'sources' not in unique_article:
                        unique_article['sources'] = [{'name': unique_article['source_name'], 'link': unique_article['link']}]
                    if not any(s['link'] == source_info['link'] for s in unique_article['sources']):
                        unique_article['sources'].append(source_info)
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            new_article = article.copy()
            new_article['sources'] = [source_info]
            unique_articles.append(new_article)
    return unique_articles