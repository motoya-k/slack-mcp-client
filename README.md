# Slack MCPクライアント

Slackからのイベントを受け取り、fast-agentを利用して処理し、MCPプロトコルを通じて外部サービス（PostgreSQL、Gmail、Notion）と連携するクライアントです。AWS Fargate上でコンテナとして実行され、スケーラビリティと管理の容易さを実現します。

## システム概要

このシステムは以下のコンポーネントで構成されています：

1. **Slack Event Handler**: Slackからのイベントを受信し、処理します
2. **fast-agent統合**: イベント処理とタスク実行を管理します
3. **MCPクライアント**: 外部サービスとMCPプロトコルで連携します
4. **セキュリティ機能**: 認証、認可、暗号化、監査を提供します

## 前提条件

- Python 3.9以上
- Docker（開発・デプロイ用）
- AWS CLI（AWSリソース操作用）
- Slack APIアクセス用のトークンとシークレット
- 各外部サービス（PostgreSQL、Gmail、Notion）のAPIキーまたは認証情報

## セットアップ

### 開発環境のセットアップ

1. リポジトリをクローン
   ```
   git clone https://github.com/yourusername/slack-mcp-client.git
   cd slack-mcp-client
   ```

2. 仮想環境の作成と有効化
   ```
   python -m venv venv
   source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
   ```

3. 依存関係のインストール
   ```
   pip install -r requirements.txt
   ```

4. 環境変数の設定
   ```
   cp .env.example .env
   # .envファイルを編集して必要な設定を行う
   ```

5. アプリケーションの実行
   ```
   python -m src.main
   ```

### Dockerを使用したセットアップ

1. Dockerイメージのビルド
   ```
   docker build -t slack-mcp-client .
   ```

2. Dockerコンテナの実行
   ```
   docker run -p 8000:8000 --env-file .env slack-mcp-client
   ```

## 使用方法

1. Slackアプリを設定し、イベントサブスクリプションURLを設定します
   - イベントURL: `https://your-domain.com/slack/events`

2. 必要なSlackの権限スコープを設定します
   - `chat:write`
   - `commands`
   - その他必要なスコープ

3. Slackでコマンドを使用して、外部サービスと連携します
   - 例: `/mcp-query "SELECT * FROM users LIMIT 10"`

## 開発

### テストの実行

```
pytest
```

### コードスタイルチェック

```
flake8 src tests
```

### 型チェック

```
mypy src
```

## デプロイ

AWS Fargateへのデプロイは、GitHub Actionsを使用して自動化されています。
詳細は`.github/workflows/deploy.yml`を参照してください。

## ライセンス

[MIT License](LICENSE)
