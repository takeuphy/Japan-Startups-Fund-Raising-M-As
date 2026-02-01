"""
NewsPicks スクレイパー
有料会員向けコンテンツを含む
"""

import logging
import re
from typing import List, Optional
from datetime import datetime

from src.models import Article
from .base import BaseScraper

logger = logging.getLogger(__name__)


class NewsPicksScraper(BaseScraper):
    """NewsPicksスクレイパー"""

    source_name = "NewsPicks"
    base_url = "https://newspicks.com"

    # スタートアップ・投資関連のテーマ
    themes = [
        "/theme/8",  # スタートアップ
        "/theme/1",  # ビジネス
        "/theme/13",  # テクノロジー
    ]

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.email = email
        self.password = password
        self._logged_in = False

    def login(self) -> bool:
        """NewsPicksにログイン"""
        if not self.email or not self.password:
            logger.warning(
                "NewsPicks credentials not provided, using public content only"
            )
            return False

        # 注: 実際のログイン実装はサイトの仕様に応じて調整が必要
        logger.info("NewsPicks login attempted (implementation needed)")
        return False

    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        """NewsPicksから記事を収集"""
        if since is None:
            since = self.get_default_since()

        # 認証情報があればログイン試行
        if self.email and self.password and not self._logged_in:
            self.login()

        articles = []

        # テーマページから収集
        for theme in self.themes:
            theme_articles = self._scrape_theme(theme, since)
            articles.extend(theme_articles)

        # 検索による収集
        search_keywords = ["資金調達", "M&A", "スタートアップ 投資"]
        for keyword in search_keywords:
            search_articles = self._search(keyword, since)
            articles.extend(search_articles)

        # 重複除去
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.source_url not in seen_urls:
                seen_urls.add(article.source_url)
                unique_articles.append(article)

        logger.info(f"NewsPicks: collected {len(unique_articles)} unique articles")
        return self.filter_relevant_articles(unique_articles)

    def _scrape_theme(self, theme_path: str, since: datetime) -> List[Article]:
        """テーマページをスクレイプ"""
        articles = []
        url = f"{self.base_url}{theme_path}"

        soup = self.fetch_page(url)
        if soup is None:
            return articles

        # 記事カード取得
        article_items = soup.select("[class*='NewsCard'], [class*='article']")

        for item in article_items[:20]:
            article = self._parse_article_item(item)
            if article and (
                article.published_at is None or article.published_at >= since
            ):
                articles.append(article)

        return articles

    def _search(self, keyword: str, since: datetime) -> List[Article]:
        """キーワード検索"""
        articles = []
        search_url = f"{self.base_url}/search"

        # NewsPicksの検索APIを使用
        # 注: 実際のAPI仕様に合わせて調整が必要
        params = {"q": keyword}

        soup = self.fetch_page(f"{search_url}?q={keyword}")
        if soup is None:
            return articles

        article_items = soup.select("[class*='NewsCard'], [class*='article']")

        for item in article_items[:10]:
            article = self._parse_article_item(item)
            if article and (
                article.published_at is None or article.published_at >= since
            ):
                articles.append(article)

        return articles

    def _parse_article_item(self, item) -> Optional[Article]:
        """記事アイテムをパース"""
        try:
            # リンクとタイトル
            link_elem = item.select_one("a[href*='/news/']")
            if not link_elem:
                return None

            url = link_elem.get("href", "")
            if not url.startswith("http"):
                url = f"{self.base_url}{url}"

            title_elem = item.select_one("[class*='title'], h2, h3")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if not title:
                title = link_elem.get_text(strip=True)

            if not title:
                return None

            # 日付
            date_elem = item.select_one("time, [class*='date'], [class*='time']")
            published_at = None
            if date_elem:
                date_text = date_elem.get("datetime") or date_elem.get_text(strip=True)
                published_at = self._parse_date(date_text)

            # 出典メディア
            source_elem = item.select_one("[class*='publisher'], [class*='source']")
            original_source = (
                source_elem.get_text(strip=True) if source_elem else None
            )

            return Article(
                source=f"{self.source_name}"
                + (f" ({original_source})" if original_source else ""),
                source_url=url,
                title=title,
                published_at=published_at,
            )

        except Exception as e:
            logger.error(f"Error parsing NewsPicks article: {e}")
            return None

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """日付をパース"""
        try:
            # ISO format
            if "T" in date_text:
                return datetime.fromisoformat(date_text.replace("Z", "+00:00"))

            # 相対時間（"2時間前" など）はスキップ
            if "前" in date_text:
                return datetime.utcnow()

            # "2024/1/15" format
            match = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", date_text)
            if match:
                return datetime(
                    int(match.group(1)), int(match.group(2)), int(match.group(3))
                )
        except (ValueError, AttributeError):
            pass
        return None
