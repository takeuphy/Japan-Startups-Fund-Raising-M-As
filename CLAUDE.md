# CLAUDE.md - AI Assistant Guidelines

This document provides guidance for AI assistants working with this repository.

## Project Overview

**Repository**: Japan-Startups-Fund-Raising-M-As
**Purpose**: Automated collection and daily digest of Japanese startup fund-raising and M&A news

This project:
- Collects news from multiple sources (PR TIMES, TechCrunch Japan, Nikkei, NewsPicks, INITIAL, Crunchbase)
- Uses Claude API to summarize and structure deal information
- Sends daily email digests via Resend
- Runs automatically via GitHub Actions

## Repository Structure

```
Japan-Startups-Fund-Raising-M-As/
├── .github/
│   └── workflows/
│       └── daily_digest.yml    # GitHub Actions (毎日 JST 8:00 実行)
├── config/
│   ├── __init__.py
│   └── settings.py             # Pydantic settings (環境変数管理)
├── data/                       # SQLite データベース保存先
├── src/
│   ├── __init__.py
│   ├── main.py                 # エントリーポイント
│   ├── models/
│   │   ├── __init__.py
│   │   └── article.py          # Article, DealSummary モデル
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseScraper 基底クラス
│   │   ├── prtimes.py          # PR TIMES スクレイパー
│   │   ├── techcrunch_jp.py    # TechCrunch Japan (RSS)
│   │   ├── nikkei.py           # 日経新聞 (有料対応)
│   │   ├── newspicks.py        # NewsPicks (有料対応)
│   │   ├── initial_inc.py      # INITIAL
│   │   └── crunchbase.py       # Crunchbase API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── collector.py        # 全スクレイパー統合
│   │   ├── summarizer.py       # Claude API 要約
│   │   └── email_sender.py     # Resend メール送信
│   └── utils/
│       └── __init__.py
├── templates/
│   └── digest_email.html       # Jinja2 メールテンプレート
├── tests/                      # pytest テスト
├── .env.example                # 環境変数サンプル
├── .gitignore
├── requirements.txt
├── README.md
└── CLAUDE.md                   # このファイル
```

## Key Files

### Entry Point
- `src/main.py` - CLI with `--mode digest|collect|test-email`

### Data Models
- `src/models/article.py` - `Article`, `ArticleDB`, `DealSummary`, `DealType`, `FundingRound`

### Core Services
- `src/services/collector.py` - `CollectorService` orchestrates all scrapers
- `src/services/summarizer.py` - `SummarizerService` uses Claude API
- `src/services/email_sender.py` - `EmailService` uses Resend API

### Configuration
- `config/settings.py` - Pydantic `Settings` class loads from `.env`

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8 conventions
  - Use 4 spaces for indentation
  - Maximum line length: 88 characters (Black formatter)
  - Use type hints for function signatures
  - Write docstrings for all public functions and classes

### Running Locally

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Run modes
python -m src.main --mode collect     # データ収集のみ
python -m src.main --mode test-email  # メールテスト
python -m src.main --mode digest      # フル実行
```

### Adding a New Scraper

1. Create `src/scrapers/new_source.py`
2. Inherit from `BaseScraper`
3. Implement `scrape(since: datetime) -> List[Article]`
4. Export in `src/scrapers/__init__.py`
5. Add to `CollectorService.__init__()` in `src/services/collector.py`

Example:
```python
class NewSourceScraper(BaseScraper):
    source_name = "New Source"
    base_url = "https://example.com"

    def scrape(self, since: Optional[datetime] = None) -> List[Article]:
        # Implementation
        pass
```

### Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Claude API key
- `RESEND_API_KEY` - Resend API key
- `EMAIL_FROM` - Sender email
- `EMAIL_TO` - Recipient email(s)

Optional:
- `CRUNCHBASE_API_KEY` - Crunchbase API key
- `NIKKEI_EMAIL`, `NIKKEI_PASSWORD` - Nikkei credentials
- `NEWSPICKS_EMAIL`, `NEWSPICKS_PASSWORD` - NewsPicks credentials

## Git Workflow

### Branch Naming

- Feature branches: `feature/<description>`
- Bug fixes: `fix/<description>`
- Documentation: `docs/<description>`

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Test additions
- `chore:` Maintenance

## Testing

```bash
pytest tests/
```

## AI Assistant Notes

### Important Considerations

1. **API Keys**: Never commit `.env` or expose API keys
2. **Rate Limiting**: Scrapers have built-in delays (`settings.request_delay`)
3. **Error Handling**: Each scraper handles errors independently
4. **Japanese Text**: All text is UTF-8 encoded

### Common Tasks

**Debug scraping issues:**
```python
from src.scrapers import PRTimesScraper
scraper = PRTimesScraper()
articles = scraper.scrape()
print(f"Found {len(articles)} articles")
```

**Test summarization:**
```python
from src.services.summarizer import SummarizerService
summarizer = SummarizerService(api_key="...")
summary = summarizer.summarize_article(article)
```

### Japanese Business Terms

| Term | Meaning |
|------|---------|
| 資金調達 | Fund raising |
| M&A | Mergers and Acquisitions |
| スタートアップ | Startup |
| 投資 | Investment |
| 上場 / IPO | IPO/Listing |
| 買収 | Acquisition |
| 合併 | Merger |
| シリーズA/B/C | Series A/B/C funding |

## Status

**Current State**: Fully implemented, ready for deployment

### Implemented Features
- [x] PR TIMES scraper
- [x] TechCrunch Japan scraper (RSS)
- [x] Nikkei scraper (partial - needs login implementation)
- [x] NewsPicks scraper (partial - needs login implementation)
- [x] INITIAL scraper
- [x] Crunchbase API client
- [x] Claude API summarization
- [x] Resend email delivery
- [x] GitHub Actions workflow
- [x] HTML email template

### TODO
- [ ] Complete Nikkei/NewsPicks login flow
- [ ] Add Pitchbook integration
- [ ] Add STARTUP DB integration
- [ ] Add unit tests
- [ ] Add error notification (Slack)

---

*Last updated: 2026-02-01*
