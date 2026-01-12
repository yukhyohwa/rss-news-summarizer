from deep_translator import GoogleTranslator
from tqdm import tqdm
import time
import re

def translate_articles(articles):
    """
    Translates article titles and summaries into Chinese using free Google Translate API.
    """
    print(f"\n[Stage 3/5] Starting translation using free API...")
    processed_articles = []
    
    # Initialize translator (Target language remains zh-CN as per previous requirement)
    translator = GoogleTranslator(source='auto', target='zh-CN')

    for article in tqdm(articles, desc="Translating"):
        new_article = article.copy()
        
        try:
            # Translate title if it contains non-Chinese characters
            title = article.get('title', '')
            if title and (any(ord(c) > 127 for c in title) or re.search('[a-zA-Z]', title)):
                new_article['translated_title'] = translator.translate(title)
            else:
                new_article['translated_title'] = title
            
            # Translate summary (capped for API stability)
            summary = article.get('summary', '')[:2000]
            if summary:
                new_article['translated_summary'] = translator.translate(summary)
            else:
                new_article['translated_summary'] = ""
            
            # Simple keyword-based topic key for merging
            clean_title = re.sub(r'[^\w\s]', '', new_article['translated_title'])
            new_article['topic_key'] = clean_title[:10].strip()
            
            processed_articles.append(new_article)
            # Short sleep to prevent IP rate-limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"\n❗ Translation error: {e}")
            new_article['translated_title'] = article.get('title', 'N/A')
            new_article['translated_summary'] = article.get('summary', '')
            new_article['topic_key'] = None
            processed_articles.append(new_article)
            time.sleep(1)

    return processed_articles
