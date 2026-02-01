"""
メール送信サービス
Resend APIを使用した日次ダイジェスト配信
"""

import logging
from typing import List, Optional
from datetime import datetime

import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models import DealSummary, DealType

logger = logging.getLogger(__name__)


class EmailService:
    """メール配信サービス"""

    def __init__(
        self,
        api_key: str,
        from_email: str,
        template_dir: str = "templates",
    ):
        resend.api_key = api_key
        self.from_email = from_email

        # Jinja2テンプレート環境
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def send_daily_digest(
        self,
        to_emails: List[str],
        summaries: List[DealSummary],
        date: Optional[datetime] = None,
    ) -> bool:
        """日次ダイジェストを送信"""
        if not summaries:
            logger.info("No summaries to send, skipping email")
            return True

        if date is None:
            date = datetime.now()

        # 記事を種類別に分類
        funding_deals = [s for s in summaries if s.deal_type == DealType.FUNDING]
        ma_deals = [s for s in summaries if s.deal_type == DealType.MA]
        ipo_deals = [s for s in summaries if s.deal_type == DealType.IPO]
        other_deals = [s for s in summaries if s.deal_type == DealType.UNKNOWN]

        # HTMLメール本文を生成
        html_content = self._render_digest_html(
            date=date,
            funding_deals=funding_deals,
            ma_deals=ma_deals,
            ipo_deals=ipo_deals,
            other_deals=other_deals,
            total_count=len(summaries),
        )

        # テキスト版も生成
        text_content = self._render_digest_text(
            date=date,
            summaries=summaries,
        )

        # 件名
        subject = f"【スタートアップ速報】{date.strftime('%Y年%m月%d日')} - {len(summaries)}件の資金調達・M&A情報"

        try:
            response = resend.Emails.send(
                {
                    "from": self.from_email,
                    "to": to_emails,
                    "subject": subject,
                    "html": html_content,
                    "text": text_content,
                }
            )
            logger.info(f"Email sent successfully: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _render_digest_html(
        self,
        date: datetime,
        funding_deals: List[DealSummary],
        ma_deals: List[DealSummary],
        ipo_deals: List[DealSummary],
        other_deals: List[DealSummary],
        total_count: int,
    ) -> str:
        """HTMLダイジェストをレンダリング"""
        try:
            template = self.jinja_env.get_template("digest_email.html")
            return template.render(
                date=date,
                funding_deals=funding_deals,
                ma_deals=ma_deals,
                ipo_deals=ipo_deals,
                other_deals=other_deals,
                total_count=total_count,
            )
        except Exception as e:
            logger.warning(f"Template rendering failed, using fallback: {e}")
            return self._fallback_html(
                date, funding_deals, ma_deals, ipo_deals, other_deals
            )

    def _fallback_html(
        self,
        date: datetime,
        funding_deals: List[DealSummary],
        ma_deals: List[DealSummary],
        ipo_deals: List[DealSummary],
        other_deals: List[DealSummary],
    ) -> str:
        """フォールバックHTML生成"""
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        h2 {{ color: #34a853; margin-top: 30px; }}
        .deal {{ background: #f8f9fa; border-left: 4px solid #1a73e8; padding: 15px; margin: 15px 0; }}
        .deal-funding {{ border-left-color: #34a853; }}
        .deal-ma {{ border-left-color: #ea4335; }}
        .deal-ipo {{ border-left-color: #fbbc04; }}
        .company {{ font-size: 1.1em; font-weight: bold; color: #1a73e8; }}
        .amount {{ color: #34a853; font-weight: bold; }}
        .meta {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
        a {{ color: #1a73e8; }}
    </style>
</head>
<body>
    <h1>スタートアップ資金調達・M&A速報</h1>
    <p>{date.strftime('%Y年%m月%d日')}の情報をお届けします。</p>
"""

        if funding_deals:
            html += "<h2>資金調達</h2>"
            for deal in funding_deals:
                html += self._deal_html(deal, "funding")

        if ma_deals:
            html += "<h2>M&A</h2>"
            for deal in ma_deals:
                html += self._deal_html(deal, "ma")

        if ipo_deals:
            html += "<h2>IPO / 上場</h2>"
            for deal in ipo_deals:
                html += self._deal_html(deal, "ipo")

        if other_deals:
            html += "<h2>その他</h2>"
            for deal in other_deals:
                html += self._deal_html(deal, "other")

        html += """
    <hr>
    <p style="color: #666; font-size: 0.85em;">
        このメールは Japan Startups Fund Raising & M&A Digest より自動配信されています。
    </p>
</body>
</html>
"""
        return html

    def _deal_html(self, deal: DealSummary, deal_class: str) -> str:
        """個別ディールのHTML"""
        round_display = ""
        if deal.funding_round and deal.funding_round.value != "unknown":
            round_display = f" ({deal.funding_round.value.replace('_', ' ').title()})"

        return f"""
    <div class="deal deal-{deal_class}">
        <div class="company">{deal.company_name_ja}</div>
        {f'<div style="color: #666;">({deal.company_name_en})</div>' if deal.company_name_en else ''}
        <div class="amount">{deal.amount_display}{round_display}</div>
        <div>{deal.investors_display}</div>
        <div style="margin-top: 8px;">{deal.summary}</div>
        <div class="meta">
            業界: {deal.industry} |
            ソース: <a href="{deal.source_url}">{deal.source}</a>
            {f' | {deal.published_at.strftime("%Y/%m/%d")}' if deal.published_at else ''}
        </div>
    </div>
"""

    def _render_digest_text(
        self, date: datetime, summaries: List[DealSummary]
    ) -> str:
        """テキスト版ダイジェストを生成"""
        lines = [
            f"スタートアップ資金調達・M&A速報",
            f"{date.strftime('%Y年%m月%d日')}",
            "=" * 50,
            "",
        ]

        for i, deal in enumerate(summaries, 1):
            lines.append(f"【{i}】{deal.company_name_ja}")
            if deal.company_name_en:
                lines.append(f"    ({deal.company_name_en})")
            lines.append(f"    金額: {deal.amount_display}")
            lines.append(f"    {deal.investors_display}")
            lines.append(f"    {deal.summary}")
            lines.append(f"    業界: {deal.industry}")
            lines.append(f"    ソース: {deal.source}")
            lines.append(f"    URL: {deal.source_url}")
            lines.append("")

        lines.append("-" * 50)
        lines.append("Japan Startups Fund Raising & M&A Digest")

        return "\n".join(lines)
