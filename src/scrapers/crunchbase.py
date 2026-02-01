"""
Crunchbase スクレイパー/API クライアント
グローバルスタートアップデータベース
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.models import Article, DealType, FundingRound
from .base import BaseScraper

logger = logging.getLogger(__name__)


class CrunchbaseScraper(BaseScraper):
    """Crunchbase API クライアント"""

    source_name = "Crunchbase"
    base_url = "https://api.crunchbase.com/api/v4"

    # ラウンドマッピング
    ROUND_MAPPING = {
        "pre_seed": FundingRound.PRE_SEED,
        "seed": FundingRound.SEED,
        "series_a": FundingRound.SERIES_A,
        "series_b": FundingRound.SERIES_B,
        "series_c": FundingRound.SERIES_C,
        "series_d": FundingRound.SERIES_D,
        "series_e": FundingRound.SERIES_E_PLUS,
        "series_f": FundingRound.SERIES_E_PLUS,
        "debt_financing": FundingRound.DEBT,
        "grant": FundingRound.GRANT,
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        if api_key:
            self.session.headers.update({"X-cb-user-key": api_key})

    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        """Crunchbaseから日本のスタートアップ資金調達情報を取得"""
        if since is None:
            since = self.get_default_since()

        if not self.api_key:
            logger.warning("Crunchbase API key not provided, skipping")
            return []

        articles = []

        # 日本の資金調達ラウンドを取得
        funding_rounds = self._fetch_japan_funding_rounds(since)
        for round_data in funding_rounds:
            article = self._parse_funding_round(round_data)
            if article:
                articles.append(article)

        # 日本関連のM&Aを取得
        acquisitions = self._fetch_japan_acquisitions(since)
        for acq_data in acquisitions:
            article = self._parse_acquisition(acq_data)
            if article:
                articles.append(article)

        logger.info(f"Crunchbase: collected {len(articles)} articles")
        return articles

    def _fetch_japan_funding_rounds(self, since: datetime) -> List[Dict[str, Any]]:
        """日本の資金調達ラウンドを取得"""
        # Crunchbase API v4 エンドポイント
        url = f"{self.base_url}/searches/funding_rounds"

        # クエリ: 日本のスタートアップ、指定日以降
        since_str = since.strftime("%Y-%m-%d")

        payload = {
            "field_ids": [
                "identifier",
                "announced_on",
                "funded_organization_identifier",
                "money_raised",
                "investment_type",
                "investor_identifiers",
            ],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "funded_organization_location",
                    "operator_id": "includes",
                    "values": ["Japan"],
                },
                {
                    "type": "predicate",
                    "field_id": "announced_on",
                    "operator_id": "gte",
                    "values": [since_str],
                },
            ],
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "limit": 50,
        }

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("entities", [])
        except Exception as e:
            logger.error(f"Crunchbase funding rounds fetch failed: {e}")
            return []

    def _fetch_japan_acquisitions(self, since: datetime) -> List[Dict[str, Any]]:
        """日本関連のM&Aを取得"""
        url = f"{self.base_url}/searches/acquisitions"

        since_str = since.strftime("%Y-%m-%d")

        payload = {
            "field_ids": [
                "identifier",
                "announced_on",
                "acquiree_identifier",
                "acquirer_identifier",
                "price",
                "acquisition_type",
            ],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "acquiree_location",
                    "operator_id": "includes",
                    "values": ["Japan"],
                },
                {
                    "type": "predicate",
                    "field_id": "announced_on",
                    "operator_id": "gte",
                    "values": [since_str],
                },
            ],
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "limit": 50,
        }

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("entities", [])
        except Exception as e:
            logger.error(f"Crunchbase acquisitions fetch failed: {e}")
            return []

    def _parse_funding_round(self, data: Dict[str, Any]) -> Optional[Article]:
        """資金調達ラウンドデータをパース"""
        try:
            props = data.get("properties", {})

            # 企業情報
            org = props.get("funded_organization_identifier", {})
            company_name = org.get("value", "Unknown")
            company_uuid = org.get("uuid", "")

            # 日付
            announced_on = props.get("announced_on")
            published_at = None
            if announced_on:
                published_at = datetime.strptime(announced_on, "%Y-%m-%d")

            # 金額
            money_raised = props.get("money_raised", {})
            amount_usd = money_raised.get("value")
            currency = money_raised.get("currency", "USD")

            amount_display = ""
            amount_jpy = None
            if amount_usd:
                # USD to JPY 概算 (150円/ドル)
                amount_jpy = float(amount_usd) * 150
                if amount_jpy >= 100_000_000:
                    amount_display = f"約{amount_jpy / 100_000_000:.1f}億円"
                else:
                    amount_display = f"約{amount_jpy / 10_000:.0f}万円"

            # ラウンド
            investment_type = props.get("investment_type", "unknown")
            funding_round = self.ROUND_MAPPING.get(
                investment_type.lower(), FundingRound.UNKNOWN
            )

            # 投資家
            investors = props.get("investor_identifiers", [])
            investor_names = [inv.get("value", "") for inv in investors if inv.get("value")]

            # タイトル生成
            title = f"{company_name}が{amount_display}を調達"
            if investment_type and investment_type != "unknown":
                title += f"（{investment_type.replace('_', ' ').title()}）"

            url = f"https://www.crunchbase.com/funding_round/{data.get('uuid', '')}"

            return Article(
                source=self.source_name,
                source_url=url,
                title=title,
                published_at=published_at,
                company_name_en=company_name,
                deal_type=DealType.FUNDING,
                funding_round=funding_round,
                amount_jpy=amount_jpy,
                amount_original=f"${amount_usd:,.0f}" if amount_usd else None,
                investors=investor_names if investor_names else None,
            )

        except Exception as e:
            logger.error(f"Error parsing Crunchbase funding round: {e}")
            return None

    def _parse_acquisition(self, data: Dict[str, Any]) -> Optional[Article]:
        """M&Aデータをパース"""
        try:
            props = data.get("properties", {})

            # 被買収企業
            acquiree = props.get("acquiree_identifier", {})
            target_name = acquiree.get("value", "Unknown")

            # 買収企業
            acquirer = props.get("acquirer_identifier", {})
            acquirer_name = acquirer.get("value", "Unknown")

            # 日付
            announced_on = props.get("announced_on")
            published_at = None
            if announced_on:
                published_at = datetime.strptime(announced_on, "%Y-%m-%d")

            # 金額
            price = props.get("price", {})
            price_usd = price.get("value")

            amount_display = ""
            amount_jpy = None
            if price_usd:
                amount_jpy = float(price_usd) * 150
                if amount_jpy >= 100_000_000:
                    amount_display = f"（約{amount_jpy / 100_000_000:.1f}億円）"
                else:
                    amount_display = f"（約{amount_jpy / 10_000:.0f}万円）"

            # タイトル生成
            title = f"{acquirer_name}が{target_name}を買収{amount_display}"

            url = f"https://www.crunchbase.com/acquisition/{data.get('uuid', '')}"

            return Article(
                source=self.source_name,
                source_url=url,
                title=title,
                published_at=published_at,
                company_name_en=target_name,
                deal_type=DealType.MA,
                amount_jpy=amount_jpy,
                amount_original=f"${price_usd:,.0f}" if price_usd else None,
                acquirer=acquirer_name,
            )

        except Exception as e:
            logger.error(f"Error parsing Crunchbase acquisition: {e}")
            return None
