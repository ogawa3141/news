import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import DISCORD_WEBHOOK_URL, LOG_LEVEL, SCHEDULE_TIMES, TIMEZONE
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
    try:
        news = fetch_all_news()

        total = sum(len(articles) for articles in news.categories.values())
        logger.info("取得記事数合計: %d件", total)

        if total == 0:
            logger.warning("記事が取得できませんでした。配信をスキップします。")
            return

        success = send_to_discord(news)
        if success:
            logger.info("=== 配信完了 ===")
        else:
            logger.error("=== 配信失敗 ===")
    except Exception:
        logger.exception("ジョブ実行中にエラーが発生しました")


def main():
    """メインエントリポイント"""
    if not DISCORD_WEBHOOK_URL:
        logger.error(
            "DISCORD_WEBHOOK_URL が設定されていません。\n"
            ".env ファイルに DISCORD_WEBHOOK_URL を設定してください。"
        )
        sys.exit(1)

    logger.info("日経ニュース Discord 配信ボット起動")
    logger.info("タイムゾーン: %s", TIMEZONE)
    logger.info("配信スケジュール: %s", SCHEDULE_TIMES)

    scheduler = BlockingScheduler(timezone=TIMEZONE)

    # スケジュール登録
    for schedule in SCHEDULE_TIMES:
        trigger = CronTrigger(
            hour=schedule["hour"],
            minute=schedule["minute"],
            timezone=TIMEZONE,
        )
        scheduler.add_job(
            job_fetch_and_send,
            trigger=trigger,
            id=f"news_{schedule['hour']}_{schedule['minute']:02d}",
            name=f"ニュース配信 {schedule['hour']}:{schedule['minute']:02d}",
        )
        logger.info(
            "スケジュール登録: %d:%02d",
            schedule["hour"],
            schedule["minute"],
        )

    # 起動時に一度実行するオプション
    if "--run-now" in sys.argv:
        logger.info("起動時実行モード: 即座にニュースを取得・配信します")
        job_fetch_and_send()

    # シグナルハンドラ
    def shutdown(signum, frame):
        logger.info("シャットダウンシグナル受信。スケジューラを停止します。")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        logger.info("スケジューラ起動。Ctrl+C で停止。")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("ボット停止")


if __name__ == "__main__":
    main()
