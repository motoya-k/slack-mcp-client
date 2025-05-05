FROM python:3.9-slim

WORKDIR /app

# 開発用パッケージのインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 開発用の追加パッケージ
RUN pip install --no-cache-dir \
    pytest-watch \
    ipython \
    black \
    flake8 \
    mypy

# ログディレクトリの作成
RUN mkdir -p logs

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBUG=true

# ポートの公開
EXPOSE 8000

# 開発サーバーの実行
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
