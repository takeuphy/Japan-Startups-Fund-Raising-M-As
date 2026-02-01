"""
アプリケーション設定
環境変数から設定を読み込み
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Database
    database_url: str = Field(default="sqlite:///data/startup_news.db")

    # Claude API (要約生成用)
    anthropic_api_key: str = Field(default="")

    # Email (Resend)
    resend_api_key: str = Field(default="")
    email_from: str = Field(default="digest@example.com")
    email_to: str = Field(default="")  # カンマ区切りで複数指定可

    # 有料サービスの認証情報
    nikkei_email: Optional[str] = Field(default=None)
    nikkei_password: Optional[str] = Field(default=None)

    crunchbase_api_key: Optional[str] = Field(default=None)

    newspicks_email: Optional[str] = Field(default=None)
    newspicks_password: Optional[str] = Field(default=None)

    # Scraping settings
    request_timeout: int = Field(default=30)
    request_delay: float = Field(default=1.0)  # リクエスト間隔（秒）
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    # Summary settings
    summary_model: str = Field(default="claude-sonnet-4-20250514")
    max_articles_per_digest: int = Field(default=50)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
