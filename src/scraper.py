import logging
from dataclasses import dataclass, field
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup

from src.config import MAX_ARTICLES_PER_CATEGORY, NEWS_CATEGORIES

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class Article:
    title: str
    url: str
    category: str
    published: str = ""
    summary: str = ""


@dataclass
class NewsFetchResult:
    categories: dict[str, list[Article]] = field(default_factory=dict)
    fetch_time: str = ""


def fetch_rss_articles(rss_url: str, keywords: list[str], category: str) -> list[Article]:
    """RSSフィードから記事を取得し、キーワードでフィルタリングする"""
    articles = []
    try:
        feed = feedparser.parse(rss_url, agent=USER_AGENT)
        if feed.bozo and not feed.entries:
            logger.warning("RSSフィード解析エラー: %s - %s", rss_url, feed.bozo_exception)
            return articles

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))
            published = entry.get("published", entry.get("updated", ""))

            # キーワードマッチング: タイトルまたは要約にキーワードが含まれるか
            text = f"{title} {summary}".lower()
            if any(kw.lower() in text for kw in keywords):
                articles.append(Article(
                    title=title,
                    url=link,
                    category=category,
                    published=published,
                    summary=summary[:200] if summary else "",
                ))

        logger.info("RSS [%s] %d件取得 (フィード: %d件中)", category, len(articles), len(feed.entries))
    except Exception:
        logger.exception("RSS取得エラー [%s]: %s", category, rss_url)

    return articles[:MAX_ARTICLES_PER_CATEGORY]


def scrape_nikkei_page(url: str, category: str) -> list[Article]:
    """日経新聞のカテゴリページからニュース見出しをスクレイピングする"""
    articles = []
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 記事リンクを探す (日経のページ構造に合わせた複数のセレクタを試行)
        selectors = [
            "a[href*='/article/']",
            "a[href*='/news/']",
            ".articleList a",
            "[class*='headline'] a",
            "[class*='article'] a",
        ]

        seen_urls = set()
        for selector in selectors:
            for link_tag in soup.select(selector):
                href = link_tag.get("href", "")
                title = link_tag.get_text(strip=True)

                if not title or len(title) < 5:
                    continue

                # 相対URLを絶対URLに変換
                if href.startswith("/"):
                    href = f"https://www.nikkei.com{href}"

                if href in seen_urls:
                    continue
                seen_urls.add(href)

                articles.append(Article(
                    title=title,
                    url=href,
                    category=category,
                ))

            if articles:
                break

        logger.info("スクレイピング [%s] %d件取得: %s", category, len(articles), url)
    except Exception:
        logger.exception("スクレイピングエラー [%s]: %s", category, url)

    return articles[:MAX_ARTICLES_PER_CATEGORY]


def fetch_all_news() -> NewsFetchResult:
    """全カテゴリのニュースを取得する"""
    result = NewsFetchResult(
        fetch_time=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
    )

    for category, config in NEWS_CATEGORIES.items():
        articles = []

        # まずRSSフィードからキーワードフィルタリングで取得
        rss_articles = fetch_rss_articles(
            config["rss_url"],
            config["keywords"],
            category,
        )
        articles.extend(rss_articles)

        # RSS記事が少ない場合はスクレイピングで補完
        if len(articles) < MAX_ARTICLES_PER_CATEGORY:
            scraped = scrape_nikkei_page(config["nikkei_url"], category)
            # 重複排除
            existing_urls = {a.url for a in articles}
            for article in scraped:
                if article.url not in existing_urls and len(articles) < MAX_ARTICLES_PER_CATEGORY:
                    articles.append(article)
                    existing_urls.add(article.url)

        result.categories[category] = articles
        logger.info("カテゴリ [%s] 合計: %d件", category, len(articles))

    return result
