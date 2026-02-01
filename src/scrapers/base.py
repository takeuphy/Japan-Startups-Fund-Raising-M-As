"""
ベーススクレイパー
全てのスクレイパーの共通機能を提供
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from src.models import Article

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """スクレイパーの基底クラス"""

    source_name: str = "unknown"
    base_url: str = ""

    def __init__(
        self,
        timeout: int = 30,
        delay: float = 1.0,
        user_agent: Optional[str] = None,
    ):
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent
                or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            }
        )
        self._last_request_time: Optional[float] = None

    def _rate_limit(self) -> None:
        """レート制限: リクエスト間隔を制御"""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """ページを取得してパース"""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def fetch_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """JSON APIを取得"""
        self._rate_limit()
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch JSON from {url}: {e}")
            return None

    @abstractmethod
    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        """
        記事を収集

        Args:
            since: この日時以降の記事のみ取得（指定なしの場合は過去24時間）

        Returns:
            収集した記事のリスト
        """
        pass

    def filter_relevant_articles(self, articles: List[Article]) -> List[Article]:
        """資金調達・M&A関連の記事のみフィルタ"""
        keywords = [
            # 資金調達関連
            "資金調達",
            "調達",
            "出資",
            "投資",
            "ファンド",
            "増資",
            "シード",
            "シリーズ",
            "ラウンド",
            "funding",
            "investment",
            "series",
            "raise",
            "venture",
            "VC",
            # M&A関連
            "買収",
            "合併",
            "M&A",
            "子会社化",
            "グループ入り",
            "acquisition",
            "merger",
            "acquire",
            # IPO関連
            "上場",
            "IPO",
            "株式公開",
        ]

        relevant = []
        for article in articles:
            text = f"{article.title} {article.content_raw or ''}"
            if any(kw.lower() in text.lower() for kw in keywords):
                article.is_relevant = True
                relevant.append(article)

        logger.info(
            f"{self.source_name}: {len(relevant)}/{len(articles)} relevant articles"
        )
        return relevant

    def get_default_since(self) -> datetime:
        """デフォルトの取得開始日時（24時間前）"""
        return datetime.utcnow() - timedelta(hours=24)
