"""
TechCrunch Japan スクレイパー
スタートアップニュースを収集
"""

import logging
from typing import List, Optional
from datetime import datetime

import feedparser

from src.models import Article
from .base import BaseScraper

logger = logging.getLogger(__name__)


class TechCrunchJPScraper(BaseScraper):
    """TechCrunch Japanスクレイパー（RSSフィード利用）"""

    source_name = "TechCrunch Japan"
    base_url = "https://jp.techcrunch.com"

    # RSSフィードURL
    rss_feeds = [
        "https://jp.techcrunch.com/feed/",
    ]

    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        """TechCrunch JapanからRSSで記事を収集"""
        if since is None:
            since = self.get_default_since()

        articles = []

        for feed_url in self.rss_feeds:
            feed_articles = self._parse_feed(feed_url, since)
            articles.extend(feed_articles)

        logger.info(f"TechCrunch Japan: collected {len(articles)} articles")
        return self.filter_relevant_articles(articles)

    def _parse_feed(self, feed_url: str, since: datetime) -> List[Article]:
        """RSSフィードをパース"""
        articles = []

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                article = self._parse_entry(entry)
                if article and (
                    article.published_at is None or article.published_at >= since
                ):
                    articles.append(article)

        except Exception as e:
            logger.error(f"Error parsing TechCrunch feed: {e}")

        return articles

    def _parse_entry(self, entry) -> Optional[Article]:
        """RSSエントリをパース"""
        try:
            title = entry.get("title", "")
            url = entry.get("link", "")

            if not title or not url:
                return None

            # 日付パース
            published_at = None
            if "published_parsed" in entry and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])

            # 本文（サマリー）
            content = ""
            if "summary" in entry:
                content = entry.summary
            elif "content" in entry and entry.content:
                content = entry.content[0].get("value", "")

            return Article(
                source=self.source_name,
                source_url=url,
                title=title,
                published_at=published_at,
                content_raw=content,
            )

        except Exception as e:
            logger.error(f"Error parsing TechCrunch entry: {e}")
            return None
