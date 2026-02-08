FROM python:3.12-slim

WORKDIR /app

# 依存パッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY src/ src/

# 非rootユーザーで実行
RUN useradd --create-home appuser
USER appuser

CMD ["python", "-m", "src.main"]
