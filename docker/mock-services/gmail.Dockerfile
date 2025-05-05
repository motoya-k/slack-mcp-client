FROM python:3.9-slim

WORKDIR /app

# 依存関係のインストール
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# ポートの公開
EXPOSE 8001

# アプリケーションの実行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
