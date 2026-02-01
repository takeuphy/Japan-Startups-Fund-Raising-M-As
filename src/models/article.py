"""
データモデル定義
資金調達・M&A記事のスキーマ
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Boolean,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class DealType(str, Enum):
    """取引タイプ"""

    FUNDING = "funding"  # 資金調達
    MA = "ma"  # M&A
    IPO = "ipo"  # 上場
    UNKNOWN = "unknown"


class FundingRound(str, Enum):
    """資金調達ラウンド"""

    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D = "series_d"
    SERIES_E_PLUS = "series_e_plus"
    DEBT = "debt"  # デットファイナンス
    GRANT = "grant"  # 助成金
    UNKNOWN = "unknown"


class ArticleDB(Base):
    """SQLAlchemy モデル: 記事データ"""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # PR TIMES, Nikkei, etc.
    source_url = Column(String(500), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    published_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # 企業情報
    company_name_ja = Column(String(200), nullable=True)
    company_name_en = Column(String(200), nullable=True)

    # 取引情報
    deal_type = Column(String(20), nullable=True)
    funding_round = Column(String(30), nullable=True)
    amount_jpy = Column(Float, nullable=True)  # 金額（円）
    amount_original = Column(String(100), nullable=True)  # 元の表記

    # 関係者
    investors = Column(Text, nullable=True)  # JSON形式で保存
    acquirer = Column(String(200), nullable=True)  # 買収者（M&Aの場合）

    # 分類
    industry = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)

    # コンテンツ
    content_raw = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)  # AI生成の要約

    # ステータス
    is_relevant = Column(Boolean, default=True)  # 資金調達/M&A関連か
    is_summarized = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)  # メール送信済みか


class Article(BaseModel):
    """Pydantic モデル: 記事データ（バリデーション用）"""

    source: str
    source_url: str
    title: str
    published_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    company_name_ja: Optional[str] = None
    company_name_en: Optional[str] = None

    deal_type: Optional[DealType] = None
    funding_round: Optional[FundingRound] = None
    amount_jpy: Optional[float] = None
    amount_original: Optional[str] = None

    investors: Optional[List[str]] = None
    acquirer: Optional[str] = None

    industry: Optional[str] = None
    sector: Optional[str] = None

    content_raw: Optional[str] = None
    summary: Optional[str] = None

    is_relevant: bool = True
    is_summarized: bool = False
    is_sent: bool = False

    class Config:
        from_attributes = True


class DealSummary(BaseModel):
    """要約済み取引情報"""

    company_name_ja: str
    company_name_en: Optional[str] = None
    deal_type: DealType
    funding_round: Optional[FundingRound] = None
    amount_display: str  # "10億円" など
    investors_display: str  # "A社、B社、C社" など
    industry: str
    summary: str
    source: str
    source_url: str
    published_at: Optional[datetime] = None


def init_database(database_url: str) -> sessionmaker:
    """データベース初期化"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
