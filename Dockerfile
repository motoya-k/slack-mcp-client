FROM python:3.9-slim

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ログディレクトリの作成
RUN mkdir -p logs

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# ポートの公開
EXPOSE 8000

# アプリケーションの実行
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
