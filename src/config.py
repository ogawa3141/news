import os
from dotenv import load_dotenv

load_dotenv()

# Discord Webhook URL
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# 取得するニュースカテゴリとRSSフィードURL
NEWS_CATEGORIES = {
    "ビジネス": {
        "rss_url": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",
        "nikkei_url": "https://www.nikkei.com/economy/",
        "keywords": ["企業", "経営", "ビジネス", "業績", "決算", "産業"],
    },
    "株式・マーケット": {
        "rss_url": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",
        "nikkei_url": "https://www.nikkei.com/markets/",
        "keywords": ["株", "市場", "日経平均", "為替", "債券", "投資", "相場", "ダウ", "TOPIX"],
    },
    "不動産": {
        "rss_url": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",
        "nikkei_url": "https://www.nikkei.com/",
        "keywords": ["不動産", "住宅", "マンション", "地価", "オフィス", "REIT", "賃貸"],
    },
    "世界情勢": {
        "rss_url": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",
        "nikkei_url": "https://www.nikkei.com/international/",
        "keywords": ["米国", "中国", "欧州", "アジア", "国際", "外交", "貿易", "NATO", "EU"],
    },
    "日本の政策": {
        "rss_url": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",
        "nikkei_url": "https://www.nikkei.com/politics/",
        "keywords": ["政府", "政策", "法案", "国会", "首相", "内閣", "規制", "税制", "予算"],
    },
}

# 各カテゴリの最大記事数
MAX_ARTICLES_PER_CATEGORY = int(os.getenv("MAX_ARTICLES_PER_CATEGORY", "5"))

# ログレベル
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
