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

## セットアップ

### 1. Discord Webhook URL を取得

1. Discord サーバーの **サーバー設定** > **連携サービス** > **ウェブフック** を開く
2. **新しいウェブフック** をクリック
3. 名前とチャンネルを設定
4. **ウェブフックURLをコピー** をクリック

### 2. 環境変数を設定

```bash
cp .env.example .env
```

`.env` ファイルを編集し、`DISCORD_WEBHOOK_URL` に取得した URL を設定:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy
```

### 3A. Docker で実行 (推奨)

```bash
docker compose up -d
```

ログ確認:
```bash
docker compose logs -f
```

停止:
```bash
docker compose down
```

### 3B. 直接実行

```bash
pip install -r requirements.txt
python -m src.main
```

## オプション

### 起動時に即座に配信

```bash
python -m src.main --run-now
```

### 環境変数

| 変数 | 説明 | デフォルト |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL (必須) | - |
| `MAX_ARTICLES_PER_CATEGORY` | カテゴリ毎の最大記事数 | 5 |
| `LOG_LEVEL` | ログレベル | INFO |

## アーキテクチャ

```
src/
├── main.py            # エントリポイント、スケジューラ
├── config.py          # 設定管理
├── scraper.py         # RSS/スクレイピングによるニュース取得
└── discord_sender.py  # Discord Webhook 送信
```

- **RSS フィード**: RSS愛好会提供の非公式フィード + キーワードフィルタリング
- **スクレイピング**: RSS で不足分を日経サイトから補完
- **スケジューリング**: APScheduler による cron 形式スケジュール
