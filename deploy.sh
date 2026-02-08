#!/bin/bash
set -euo pipefail

# ============================================
# 日経ニュース Discord ボット - GCP デプロイスクリプト
# ============================================

# --- 設定 (必要に応じて変更) ---
PROJECT_ID="${GCP_PROJECT_ID:?環境変数 GCP_PROJECT_ID を設定してください}"
REGION="${GCP_REGION:-asia-northeast1}"
JOB_NAME="nikkei-news-bot"
IMAGE="asia-northeast1-docker.pkg.dev/${PROJECT_ID}/nikkei-news-bot/app"

# --- Discord Webhook URL チェック ---
if [ -z "${DISCORD_WEBHOOK_URL:-}" ]; then
  echo "エラー: 環境変数 DISCORD_WEBHOOK_URL を設定してください"
  echo "例: export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy"
  exit 1
fi

echo "=== GCP プロジェクト: ${PROJECT_ID} ==="
echo "=== リージョン: ${REGION} ==="

# --- 1. Artifact Registry リポジトリ作成 (初回のみ) ---
echo "[1/5] Artifact Registry リポジトリ確認..."
if ! gcloud artifacts repositories describe nikkei-news-bot \
  --project="${PROJECT_ID}" \
  --location="${REGION}" &>/dev/null; then
  echo "  リポジトリ作成中..."
  gcloud artifacts repositories create nikkei-news-bot \
    --project="${PROJECT_ID}" \
    --repository-format=docker \
    --location="${REGION}"
fi

# --- 2. Docker イメージをビルド & プッシュ ---
echo "[2/5] Docker イメージをビルド & プッシュ..."
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --tag="${IMAGE}" .

# --- 3. Cloud Run Job を作成/更新 ---
echo "[3/5] Cloud Run Job を作成/更新..."
if gcloud run jobs describe "${JOB_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" &>/dev/null; then
  gcloud run jobs update "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE}" \
    --set-env-vars="DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}" \
    --max-retries=1 \
    --task-timeout=120s
else
  gcloud run jobs create "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE}" \
    --set-env-vars="DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}" \
    --max-retries=1 \
    --task-timeout=120s
fi

# --- 4. Cloud Scheduler ジョブ作成 (3つの配信時間) ---
echo "[4/5] Cloud Scheduler ジョブを作成..."

SCHEDULES=(
  "nikkei-morning:30 6 * * *:朝刊"
  "nikkei-noon:0 12 * * *:昼刊"
  "nikkei-evening:0 18 * * *:夕刊"
)

for schedule_entry in "${SCHEDULES[@]}"; do
  IFS=':' read -r name cron label <<< "${schedule_entry}"

  if gcloud scheduler jobs describe "${name}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" &>/dev/null; then
    echo "  ${label} (${name}) 更新中..."
    gcloud scheduler jobs update http "${name}" \
      --project="${PROJECT_ID}" \
      --location="${REGION}" \
      --schedule="${cron}" \
      --time-zone="Asia/Tokyo" \
      --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
      --http-method=POST \
      --oauth-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com"
  else
    echo "  ${label} (${name}) 作成中..."
    gcloud scheduler jobs create http "${name}" \
      --project="${PROJECT_ID}" \
      --location="${REGION}" \
      --schedule="${cron}" \
      --time-zone="Asia/Tokyo" \
      --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
      --http-method=POST \
      --oauth-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com"
  fi
done

# --- 5. テスト実行 ---
echo "[5/5] テスト実行..."
echo "手動でジョブを実行するには:"
echo "  gcloud run jobs execute ${JOB_NAME} --project=${PROJECT_ID} --region=${REGION}"

echo ""
echo "=== デプロイ完了 ==="
echo "配信スケジュール (JST):"
echo "  06:30 - 朝刊"
echo "  12:00 - 昼刊"
echo "  18:00 - 夕刊"
