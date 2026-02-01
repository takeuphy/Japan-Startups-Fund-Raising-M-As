# CLAUDE.md - AI Assistant Guidelines

This document provides guidance for AI assistants working with this repository.

## Project Overview

**Repository**: Japan-Startups-Fund-Raising-M-As
**Purpose**: Analysis of Japanese startup fund-raising activities and mergers & acquisitions (M&A) data

This project focuses on collecting, analyzing, and visualizing data related to:
- Japanese startup funding rounds and investment trends
- Mergers and acquisitions involving Japanese startups
- Investor patterns and deal flow analysis
- Market insights for the Japanese startup ecosystem

## Repository Structure

```
Japan-Startups-Fund-Raising-M-As/
├── CLAUDE.md           # This file - AI assistant guidelines
├── README.md           # Project documentation (to be created)
├── data/               # Data files (CSV, JSON, etc.)
│   ├── raw/            # Original unprocessed data
│   └── processed/      # Cleaned and transformed data
├── src/                # Source code
│   ├── analysis/       # Analysis scripts
│   ├── scrapers/       # Data collection scripts
│   └── utils/          # Utility functions
├── notebooks/          # Jupyter notebooks for exploration
├── tests/              # Test files
├── docs/               # Additional documentation
└── output/             # Generated reports and visualizations
```

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8 conventions
  - Use 4 spaces for indentation
  - Maximum line length: 88 characters (Black formatter compatible)
  - Use type hints for function signatures
  - Write docstrings for all public functions and classes

- **Data Files**:
  - Use UTF-8 encoding for all text files
  - CSV files should include headers
  - JSON files should be properly formatted
  - Date format: ISO 8601 (YYYY-MM-DD)
  - Currency: JPY (Japanese Yen) as default, with explicit notation when using other currencies

### Naming Conventions

- **Files**: Use snake_case for Python files and data files
  - Example: `startup_funding_analysis.py`, `ma_deals_2024.csv`
- **Variables**: Use snake_case
- **Classes**: Use PascalCase
- **Constants**: Use UPPER_SNAKE_CASE
- **Data columns**: Use snake_case with descriptive names
  - Example: `company_name`, `funding_amount_jpy`, `deal_date`

### Japanese Language Handling

- Store Japanese text in UTF-8 encoding
- Maintain both Japanese original names and romanized versions where applicable
- Use ISO 3166-1 codes for country references (JP for Japan)
- Prefecture names should be stored in both kanji and romaji

### Data Integrity

- Always preserve original data in `data/raw/`
- Document all data transformations
- Include data sources and collection dates in metadata
- Handle missing values explicitly (use `None`/`null`, not empty strings)

## Git Workflow

### Branch Naming

- Feature branches: `feature/<description>`
- Bug fixes: `fix/<description>`
- Data updates: `data/<description>`
- Documentation: `docs/<description>`

### Commit Messages

Follow conventional commits format:
- `feat:` New feature or analysis
- `fix:` Bug fix
- `data:` Data updates or additions
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions or modifications
- `chore:` Maintenance tasks

Example: `feat: add quarterly funding trend analysis`

### Pull Requests

- Provide clear description of changes
- Include data source citations when adding new data
- Reference any related issues
- Ensure all tests pass before merging

## Testing

- Write tests for data processing functions
- Validate data integrity after transformations
- Test edge cases for Japanese text handling
- Use pytest as the testing framework

Run tests with:
```bash
pytest tests/
```

## Common Tasks

### Adding New Data

1. Place raw data in `data/raw/` with descriptive filename
2. Create processing script in `src/` if needed
3. Document data source, collection method, and date
4. Save processed output to `data/processed/`

### Running Analysis

```bash
# Activate virtual environment (if using)
source venv/bin/activate

# Run specific analysis
python src/analysis/<script_name>.py

# Run Jupyter notebooks
jupyter notebook notebooks/
```

### Data Sources

When working with this repository, common data sources include:
- INITIAL (Japanese startup database)
- STARTUP DB
- Japan Venture Research (JVR)
- Crunchbase (for international context)
- Press releases and company announcements

Always cite data sources and note access dates.

## Key Dependencies

Typical dependencies for this project type:
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `matplotlib` / `seaborn` - Visualization
- `requests` / `beautifulsoup4` - Web scraping
- `jupyter` - Interactive notebooks
- `pytest` - Testing

Install dependencies:
```bash
pip install -r requirements.txt
```

## AI Assistant Notes

When working on this repository:

1. **Data Privacy**: Be cautious with personal information and company-sensitive data
2. **Data Accuracy**: Verify financial figures and dates when possible
3. **Cultural Context**: Understand Japanese business terminology and practices
4. **Currency**: Default to JPY; convert and note exchange rates when comparing internationally
5. **Date Handling**: Be aware of Japanese fiscal year (April-March) vs calendar year
6. **Company Names**: Preserve original Japanese company names alongside translations

### Common Japanese Business Terms

| Term | Meaning |
|------|---------|
| 資金調達 (shikin chōtatsu) | Fund raising |
| M&A (エムアンドエー) | Mergers and Acquisitions |
| スタートアップ | Startup |
| 投資 (tōshi) | Investment |
| 上場 (jōjō) | IPO/Listing |
| 買収 (baishū) | Acquisition |
| 合併 (gappei) | Merger |

## Status

**Current State**: Repository initialized, awaiting data and analysis code.

---

*Last updated: 2026-02-01*
