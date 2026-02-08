import logging
import sys

from src.config import DISCORD_WEBHOOK_URL, LOG_LEVEL
from src.discord_sender import send_to_discord
from src.scraper import fetch_all_news

# ログ設定
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def job_fetch_and_send():
    """ニュース取得・配信ジョブ"""
    logger.info("=== ニュース取得・配信ジョブ開始 ===")
    news = fetch_all_news()

    total = sum(len(articles) for articles in news.categories.values())
    logger.info("取得記事数合計: %d件", total)

    if total == 0:
        logger.warning("記事が取得できませんでした。配信をスキップします。")
        return False

    success = send_to_discord(news)
    if success:
        logger.info("=== 配信完了 ===")
    else:
        logger.error("=== 配信失敗 ===")
    return success


def main():
    """メインエントリポイント (Cloud Run Jobs 用: 実行して終了)"""
    if not DISCORD_WEBHOOK_URL:
        logger.error(
            "DISCORD_WEBHOOK_URL が設定されていません。\n"
            "環境変数 DISCORD_WEBHOOK_URL を設定してください。"
        )
        sys.exit(1)

    logger.info("日経ニュース Discord 配信ボット実行開始")

    try:
        success = job_fetch_and_send()
        if not success:
            sys.exit(1)
    except Exception:
        logger.exception("ジョブ実行中にエラーが発生しました")
        sys.exit(1)

    logger.info("正常終了")


if __name__ == "__main__":
    main()
