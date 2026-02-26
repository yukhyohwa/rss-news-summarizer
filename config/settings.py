# config.py
import os

# --- RSS 源列表 ---
# 在此列表中添加或删除您想订阅的 RSS 源 URL
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
#   "https://www.theguardian.com/profile/editorial/rss",
    "https://cn.nytimes.com/rss/", 
#   "https://www.france24.com/en/rss",
    "https://www.lefigaro.fr/rss/figaro_actualites.xml",
#   "https://feeds.washingtonpost.com/rss/politics",
    "https://plink.anyfeeder.com/bbc/world"
]
# --- 屏蔽词列表 ---
# 包含以下词汇的文章将被过滤掉 (匹配标题或摘要)
BLOCKED_KEYWORDS = [
    "曲棍球",
    "非洲杯",
    "AFCON",
    "Hockey",
    "法轮功",
    "Falun Gong",
    # 政治/敏感内容
    "爱泼斯坦", "Epstein",
    "教皇利奥", "Pope Leo",
    # 会议/峰会 (TechCrunch 相关)
    "TechCrunch Disrupt",
    "Founders Summit","TechCrunch Founder Summit",
    # 巴黎市政 (Le Figaro 相关)
    "Mairie de Paris", "Hôtel de Ville de Paris", "Paris City Hall","Municipales",
    # 体育类 (法甲、欧冠等)
    "Ligue 1", "Champions League", 
    "Football", "PSG", "Olympique de Marseille", "Real Madrid",
]

# --- 渲染选项 ---
# 是否在报表中显示图片 (默认为 False)
SHOW_IMAGES = False
