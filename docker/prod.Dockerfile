# ビルドステージ
FROM python:3.9-slim as builder

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 本番環境用の依存関係
RUN pip install --no-cache-dir \
    gunicorn \
    uvloop \
    httptools

# 実行ステージ
FROM python:3.9-slim

WORKDIR /app

# 必要なパッケージのみインストール
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージからPythonパッケージをコピー
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードのコピー
COPY . .

# ログディレクトリの作成
RUN mkdir -p logs

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBUG=false

# 非rootユーザーの作成と権限設定
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# ポートの公開
EXPOSE 8000

# tiniを使用してプロセス管理を改善
ENTRYPOINT ["/usr/bin/tini", "--"]

# Gunicornを使用して本番環境で実行
CMD ["gunicorn", "src.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
