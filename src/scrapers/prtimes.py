"""
PR TIMES スクレイパー
プレスリリースから資金調達・M&A情報を収集
"""

import logging
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin

from bs4 import Tag

from src.models import Article
from .base import BaseScraper

logger = logging.getLogger(__name__)


class PRTimesScraper(BaseScraper):
    """PR TIMESスクレイパー"""

    source_name = "PR TIMES"
    base_url = "https://prtimes.jp"

    # 資金調達・M&A関連のキーワード検索URL
    search_keywords = [
        "資金調達",
        "シリーズA",
        "シリーズB",
        "M%26A",  # M&A (URL encoded)
        "買収",
        "出資",
    ]

    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        """PR TIMESから記事を収集"""
        if since is None:
            since = self.get_default_since()

        articles = []

        for keyword in self.search_keywords:
            keyword_articles = self._search_keyword(keyword, since)
            articles.extend(keyword_articles)

        # 重複除去（URLベース）
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.source_url not in seen_urls:
                seen_urls.add(article.source_url)
                unique_articles.append(article)

        logger.info(f"PR TIMES: collected {len(unique_articles)} unique articles")
        return self.filter_relevant_articles(unique_articles)

    def _search_keyword(
        self, keyword: str, since: datetime
    ) -> List[Article]:
        """キーワードで検索"""
        articles = []
        search_url = f"{self.base_url}/main/action.php?run=html&page=searchkey&search_word={keyword}"

        soup = self.fetch_page(search_url)
        if soup is None:
            return articles

        # 検索結果から記事を抽出
        article_items = soup.select("article.list-article__item")

        for item in article_items[:20]:  # 最新20件
            article = self._parse_article_item(item)
            if article and (article.published_at is None or article.published_at >= since):
                articles.append(article)

        return articles

    def _parse_article_item(self, item: Tag) -> Optional[Article]:
        """記事アイテムをパース"""
        try:
            # リンクとタイトル
            link_elem = item.select_one("a.list-article__link")
            if not link_elem:
                return None

            url = urljoin(self.base_url, link_elem.get("href", ""))
            title_elem = item.select_one(".list-article__title")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if not title:
                return None

            # 日付
            date_elem = item.select_one(".list-article__date")
            published_at = None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_at = self._parse_date(date_text)

            # 企業名
            company_elem = item.select_one(".list-article__company")
            company_name = (
                company_elem.get_text(strip=True) if company_elem else None
            )

            return Article(
                source=self.source_name,
                source_url=url,
                title=title,
                published_at=published_at,
                company_name_ja=company_name,
            )

        except Exception as e:
            logger.error(f"Error parsing PR TIMES article: {e}")
            return None

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """日付テキストをパース"""
        try:
            # "2024年1月15日 10:00" 形式
            date_text = date_text.replace("年", "-").replace("月", "-").replace("日", "")
            parts = date_text.split()
            date_part = parts[0]
            return datetime.strptime(date_part, "%Y-%m-%d")
        except (ValueError, IndexError):
            return None

    def fetch_article_detail(self, url: str) -> Optional[str]:
        """記事の詳細を取得"""
        soup = self.fetch_page(url)
        if soup is None:
            return None

        content_elem = soup.select_one(".rich-text, .article-body")
        if content_elem:
            return content_elem.get_text(strip=True)
        return None
