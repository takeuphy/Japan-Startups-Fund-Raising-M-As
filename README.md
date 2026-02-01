# Japan Startups Fund Raising & M&A Digest

日本のスタートアップの資金調達・M&A情報を自動収集し、日次でメール配信するシステムです。

## 機能

- **自動データ収集**: 複数のニュースソースから資金調達・M&A情報を収集
- **AI要約**: Claude APIを使用して記事を構造化・要約
- **メール配信**: 日次ダイジェストをHTML形式で配信
- **スケジュール実行**: GitHub Actionsで毎日自動実行

## 対応データソース

### ニュースサイト
- PR TIMES（プレスリリース）
- TechCrunch Japan
- 日本経済新聞（有料会員対応）
- NewsPicks（有料会員対応）

### スタートアップDB
- INITIAL
- Crunchbase（API対応）

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/Japan-Startups-Fund-Raising-M-As.git
cd Japan-Startups-Fund-Raising-M-As
```

### 2. Python環境を構築

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 環境変数を設定

```bash
cp .env.example .env
# .env ファイルを編集して必要な値を設定
```

### 必要なAPIキー

| サービス | 用途 | 取得先 |
|---------|------|--------|
| Anthropic API | AI要約生成 | https://console.anthropic.com/ |
| Resend | メール配信 | https://resend.com/ |
| Crunchbase API | スタートアップDB | https://data.crunchbase.com/ |

### 4. ローカルで実行

```bash
# データ収集のみ
python -m src.main --mode collect

# メールテスト
python -m src.main --mode test-email

# フル実行（収集→要約→メール送信）
python -m src.main --mode digest
```

## GitHub Actionsでの自動実行

### 1. シークレットを設定

リポジトリの Settings > Secrets and variables > Actions で以下を設定:

| シークレット名 | 説明 |
|--------------|------|
| `ANTHROPIC_API_KEY` | Claude API キー |
| `RESEND_API_KEY` | Resend API キー |
| `EMAIL_FROM` | 送信元メールアドレス |
| `EMAIL_TO` | 送信先メールアドレス（カンマ区切りで複数可） |
| `CRUNCHBASE_API_KEY` | Crunchbase API キー（オプション） |
| `NIKKEI_EMAIL` | 日経電子版ログインメール（オプション） |
| `NIKKEI_PASSWORD` | 日経電子版パスワード（オプション） |
| `NEWSPICKS_EMAIL` | NewsPicksログインメール（オプション） |
| `NEWSPICKS_PASSWORD` | NewsPicksパスワード（オプション） |

### 2. スケジュール

デフォルトで毎日日本時間 8:00 AM に実行されます。

手動実行: Actions タブ → Daily Startup News Digest → Run workflow

## プロジェクト構成

```
Japan-Startups-Fund-Raising-M-As/
├── .github/
│   └── workflows/
│       └── daily_digest.yml    # GitHub Actions ワークフロー
├── config/
│   └── settings.py             # 設定管理
├── data/                       # データベース保存先
├── src/
│   ├── main.py                 # エントリーポイント
│   ├── models/
│   │   └── article.py          # データモデル
│   ├── scrapers/
│   │   ├── base.py             # ベーススクレイパー
│   │   ├── prtimes.py          # PR TIMES
│   │   ├── techcrunch_jp.py    # TechCrunch Japan
│   │   ├── nikkei.py           # 日経新聞
│   │   ├── newspicks.py        # NewsPicks
│   │   ├── initial_inc.py      # INITIAL
│   │   └── crunchbase.py       # Crunchbase
│   └── services/
│       ├── collector.py        # データ収集サービス
│       ├── summarizer.py       # AI要約サービス
│       └── email_sender.py     # メール送信サービス
├── templates/
│   └── digest_email.html       # メールテンプレート
├── tests/                      # テストファイル
├── .env.example                # 環境変数サンプル
├── requirements.txt            # Python依存関係
└── README.md                   # このファイル
```

## メールサンプル

配信されるダイジェストには以下の情報が含まれます:

- **企業名**（日本語・英語）
- **調達額 / 買収額**
- **投資家 / 買収者**
- **ラウンド**（シード、シリーズA等）
- **業界・セクター**
- **簡潔な要約**
- **ソースへのリンク**

## カスタマイズ

### データソースの追加

新しいスクレイパーを追加するには:

1. `src/scrapers/` に新しいファイルを作成
2. `BaseScraper` を継承したクラスを実装
3. `src/scrapers/__init__.py` でエクスポート
4. `src/services/collector.py` でスクレイパーを追加

### メールテンプレートの変更

`templates/digest_email.html` を編集してデザインをカスタマイズできます。

## ライセンス

MIT License

## 注意事項

- 各ニュースサイトの利用規約を遵守してください
- スクレイピング時は適切なレート制限を設定してください
- 有料サービスの認証情報は安全に管理してください
