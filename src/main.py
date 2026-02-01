"""
メインエントリーポイント
日次ダイジェスト生成・配信のオーケストレーション
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import List

from config.settings import settings
from src.models import Article, DealSummary
from src.services.collector import CollectorService
from src.services.summarizer import SummarizerService
from src.services.email_sender import EmailService

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def run_daily_digest() -> bool:
    """
    日次ダイジェストを実行

    1. 全ソースからニュースを収集
    2. AIで要約・構造化
    3. メールで配信

    Returns:
        bool: 成功した場合True
    """
    logger.info("=" * 60)
    logger.info("Starting daily digest generation")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # 1. データ収集
        logger.info("Step 1: Collecting articles from all sources...")
        collector = CollectorService()

        # 過去24時間の記事を取得
        since = datetime.utcnow() - timedelta(hours=24)
        articles = collector.collect_all(since=since)

        if not articles:
            logger.warning("No articles collected, skipping digest")
            return True

        logger.info(f"Collected {len(articles)} articles")

        # データベースに保存
        saved_count = collector.save_articles(articles)
        logger.info(f"Saved {saved_count} new articles to database")

        # 2. 要約生成
        logger.info("Step 2: Summarizing articles with AI...")
        if not settings.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY not set, cannot summarize")
            return False

        summarizer = SummarizerService(
            api_key=settings.anthropic_api_key,
            model=settings.summary_model,
        )

        # 記事の詳細を取得して要約
        summaries: List[DealSummary] = []
        for article in articles[: settings.max_articles_per_digest]:
            summary = summarizer.summarize_article(article)
            if summary:
                summaries.append(summary)

        logger.info(f"Generated {len(summaries)} summaries")

        if not summaries:
            logger.warning("No summaries generated, skipping email")
            return True

        # 3. メール送信
        logger.info("Step 3: Sending email digest...")
        if not settings.resend_api_key or not settings.email_to:
            logger.error("Email configuration incomplete (RESEND_API_KEY, EMAIL_TO)")
            return False

        email_service = EmailService(
            api_key=settings.resend_api_key,
            from_email=settings.email_from,
            template_dir="templates",
        )

        to_emails = [e.strip() for e in settings.email_to.split(",")]

        success = email_service.send_daily_digest(
            to_emails=to_emails,
            summaries=summaries,
            date=datetime.now(),
        )

        if success:
            logger.info("Email sent successfully!")
            # 送信済みにマーク
            # collector.mark_as_sent([a.id for a in articles])
        else:
            logger.error("Failed to send email")
            return False

        logger.info("=" * 60)
        logger.info("Daily digest completed successfully!")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.exception(f"Error running daily digest: {e}")
        return False


def collect_only() -> bool:
    """データ収集のみ実行（テスト用）"""
    logger.info("Running collection only...")

    collector = CollectorService()
    since = datetime.utcnow() - timedelta(hours=24)
    articles = collector.collect_all(since=since)

    logger.info(f"Collected {len(articles)} articles:")
    for article in articles[:10]:
        logger.info(f"  - [{article.source}] {article.title[:50]}...")

    if articles:
        saved = collector.save_articles(articles)
        logger.info(f"Saved {saved} articles to database")

    return True


def test_email() -> bool:
    """メール送信テスト"""
    logger.info("Testing email sending...")

    if not settings.resend_api_key or not settings.email_to:
        logger.error("Email configuration incomplete")
        return False

    # テスト用サマリー
    test_summary = DealSummary(
        company_name_ja="テスト株式会社",
        company_name_en="Test Inc.",
        deal_type="funding",
        funding_round="series_a",
        amount_display="10億円",
        investors_display="テストVC、サンプルキャピタル",
        industry="テクノロジー",
        summary="これはテスト用の要約です。システムが正常に動作しているか確認しています。",
        source="テストソース",
        source_url="https://example.com/test",
        published_at=datetime.now(),
    )

    email_service = EmailService(
        api_key=settings.resend_api_key,
        from_email=settings.email_from,
        template_dir="templates",
    )

    to_emails = [e.strip() for e in settings.email_to.split(",")]

    return email_service.send_daily_digest(
        to_emails=to_emails,
        summaries=[test_summary],
        date=datetime.now(),
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Japan Startup News Digest")
    parser.add_argument(
        "--mode",
        choices=["digest", "collect", "test-email"],
        default="digest",
        help="Execution mode",
    )

    args = parser.parse_args()

    if args.mode == "digest":
        success = run_daily_digest()
    elif args.mode == "collect":
        success = collect_only()
    elif args.mode == "test-email":
        success = test_email()
    else:
        success = False

    sys.exit(0 if success else 1)
