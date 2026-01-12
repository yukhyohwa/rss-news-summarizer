import json
import os
from datetime import datetime, timedelta, timezone
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
    """Categorizes articles based on defined keywords."""
    print("\n[Stage 3.5/5] Categorizing articles based on keywords...")
    categories = load_categories()
    if not categories:
        for article in articles:
            article['category'] = 'Others'
        return articles

    for article in tqdm(articles, desc="Categorizing"):
        # Match title and summary
        text_to_search = f"{article.get('translated_title', article.get('title', ''))} {article.get('translated_summary', article.get('summary', ''))}"
        text_to_search = text_to_search.lower()
        
        assigned_category = "Others"
        for category, keywords in categories.items():
            if category == "Others": continue
            if any(kw.lower() in text_to_search for kw in keywords):
                assigned_category = category
                break
        
        article['category'] = assigned_category
    
    return articles

def filter_articles(articles, days=None, start_date=None, end_date=None):
    """Filters articles within the specified time range."""
    if start_date and end_date:
        start_time = start_date
        end_time = end_date
    else:
        days_to_filter = days if days is not None else 1
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_to_filter)

    filtered_articles = []
    for article in articles:
        published_time = article.get('published')
        if not published_time:
            filtered_articles.append(article)
            continue
        if published_time.tzinfo is None:
            published_time = published_time.replace(tzinfo=timezone.utc)
        
        if start_time <= published_time <= end_time:
            filtered_articles.append(article)
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