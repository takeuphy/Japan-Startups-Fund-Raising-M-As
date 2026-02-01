"""
要約サービス
Claude APIを使用して記事を要約・構造化
"""

import json
import logging
import re
from typing import List, Optional

from anthropic import Anthropic

from src.models import Article, ArticleDB, DealType, FundingRound, DealSummary

logger = logging.getLogger(__name__)


class SummarizerService:
    """Claude APIを使用した要約サービス"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def summarize_article(self, article: Article) -> Optional[DealSummary]:
        """単一記事を要約・構造化"""
        prompt = self._build_extraction_prompt(article)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text
            return self._parse_response(content, article)

        except Exception as e:
            logger.error(f"Summarization failed for {article.source_url}: {e}")
            return None

    def summarize_batch(self, articles: List[Article]) -> List[DealSummary]:
        """複数記事をバッチで要約"""
        summaries = []

        for article in articles:
            summary = self.summarize_article(article)
            if summary:
                summaries.append(summary)

        logger.info(f"Summarized {len(summaries)}/{len(articles)} articles")
        return summaries

    def _build_extraction_prompt(self, article: Article) -> str:
        """情報抽出用プロンプトを構築"""
        return f"""以下の記事から資金調達またはM&A情報を抽出し、JSON形式で出力してください。

## 記事情報
タイトル: {article.title}
ソース: {article.source}
URL: {article.source_url}
本文: {article.content_raw or '(本文なし)'}

## 出力形式
以下のJSON形式で出力してください。該当しない項目はnullとしてください。

```json
{{
  "company_name_ja": "企業名（日本語）",
  "company_name_en": "Company Name (English)",
  "deal_type": "funding または ma または ipo",
  "funding_round": "pre_seed/seed/series_a/series_b/series_c/series_d/series_e_plus/debt/grant/unknown のいずれか",
  "amount_display": "10億円 など読みやすい形式",
  "investors_display": "投資家A、投資家B、投資家C",
  "acquirer": "買収者名（M&Aの場合）",
  "industry": "業界・セクター",
  "summary": "2-3文の簡潔な要約（日本語）"
}}
```

JSONのみを出力してください。"""

    def _parse_response(
        self, content: str, original_article: Article
    ) -> Optional[DealSummary]:
        """APIレスポンスをパース"""
        try:
            # JSONブロックを抽出
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # コードブロックなしの場合
                json_str = content.strip()

            data = json.loads(json_str)

            # DealTypeのマッピング
            deal_type_str = data.get("deal_type", "unknown")
            deal_type_map = {
                "funding": DealType.FUNDING,
                "ma": DealType.MA,
                "ipo": DealType.IPO,
            }
            deal_type = deal_type_map.get(deal_type_str, DealType.UNKNOWN)

            # FundingRoundのマッピング
            round_str = data.get("funding_round", "unknown")
            round_map = {
                "pre_seed": FundingRound.PRE_SEED,
                "seed": FundingRound.SEED,
                "series_a": FundingRound.SERIES_A,
                "series_b": FundingRound.SERIES_B,
                "series_c": FundingRound.SERIES_C,
                "series_d": FundingRound.SERIES_D,
                "series_e_plus": FundingRound.SERIES_E_PLUS,
                "debt": FundingRound.DEBT,
                "grant": FundingRound.GRANT,
            }
            funding_round = round_map.get(round_str, FundingRound.UNKNOWN)

            return DealSummary(
                company_name_ja=data.get("company_name_ja")
                or original_article.company_name_ja
                or "不明",
                company_name_en=data.get("company_name_en")
                or original_article.company_name_en,
                deal_type=deal_type,
                funding_round=funding_round if deal_type == DealType.FUNDING else None,
                amount_display=data.get("amount_display") or "非公開",
                investors_display=data.get("investors_display") or data.get("acquirer") or "非公開",
                industry=data.get("industry") or "不明",
                summary=data.get("summary") or original_article.title,
                source=original_article.source,
                source_url=original_article.source_url,
                published_at=original_article.published_at,
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse summarization response: {e}")
            return None

    def classify_relevance(self, article: Article) -> bool:
        """記事が資金調達/M&A関連かを判定"""
        keywords = [
            "資金調達",
            "調達",
            "出資",
            "投資",
            "シリーズ",
            "ラウンド",
            "買収",
            "合併",
            "M&A",
            "上場",
            "IPO",
            "funding",
            "investment",
            "acquisition",
            "merger",
        ]

        text = f"{article.title} {article.content_raw or ''}"
        return any(kw.lower() in text.lower() for kw in keywords)
