# Slack MCPクライアント アーキテクチャ設計書

## 1. システム概要

このシステムは、Slackからのイベントを受け取り、fast-agentを利用して処理し、MCPプロトコルを通じて外部サービス（PostgreSQL、Gmail、Notion）と連携するクライアントです。AWS Fargate上でコンテナとして実行され、スケーラビリティと管理の容易さを実現します。

## 2. 全体アーキテクチャ

```mermaid
graph TD
    A[Slack] -->|イベント| B[AWS Application Load Balancer]
    B --> C[AWS Fargate]
    
    subgraph "Fargate Container"
        D[Slack Event Handler] -->|イベント処理| E[fast-agent]
        E -->|タスク実行| F[MCP Client]
        F -->|MCP Protocol| G1[PostgreSQL MCP]
        F -->|MCP Protocol| G2[Gmail MCP]
        F -->|MCP Protocol| G3[Notion MCP]
    end
    
    H[AWS Secrets Manager] -->|認証情報| F
    I[AWS CloudWatch] -->|モニタリング/ロギング| C
    
    J[GitHub] -->|CI/CD| K[GitHub Actions]
    K -->|デプロイ| L[AWS ECR]
    L -->|イメージ| C
```

## 3. コンポーネント詳細

### 3.1 Slack Event Handler

```mermaid
classDiagram
    class SlackEventHandler {
        +handle_event(event_data)
        -validate_request(request)
        -process_command(command, user, channel)
        -send_response(response, channel)
    }
    
    class SlackClient {
        +post_message(channel, text)
        +update_message(channel, ts, text)
        +get_user_info(user_id)
    }
    
    SlackEventHandler --> SlackClient : uses
```

- Slackからのイベント（メッセージ、アクション等）を受け取る
- イベントの検証と前処理を行う
- コマンドやアクションを識別し、適切な処理にルーティング
- Slack APIを使用して応答を送信

### 3.2 fast-agent統合

```mermaid
classDiagram
    class FastAgentIntegration {
        +process_event(event_data)
        +execute_task(task_data)
        -handle_response(response)
    }
    
    class EventProcessor {
        +register_handler(event_type, handler)
        +process(event)
    }
    
    class TaskExecutor {
        +execute(task)
        +cancel(task_id)
        +get_status(task_id)
    }
    
    FastAgentIntegration --> EventProcessor : uses
    FastAgentIntegration --> TaskExecutor : uses
```

- fast-agentのイベント処理機能を活用
- イベントに基づいてタスクを定義・実行
- 非同期処理とタスク管理
- エラーハンドリングとリトライ機構

### 3.3 MCPクライアント

```mermaid
classDiagram
    class MCPClient {
        +connect(service_type)
        +execute_operation(service, operation, params)
        +get_resource(service, resource_id)
        -handle_error(error)
    }
    
    class ServiceConnector {
        +connect()
        +disconnect()
        +is_connected()
    }
    
    class PostgreSQLConnector {
        +execute_query(query, params)
        +get_data(table, conditions)
    }
    
    class GmailConnector {
        +send_email(to, subject, body)
        +get_emails(filter)
    }
    
    class NotionConnector {
        +get_page(page_id)
        +update_page(page_id, content)
        +create_page(parent_id, content)
    }
    
    MCPClient --> ServiceConnector : uses
    ServiceConnector <|-- PostgreSQLConnector
    ServiceConnector <|-- GmailConnector
    ServiceConnector <|-- NotionConnector
```

- MCPプロトコルを実装し、外部サービスと通信
- サービス固有のコネクタを管理
- 認証と認可の処理
- エラーハンドリングとリトライ機構

## 4. データフロー

```mermaid
sequenceDiagram
    participant User as Slackユーザー
    participant Slack
    participant Handler as Slack Event Handler
    participant Agent as fast-agent
    participant MCP as MCPクライアント
    participant Service as 外部サービス
    
    User->>Slack: コマンド送信
    Slack->>Handler: イベント通知
    Handler->>Handler: リクエスト検証
    Handler->>Agent: イベント処理
    Agent->>Agent: タスク定義
    Agent->>MCP: サービス操作リクエスト
    MCP->>Service: MCPプロトコルでリクエスト
    Service->>MCP: レスポンス
    MCP->>Agent: 結果返却
    Agent->>Handler: 処理結果
    Handler->>Slack: メッセージ送信
    Slack->>User: 結果表示
```

## 5. デプロイアーキテクチャ

```mermaid
graph TD
    A[開発者] -->|コード変更| B[GitHub Repository]
    B -->|トリガー| C[GitHub Actions]
    
    subgraph "CI/CD Pipeline"
        C -->|ビルド| D[Docker Build]
        D -->|テスト| E[Unit/Integration Tests]
        E -->|プッシュ| F[AWS ECR]
    end
    
    F -->|デプロイ| G[AWS ECS/Fargate]
    
    H[AWS Secrets Manager] -->|シークレット| G
    I[AWS CloudWatch] -->|モニタリング| G
    
    J[AWS Application Load Balancer] -->|トラフィック| G
    K[Slack] -->|イベント| J
```

## 6. セキュリティ考慮事項

- **認証情報管理**:
  - AWS SecretsManagerを使用して、Slack APIトークン、外部サービスの認証情報を安全に管理
  - 環境変数経由での認証情報の注入を避け、SecretsManagerからの動的取得を実装

- **アクセス制御**:
  - Slackのチャンネルやユーザーロールに基づくアクセス制御
  - 特定のコマンドや機能へのアクセス制限

- **通信セキュリティ**:
  - すべての外部通信にTLS/SSLを使用
  - AWS内部通信のセキュリティ確保（VPC内での通信など）

- **入力検証**:
  - すべてのユーザー入力の厳格な検証
  - SQLインジェクションやコマンドインジェクションの防止

## 7. 開発ロードマップ

1. **フェーズ1: 基本機能実装**
   - Slack Event Handlerの実装
   - fast-agent統合の基本機能実装
   - 単一のMCPサービス（例：PostgreSQL）との連携実装
   - 基本的なコマンド処理の実装

2. **フェーズ2: 機能拡張**
   - 追加のMCPサービス（Gmail、Notion）との連携実装
   - 高度なコマンド処理とエラーハンドリングの実装
   - ユーザーインターフェースの改善

3. **フェーズ3: デプロイと運用**
   - AWS Fargateへのデプロイパイプラインの構築
   - モニタリングとロギングの設定
   - セキュリティ強化と脆弱性対策

4. **フェーズ4: 最適化と拡張**
   - パフォーマンス最適化
   - 新しいMCPサービスの追加サポート
   - ユーザーフィードバックに基づく改善

## 8. 技術スタック

- **言語**: Python
- **フレームワーク**: 
  - FastAPI（APIエンドポイント用）
  - fast-agent（イベント処理用）
- **コンテナ化**: Docker
- **クラウドサービス**: 
  - AWS Fargate
  - AWS ECR
  - AWS Secrets Manager
  - AWS CloudWatch
- **CI/CD**: GitHub Actions
- **外部サービス連携**:
  - PostgreSQL MCP
  - Gmail MCP
  - Notion MCP
