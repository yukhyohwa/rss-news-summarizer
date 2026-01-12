# renderer.py
import datetime
import os

def write_markdown_file(categorized_articles, output_filename=""):
    """
    Renders categorized articles into a Markdown file.
    """
    print("\n[Stage 5/5] Generating Markdown report...")
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate default filename based on date
    if not output_filename:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        output_filename = f"News_Summary_{date_str}.md"
    
    full_path = os.path.join(output_dir, output_filename)

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# News Summary ({datetime.datetime.now().strftime('%Y-%m-%d')})\n\n")
            
            # Category sorting (Others always last)
            all_categories = list(categorized_articles.keys())
            categories_order = [c for c in all_categories if c != "Others"]
            if "Others" in all_categories:
                categories_order.append("Others")
            
            for category in categories_order:
                articles = categorized_articles.get(category, [])
                if not articles:
                    continue
                
                # Category Header
                f.write(f"## 📰 {category} ({len(articles)} items)\n\n")
                
                for article in articles:
                    # Format sources as (Source: Link1, Link2)
                    source_line = ", ".join([f"[{s['name']}]({s['link']})" for s in article['sources']])
                    
                    # Article Title with Source Links
                    f.write(f"### {article['translated_title']} (Source: {source_line})\n\n")
                    
                    # Translated Summary
                    if article['translated_summary']:
                        f.write(f"{article['translated_summary']}\n\n")
                    
                    f.write("---\n\n")
        
        print(f"[Stage 5/5] Success! Report saved to: {full_path}")
        return full_path
    
    except Exception as e:
        print(f"❌ Error writing Markdown file: {e}")
        return None
