# 初心者向けセットアップガイド

このガイドでは、日本スタートアップ資金調達・M&Aダイジェストアプリを動かすための手順を、ゼロから説明します。

---

## 目次

1. [必要なアカウントの準備](#step-1-必要なアカウントの準備)
2. [GitHubでの設定](#step-2-githubでの設定)
3. [動作テスト](#step-3-動作テスト)
4. [自動配信の確認](#step-4-自動配信の確認)

---

## Step 1: 必要なアカウントの準備

以下の3つのサービスに登録し、APIキーを取得します。

### 1-1. Anthropic（Claude API）- 必須

AIによる記事要約に使用します。

1. https://console.anthropic.com/ にアクセス
2. 「Sign Up」をクリックしてアカウント作成
3. クレジットカードを登録（従量課金、月$5程度の見込み）
4. 左メニューの「API Keys」をクリック
5. 「Create Key」をクリック
6. 表示されたキー（`sk-ant-api...`で始まる文字列）をメモ帳にコピー

> ⚠️ このキーは一度しか表示されません。必ずコピーして保存してください。

### 1-2. Resend（メール配信）- 必須

日次ダイジェストのメール送信に使用します。

1. https://resend.com/ にアクセス
2. 「Start Building」または「Sign Up」をクリック
3. GitHubアカウントまたはメールで登録
4. ダッシュボードの左メニュー「API Keys」をクリック
5. 「Create API Key」をクリック
6. 名前を入力（例：`startup-digest`）し、作成
7. 表示されたキー（`re_...`で始まる文字列）をメモ帳にコピー

**送信元メールアドレスの設定**:

無料プランでは `onboarding@resend.dev` からの送信のみ可能です。
独自ドメインを使いたい場合は、Resendのドメイン設定が必要です（上級者向け）。

### 1-3. Crunchbase API（オプション）

グローバルなスタートアップデータを取得する場合に使用します。

1. https://data.crunchbase.com/ にアクセス
2. 「Get API Access」をクリック
3. アカウント作成し、APIキーを取得
4. キーをメモ帳にコピー

> 💡 Crunchbaseは有料プランが必要な場合があります。なくても動作します。

---

## Step 2: GitHubでの設定

### 2-1. GitHubアカウントの準備

すでにGitHubアカウントをお持ちの場合は、2-2へ進んでください。

1. https://github.com/ にアクセス
2. 「Sign up」をクリック
3. メールアドレス、パスワード、ユーザー名を入力
4. メール認証を完了

### 2-2. リポジトリへのアクセス

このプロジェクトのリポジトリにアクセスします：

```
https://github.com/takeuphy/Japan-Startups-Fund-Raising-M-As
```

### 2-3. Secretsの設定（APIキーの登録）

GitHubにAPIキーを安全に保存します。

1. リポジトリページで「Settings」タブをクリック
2. 左メニューの「Secrets and variables」→「Actions」をクリック
3. 「New repository secret」ボタンをクリック

以下の項目を1つずつ追加します：

| Name（名前） | Secret（値） | 説明 |
|-------------|-------------|------|
| `ANTHROPIC_API_KEY` | `sk-ant-api...` | Step 1-1で取得したキー |
| `RESEND_API_KEY` | `re_...` | Step 1-2で取得したキー |
| `EMAIL_FROM` | `onboarding@resend.dev` | 送信元アドレス |
| `EMAIL_TO` | `あなたのメールアドレス` | 受信するメールアドレス |

**追加方法**:
1. 「Name」欄に名前を入力（例：`ANTHROPIC_API_KEY`）
2. 「Secret」欄に値を貼り付け
3. 「Add secret」をクリック
4. 次の項目を追加するため、再度「New repository secret」をクリック

**オプション（お持ちの有料アカウント用）**:

| Name | Secret | 説明 |
|------|--------|------|
| `CRUNCHBASE_API_KEY` | APIキー | Crunchbase API |
| `NIKKEI_EMAIL` | メールアドレス | 日経電子版ログイン用 |
| `NIKKEI_PASSWORD` | パスワード | 日経電子版パスワード |
| `NEWSPICKS_EMAIL` | メールアドレス | NewsPicksログイン用 |
| `NEWSPICKS_PASSWORD` | パスワード | NewsPicksパスワード |

---

## Step 3: 動作テスト

設定が正しいか、手動でテスト実行します。

### 3-1. GitHub Actionsを手動実行

1. リポジトリページで「Actions」タブをクリック
2. 左側の「Daily Startup News Digest」をクリック
3. 右側の「Run workflow」ボタンをクリック
4. ドロップダウンで以下を選択：
   - **Branch**: `main`（または現在のブランチ）
   - **Execution mode**: `test-email`（まずメールテスト）
5. 緑の「Run workflow」ボタンをクリック

### 3-2. 実行結果の確認

1. 画面に表示される実行中のワークフローをクリック
2. 「run-digest」ジョブをクリック
3. 各ステップの実行状況を確認

**成功の場合**:
- すべてのステップに緑のチェックマーク ✓ が表示
- 設定したメールアドレスにテストメールが届く

**失敗の場合**:
- 赤い × マークのステップをクリックして、エラーメッセージを確認
- よくあるエラー：
  - `ANTHROPIC_API_KEY is not set` → Secretの名前が間違っている
  - `Invalid API key` → APIキーの値が間違っている
  - `Email sending failed` → Resendの設定を確認

### 3-3. フル実行テスト

テストメールが成功したら、実際のダイジェストを生成します。

1. 再度「Actions」→「Daily Startup News Digest」
2. 「Run workflow」をクリック
3. **Execution mode**: `digest` を選択
4. 「Run workflow」をクリック

成功すると、収集されたニュースの要約メールが届きます。

---

## Step 4: 自動配信の確認

### 4-1. 自動実行スケジュール

設定が完了すると、毎日自動的に実行されます：

- **実行時刻**: 日本時間 午前8:00
- **実行内容**: ニュース収集 → AI要約 → メール送信

### 4-2. 実行履歴の確認

1. リポジトリの「Actions」タブをクリック
2. 過去の実行履歴が一覧で表示されます
3. 各実行をクリックすると、詳細なログを確認できます

### 4-3. 配信停止・再開

**一時停止したい場合**:
1. 「Actions」タブ
2. 「Daily Startup News Digest」を選択
3. 右上の「...」メニュー →「Disable workflow」

**再開する場合**:
1. 同じ手順で「Enable workflow」をクリック

---

## トラブルシューティング

### Q: メールが届かない

1. 迷惑メールフォルダを確認
2. `EMAIL_TO`のSecretが正しいメールアドレスか確認
3. Resendのダッシュボードでメール送信履歴を確認

### Q: エラーで実行が失敗する

1. 「Actions」タブで失敗したワークフローをクリック
2. 赤い × のステップを展開してエラーメッセージを確認
3. Secretsの設定を再確認

### Q: ニュースが収集されない

- 一部のサイト（日経、NewsPicks）は有料アカウント情報が必要です
- PR TIMESやTechCrunch Japanは無料で収集できます

### Q: 費用が心配

- **GitHub Actions**: 無料（月2,000分まで）
- **Resend**: 無料（1日100通まで）
- **Claude API**: 従量課金（目安：1日$0.1〜0.5、月$3〜15程度）

Anthropicのダッシュボードで使用量を確認し、上限を設定することをお勧めします。

---

## 次のステップ（上級者向け）

### メールの複数宛先への配信

`EMAIL_TO`に複数のメールアドレスを設定できます：

```
user1@example.com,user2@example.com,user3@example.com
```

### 独自ドメインからのメール送信

Resendで独自ドメインを設定すると、プロフェッショナルな送信元アドレスが使えます。

1. Resendダッシュボードの「Domains」
2. 「Add Domain」で独自ドメインを追加
3. DNSレコードを設定
4. `EMAIL_FROM`のSecretを更新

---

## サポート

問題が解決しない場合：

1. GitHubの「Issues」タブで質問を投稿
2. エラーメッセージのスクリーンショットを添付すると解決が早くなります

---

*このガイドは2026年2月時点の情報です。各サービスの画面は変更される可能性があります。*
