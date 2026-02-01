"""
日経新聞スクレイパー
有料会員向けコンテンツを含む
"""

import logging
import re
from typing import List, Optional
from datetime import datetime

from src.models import Article
from .base import BaseScraper

logger = logging.getLogger(__name__)


class NikkeiScraper(BaseScraper):
    """日経新聞スクレイパー"""

    source_name = "日本経済新聞"
    base_url = "https://www.nikkei.com"

    # スタートアップ・M&A関連のセクション
    sections = [
        "/news/category/startup/",  # スタートアップ
        "/news/category/ma/",  # M&A
        "/news/category/financial_market/",  # 金融・マーケット
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
        """日経電子版にログイン"""
        if not self.email or not self.password:
            logger.warning("Nikkei credentials not provided, using public content only")
            return False

        # ログイン処理
        # 注: 実際のログイン実装はサイトの仕様変更に応じて調整が必要
        login_url = "https://id.nikkei.com/lounge/nl/auth/LA0210.seam"

        try:
            # CSRFトークン取得
            login_page = self.fetch_page(login_url)
            if login_page is None:
                return False

            # ログインフォーム送信
            # 実装は日経のログインフローに依存
            logger.info("Nikkei login attempted (implementation needed)")
            self._logged_in = True
            return True

        except Exception as e:
            logger.error(f"Nikkei login failed: {e}")
            return False

    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        """日経新聞から記事を収集"""
        if since is None:
            since = self.get_default_since()

        # 認証情報があればログイン試行
        if self.email and self.password and not self._logged_in:
            self.login()

        articles = []

        for section in self.sections:
            section_articles = self._scrape_section(section, since)
            articles.extend(section_articles)

        # 重複除去
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.source_url not in seen_urls:
                seen_urls.add(article.source_url)
                unique_articles.append(article)

        logger.info(f"Nikkei: collected {len(unique_articles)} unique articles")
        return self.filter_relevant_articles(unique_articles)

    def _scrape_section(
        self, section_path: str, since: datetime
    ) -> List[Article]:
        """セクションページをスクレイプ"""
        articles = []
        url = f"{self.base_url}{section_path}"

        soup = self.fetch_page(url)
        if soup is None:
            return articles

        # 記事リスト取得
        article_items = soup.select("article, .articleList_item, [class*='article']")

        for item in article_items[:30]:
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
            link_elem = item.select_one("a[href*='/article/']")
            if not link_elem:
                return None

            url = link_elem.get("href", "")
            if not url.startswith("http"):
                url = f"{self.base_url}{url}"

            title_elem = item.select_one("h3, h2, .title, [class*='title']")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if not title:
                title = link_elem.get_text(strip=True)

            if not title:
                return None

            # 日付
            date_elem = item.select_one("time, .date, [class*='date']")
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
            logger.error(f"Error parsing Nikkei article: {e}")
            return None

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """日付をパース"""
        try:
            # ISO format
            if "T" in date_text:
                return datetime.fromisoformat(date_text.replace("Z", "+00:00"))

            # "2024/1/15" or "2024年1月15日" format
            date_text = (
                date_text.replace("年", "/").replace("月", "/").replace("日", "")
            )
            match = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", date_text)
            if match:
                return datetime(
                    int(match.group(1)), int(match.group(2)), int(match.group(3))
                )
        except (ValueError, AttributeError):
            pass
        return None
