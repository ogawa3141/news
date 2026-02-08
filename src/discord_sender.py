import logging
import time

import requests

from src.config import DISCORD_WEBHOOK_URL
from src.scraper import NewsFetchResult

logger = logging.getLogger(__name__)

# Discord Embedのカラー (カテゴリ別)
CATEGORY_COLORS = {
    "ビジネス": 0x1E90FF,       # DodgerBlue
    "株式・マーケット": 0x32CD32,  # LimeGreen
    "不動産": 0xFF8C00,          # DarkOrange
    "世界情勢": 0xDC143C,        # Crimson
    "日本の政策": 0x9370DB,      # MediumPurple
}

CATEGORY_EMOJIS = {
    "ビジネス": "\U0001f4bc",
    "株式・マーケット": "\U0001f4c8",
    "不動産": "\U0001f3e0",
    "世界情勢": "\U0001f30d",
    "日本の政策": "\U0001f3db\ufe0f",
}


def send_to_discord(news: NewsFetchResult) -> bool:
    """ニュースをDiscord Webhookで送信する"""
    if not DISCORD_WEBHOOK_URL:
        logger.error("DISCORD_WEBHOOK_URL が設定されていません")
        return False

    embeds = []
    for category, articles in news.categories.items():
        if not articles:
            continue

        emoji = CATEGORY_EMOJIS.get(category, "\U0001f4f0")
        color = CATEGORY_COLORS.get(category, 0x808080)

        # 記事リストをフォーマット
        lines = []
        for i, article in enumerate(articles, 1):
            lines.append(f"**{i}.** [{article.title}]({article.url})")
            if article.summary:
                # 要約を短く切り詰め
                short_summary = article.summary[:100]
                if len(article.summary) > 100:
                    short_summary += "..."
                lines.append(f"   {short_summary}")
            lines.append("")

        description = "\n".join(lines)
        if len(description) > 4096:
            description = description[:4090] + "\n..."

        embeds.append({
            "title": f"{emoji} {category}",
            "description": description,
            "color": color,
        })

    if not embeds:
        logger.warning("送信するニュースがありません")
        return False

    # Discord Webhookの制限: 1メッセージあたりembeds最大10個
    # 5カテゴリなので1回で送信可能
    payload = {
        "content": f"## \U0001f4f0 日経ニュース速報 - {news.fetch_time}",
        "embeds": embeds,
    }

    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10,
        )
        if resp.status_code == 429:
            # レート制限: リトライ
            retry_after = resp.json().get("retry_after", 5)
            logger.warning("Discord レート制限。%s秒後にリトライ", retry_after)
            time.sleep(retry_after)
            resp = requests.post(
                DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=10,
            )

        resp.raise_for_status()
        logger.info("Discord送信成功 (ステータス: %d)", resp.status_code)
        return True
    except Exception:
        logger.exception("Discord送信エラー")
        return False
