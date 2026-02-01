"""
データ収集サービス
全スクレイパーを統合してデータを収集
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from src.models import Article, ArticleDB, init_database
from src.scrapers import (
    PRTimesScraper,
    TechCrunchJPScraper,
    NikkeiScraper,
    NewsPicksScraper,
    InitialScraper,
    CrunchbaseScraper,
)
from config.settings import settings

logger = logging.getLogger(__name__)


class CollectorService:
    """データ収集サービス"""

    def __init__(
        self,
        database_url: Optional[str] = None,
        nikkei_email: Optional[str] = None,
        nikkei_password: Optional[str] = None,
        newspicks_email: Optional[str] = None,
        newspicks_password: Optional[str] = None,
        crunchbase_api_key: Optional[str] = None,
    ):
        self.database_url = database_url or settings.database_url
        self.SessionLocal = init_database(self.database_url)

        # スクレイパーを初期化
        self.scrapers = [
            PRTimesScraper(
                timeout=settings.request_timeout,
                delay=settings.request_delay,
                user_agent=settings.user_agent,
            ),
            TechCrunchJPScraper(
                timeout=settings.request_timeout,
                delay=settings.request_delay,
                user_agent=settings.user_agent,
            ),
            NikkeiScraper(
                email=nikkei_email or settings.nikkei_email,
                password=nikkei_password or settings.nikkei_password,
                timeout=settings.request_timeout,
                delay=settings.request_delay,
                user_agent=settings.user_agent,
            ),
            NewsPicksScraper(
                email=newspicks_email or settings.newspicks_email,
                password=newspicks_password or settings.newspicks_password,
                timeout=settings.request_timeout,
                delay=settings.request_delay,
                user_agent=settings.user_agent,
            ),
            InitialScraper(
                timeout=settings.request_timeout,
                delay=settings.request_delay,
                user_agent=settings.user_agent,
            ),
            CrunchbaseScraper(
                api_key=crunchbase_api_key or settings.crunchbase_api_key,
                timeout=settings.request_timeout,
                delay=settings.request_delay,
            ),
        ]

    def collect_all(self, since: Optional[datetime] = None) -> List[Article]:
        """全ソースからデータを収集"""
        if since is None:
            since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        all_articles = []

        for scraper in self.scrapers:
            try:
                logger.info(f"Collecting from {scraper.source_name}...")
                articles = scraper.scrape(since=since)
                all_articles.extend(articles)
                logger.info(f"{scraper.source_name}: {len(articles)} articles collected")
            except Exception as e:
                logger.error(f"Error collecting from {scraper.source_name}: {e}")
                continue

        # 重複除去（URLベース）
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.source_url not in seen_urls:
                seen_urls.add(article.source_url)
                unique_articles.append(article)

        logger.info(
            f"Total: {len(unique_articles)} unique articles from {len(all_articles)} total"
        )
        return unique_articles

    def save_articles(self, articles: List[Article]) -> int:
        """記事をデータベースに保存"""
        session: Session = self.SessionLocal()
        saved_count = 0

        try:
            for article in articles:
                # 既存チェック
                existing = (
                    session.query(ArticleDB)
                    .filter(ArticleDB.source_url == article.source_url)
                    .first()
                )

                if existing:
                    logger.debug(f"Skipping duplicate: {article.source_url}")
                    continue

                # 新規保存
                db_article = ArticleDB(
                    source=article.source,
                    source_url=article.source_url,
                    title=article.title,
                    published_at=article.published_at,
                    scraped_at=article.scraped_at,
                    company_name_ja=article.company_name_ja,
                    company_name_en=article.company_name_en,
                    deal_type=article.deal_type.value if article.deal_type else None,
                    funding_round=(
                        article.funding_round.value if article.funding_round else None
                    ),
                    amount_jpy=article.amount_jpy,
                    amount_original=article.amount_original,
                    investors=(
                        ",".join(article.investors) if article.investors else None
                    ),
                    acquirer=article.acquirer,
                    industry=article.industry,
                    sector=article.sector,
                    content_raw=article.content_raw,
                    summary=article.summary,
                    is_relevant=article.is_relevant,
                    is_summarized=article.is_summarized,
                    is_sent=article.is_sent,
                )
                session.add(db_article)
                saved_count += 1

            session.commit()
            logger.info(f"Saved {saved_count} new articles to database")

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving articles: {e}")
            raise
        finally:
            session.close()

        return saved_count

    def get_unsent_articles(self) -> List[ArticleDB]:
        """未送信の記事を取得"""
        session: Session = self.SessionLocal()

        try:
            articles = (
                session.query(ArticleDB)
                .filter(ArticleDB.is_sent == False)
                .filter(ArticleDB.is_relevant == True)
                .order_by(ArticleDB.published_at.desc())
                .limit(settings.max_articles_per_digest)
                .all()
            )
            return articles
        finally:
            session.close()

    def mark_as_sent(self, article_ids: List[int]) -> None:
        """記事を送信済みにマーク"""
        session: Session = self.SessionLocal()

        try:
            session.query(ArticleDB).filter(ArticleDB.id.in_(article_ids)).update(
                {"is_sent": True}, synchronize_session=False
            )
            session.commit()
            logger.info(f"Marked {len(article_ids)} articles as sent")
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking articles as sent: {e}")
            raise
        finally:
            session.close()
