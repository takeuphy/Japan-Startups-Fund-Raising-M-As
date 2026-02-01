"""
INITIAL (旧 entrepedia) スクレイパー
日本のスタートアップデータベース
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.models import Article
from .base import BaseScraper

logger = logging.getLogger(__name__)


class InitialScraper(BaseScraper):
    """INITIALスクレイパー"""

    source_name = "INITIAL"
    base_url = "https://initial.inc"

    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        """INITIALから資金調達ニュースを収集"""
        if since is None:
            since = self.get_default_since()

        articles = []

        # ニュースページから収集
        news_articles = self._scrape_news(since)
        articles.extend(news_articles)

        # 資金調達一覧から収集
        funding_articles = self._scrape_funding_list(since)
        articles.extend(funding_articles)

        # 重複除去
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.source_url not in seen_urls:
                seen_urls.add(article.source_url)
                unique_articles.append(article)

        logger.info(f"INITIAL: collected {len(unique_articles)} unique articles")
        return unique_articles  # INITIAL は資金調達専門なのでフィルタ不要

    def _scrape_news(self, since: datetime) -> List[Article]:
        """ニュースページをスクレイプ"""
        articles = []
        url = f"{self.base_url}/articles"

        soup = self.fetch_page(url)
        if soup is None:
            return articles

        # 記事リスト取得
        article_items = soup.select("article, [class*='article'], [class*='card']")

        for item in article_items[:30]:
            article = self._parse_article_item(item)
            if article and (
                article.published_at is None or article.published_at >= since
            ):
                articles.append(article)

        return articles

    def _scrape_funding_list(self, since: datetime) -> List[Article]:
        """資金調達一覧をスクレイプ"""
        articles = []
        url = f"{self.base_url}/funding"

        soup = self.fetch_page(url)
        if soup is None:
            return articles

        # 資金調達リスト取得
        funding_items = soup.select("[class*='funding'], [class*='deal'], tr")

        for item in funding_items[:50]:
            article = self._parse_funding_item(item)
            if article and (
                article.published_at is None or article.published_at >= since
            ):
                articles.append(article)

        return articles

    def _parse_article_item(self, item) -> Optional[Article]:
        """記事アイテムをパース"""
        try:
            link_elem = item.select_one("a[href]")
            if not link_elem:
                return None

            url = link_elem.get("href", "")
            if not url.startswith("http"):
                url = f"{self.base_url}{url}"

            title_elem = item.select_one("h2, h3, [class*='title']")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if not title:
                title = link_elem.get_text(strip=True)

            if not title:
                return None

            # 日付
            date_elem = item.select_one("time, [class*='date']")
            published_at = None
            if date_elem:
                date_text = date_elem.get("datetime") or date_elem.get_text(strip=True)
                published_at = self._parse_date(date_text)

            return Article(
                source=self.source_name,
                source_url=url,
                title=title,
                published_at=published_at,
            )

        except Exception as e:
            logger.error(f"Error parsing INITIAL article: {e}")
            return None

    def _parse_funding_item(self, item) -> Optional[Article]:
        """資金調達アイテムをパース"""
        try:
            # 企業名
            company_elem = item.select_one(
                "[class*='company'], [class*='name'], td:first-child"
            )
            if not company_elem:
                return None

            company_name = company_elem.get_text(strip=True)

            # リンク
            link_elem = item.select_one("a[href]")
            url = ""
            if link_elem:
                url = link_elem.get("href", "")
                if not url.startswith("http"):
                    url = f"{self.base_url}{url}"
            else:
                url = f"{self.base_url}/company/{company_name}"

            # 金額
            amount_elem = item.select_one("[class*='amount'], td:nth-child(2)")
            amount = amount_elem.get_text(strip=True) if amount_elem else ""

            # ラウンド
            round_elem = item.select_one("[class*='round'], td:nth-child(3)")
            funding_round = round_elem.get_text(strip=True) if round_elem else ""

            # 日付
            date_elem = item.select_one("[class*='date'], td:last-child, time")
            published_at = None
            if date_elem:
                date_text = date_elem.get("datetime") or date_elem.get_text(strip=True)
                published_at = self._parse_date(date_text)

            title = f"{company_name}が{amount}の資金調達"
            if funding_round:
                title += f"（{funding_round}）"

            return Article(
                source=self.source_name,
                source_url=url,
                title=title,
                published_at=published_at,
                company_name_ja=company_name,
                amount_original=amount,
            )

        except Exception as e:
            logger.error(f"Error parsing INITIAL funding item: {e}")
            return None

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """日付をパース"""
        try:
            # ISO format
            if "T" in date_text:
                return datetime.fromisoformat(date_text.replace("Z", "+00:00"))

            # 日本語形式
            date_text = (
                date_text.replace("年", "-").replace("月", "-").replace("日", "")
            )
            parts = date_text.strip().split("-")
            if len(parts) >= 3:
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass
        return None
