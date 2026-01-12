# RSS News Summarizer (Keyword & Free Translation) 🚀

![Python](https://img.shields.io/badge/Python-3.x-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Translation](https://img.shields.io/badge/Translation-Free_API-orange)

A lightweight RSS news aggregator and summarizer. It automatically fetches articles from multiple RSS feeds, translates them using free APIs, categorizes them based on a custom keyword dictionary, and generates elegant Markdown reports.

## 🌟 Features

- **Multi-source Aggregation**: Supports fetching from multiple RSS/Atom feeds simultaneously.
- **Free Translation**: Integrated with `deep-translator` to support automatic translation from English, French, Japanese, etc., into Chinese.
- **Precise Categorization**: Classified based on a keyword dimension table in `config/categories.json`. Supports bilingual (Chinese/English) keywords for reliable and controlled results.
- **Content Merging**: Automatically merges news items with similar topics to reduce information redundancy.
- **Localized Storage**: Reports are unified and saved in the `output/` directory.

## 📁 Project Structure

```text
rss-news-summarizer/
├── main.py              # Main entry point
├── app/                 # Source code
│   ├── core/            # Core logic (Fetcher, Translator, Processor, Renderer)
├── config/              # Configuration
│   ├── settings.py      # RSS feed configurations
│   └── categories.json  # Keyword dimension table (Customizable)
├── output/              # Generated Markdown reports
└── requirements.txt     # Dependencies
```

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure RSS Feeds
Edit the `RSS_FEEDS` list in `config/settings.py` to add your preferred RSS URLs.

### 3. Customize Keywords
Edit `config/categories.json`. You can add new categories or update keywords in existing ones. Matching is case-insensitive.

### 4. Run the Script
```bash
# Default: Fetch articles from the last 1 day
python main.py

# Fetch articles from the last 7 days
python main.py --days 7

# Fetch a specific date range (YYYYMMDD-YYYYMMDD)
python main.py --range 20260101-20260107
```

## 📄 Notes
- This project uses free translation APIs. Please avoid high-frequency concurrent calls to prevent temporary IP blocks.
- Reports are automatically saved in the `output/` folder.
