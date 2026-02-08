# 日経ニュース Discord 配信ボット

日本経済新聞の最新ニュースを自動で取得し、Discord に配信するボットです。

## 配信カテゴリ

| カテゴリ | 内容 |
|---|---|
| ビジネス | 企業・経営・業績・決算 |
| 株式・マーケット | 株式市場・為替・債券・投資 |
| 不動産 | 不動産・住宅・地価・REIT |
| 世界情勢 | 国際ニュース・外交・貿易 |
| 日本の政策 | 政府・国会・法案・税制 |

## 配信スケジュール

毎日 **6:30** / **12:00** / **18:00** (日本時間) に自動配信

## Google Cloud Run へのデプロイ (推奨)

### 前提条件

- Google Cloud アカウント (無料枠で運用可能)
- `gcloud` CLI インストール済み

### 手順

#### 1. Discord Webhook URL を取得

1. Discord サーバーの **サーバー設定** > **連携サービス** > **ウェブフック** を開く
2. **新しいウェブフック** をクリック
3. 名前とチャンネルを設定
4. **ウェブフックURLをコピー** をクリック

#### 2. GCP プロジェクトを準備

```bash
# GCP にログイン
gcloud auth login

# プロジェクト作成 (初回のみ)
gcloud projects create my-nikkei-bot --name="Nikkei News Bot"
gcloud config set project my-nikkei-bot

# 必要な API を有効化
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  artifactregistry.googleapis.com
```

#### 3. デプロイ

```bash
# 環境変数を設定してデプロイスクリプトを実行
export GCP_PROJECT_ID=my-nikkei-bot
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy

./deploy.sh
```

これだけで完了です。Cloud Scheduler が毎日 6:30 / 12:00 / 18:00 (JST) に自動実行します。

#### 4. テスト実行 (手動)

```bash
gcloud run jobs execute nikkei-news-bot --region=asia-northeast1
```

### 運用コスト

Cloud Run Jobs の無料枠内で運用できます:
- 1日3回 x 数秒の実行 = 月間の無料枠 (月240,000 vCPU秒) のごくわずか
- Cloud Scheduler: 月3ジョブ無料

## ローカルで実行する場合

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数を設定して実行
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy
python -m src.main
```

Docker の場合:
```bash
cp .env.example .env
# .env を編集して DISCORD_WEBHOOK_URL を設定
docker compose up
```

## 環境変数

| 変数 | 説明 | デフォルト |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL (必須) | - |
| `MAX_ARTICLES_PER_CATEGORY` | カテゴリ毎の最大記事数 | 5 |
| `LOG_LEVEL` | ログレベル | INFO |

## アーキテクチャ

```
src/
├── main.py            # エントリポイント (実行して終了)
├── config.py          # 設定管理
├── scraper.py         # RSS/スクレイピングによるニュース取得
└── discord_sender.py  # Discord Webhook 送信
deploy.sh              # GCP デプロイスクリプト
```

- **ニュース取得**: RSS愛好会提供の日経フィード + キーワードフィルタリング
- **補完**: RSS で不足分は日経サイトをスクレイピング
- **スケジューリング**: GCP Cloud Scheduler → Cloud Run Jobs
