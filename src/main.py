import logging
from fastapi import FastAPI, Request, HTTPException
import uvicorn

from src.config import Config
from src.logging_config import setup_logging
from src.slack.event_handler import SlackEventHandler
from src.agent.integration import FastAgentIntegration
from src.mcp.client import MCPClient
from src.security.authentication.slack_auth import SlackAuthenticator
from src.security.authentication.service_auth import ServiceAuthenticator
from src.security.secrets.secrets_manager import SecretsManager
from src.security.authorization.access_control import AccessControl
from src.security.authorization.permission import Permission
from src.security.encryption.data_encryption import DataEncryption
from src.security.encryption.key_manager import KeyManager
from src.security.audit.audit_logger import AuditLogger
from src.security.audit.models.audit_event import EventType, Status

# 設定の読み込み
config = Config()

# ロギングの設定
logger = setup_logging(config)

# セキュリティコンポーネントの初期化
secrets_manager = None
if config.AWS_SECRET_MANAGER_ENABLED:
    secrets_manager = SecretsManager(config)
    logger.info("AWS Secrets Manager enabled")

slack_authenticator = SlackAuthenticator(config)
service_authenticator = ServiceAuthenticator(config)
access_control = AccessControl()
key_manager = KeyManager(config, secrets_manager)
audit_logger = AuditLogger(config)

if secrets_manager:
    service_authenticator.set_secrets_manager(secrets_manager)

# MCPClientの初期化
mcp_client = MCPClient(config)

# FastAgentIntegrationの初期化
fast_agent = FastAgentIntegration(config)
fast_agent.initialize()
fast_agent.mcp_client = mcp_client

# SlackEventHandlerの初期化
slack_event_handler = SlackEventHandler(config)
slack_event_handler.fast_agent = fast_agent

# FastAPIアプリケーションの作成
app = FastAPI(
    title=config.APP_NAME,
    description="Slack MCPクライアント - SlackイベントをMCPプロトコルで外部サービスと連携",
    version="0.1.0",
    debug=config.DEBUG,
)


@app.get("/")
async def root():
    """
    ルートエンドポイント - ヘルスチェック用
    """
    return {"status": "ok", "service": config.APP_NAME}


@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "healthy"}


@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Slackイベント受信エンドポイント
    """
    try:
        # リクエストボディの取得
        body = await request.body()

        # Slack認証の検証
        if not slack_authenticator.verify_request(request.headers, body):
            logger.warning("Invalid Slack request signature")
            # 監査ログに記録
            audit_logger.log_auth_event(
                user_id="unknown",
                action="verification",
                status=Status.FAILURE,
                details={"reason": "Invalid signature"},
            )
            raise HTTPException(status_code=401, detail="Invalid request signature")

        # イベントデータの解析（アクセス制御のために必要）
        event_data = await request.json()

        # イベントコールバックの場合、ユーザーのアクセス権を確認
        if event_data.get("type") == "event_callback":
            event = event_data.get("event", {})
            user_id = event.get("user")
            channel_id = event.get("channel")
            event_type = event.get("type")

            # 監査ログに記録
            if user_id and channel_id:
                audit_logger.log_slack_event(
                    user_id=user_id,
                    event_subtype=event_type,
                    channel=channel_id,
                    status=Status.INFO,
                    details={"event_data": event_data},
                )

                # ユーザーIDとチャンネルIDが存在する場合、アクセス権を確認
                # 現時点では全てのユーザーにアクセスを許可
                # 実際の実装では、以下のようにアクセス制御を行う
                # if not access_control.can_access_channel(user_id, channel_id):
                #     logger.warning(f"Access denied for user {user_id} to channel {channel_id}")
                #     audit_logger.log_slack_event(
                #         user_id=user_id,
                #         event_subtype=event_type,
                #         channel=channel_id,
                #         status=Status.FAILURE,
                #         details={"reason": "Access denied"}
                #     )
                #     raise HTTPException(status_code=403, detail="Access denied")

        result = await slack_event_handler.handle_event(request)

        # 成功を監査ログに記録
        if event_data.get("type") == "event_callback":
            event = event_data.get("event", {})
            user_id = event.get("user", "unknown")
            channel_id = event.get("channel", "unknown")
            event_type = event.get("type", "unknown")

            audit_logger.log_slack_event(
                user_id=user_id,
                event_subtype=event_type,
                channel=channel_id,
                status=Status.SUCCESS,
                details={"response": result},
            )

        return result
    except HTTPException as e:
        # HTTPExceptionはそのまま再送出
        raise e
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")

        # エラーを監査ログに記録
        audit_logger.log_system_event(
            action="error",
            status=Status.ERROR,
            details={"error": str(e), "location": "slack_events"},
        )

        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {config.APP_NAME}")

    # システム起動を監査ログに記録
    audit_logger.log_system_event(
        action="start",
        status=Status.INFO,
        details={"app_name": config.APP_NAME, "version": "0.1.0"},
    )

    # FastAgentの初期化
    if not fast_agent.initialize():
        logger.error("Failed to initialize FastAgent")
        audit_logger.log_system_event(
            action="initialize",
            status=Status.FAILURE,
            details={"component": "FastAgent", "reason": "Initialization failed"},
        )
    else:
        logger.info("FastAgent initialized successfully")
        audit_logger.log_system_event(
            action="initialize",
            status=Status.SUCCESS,
            details={"component": "FastAgent"},
        )

    # サービス認証情報の読み込み
    for service_type in ["postgresql", "gmail", "notion"]:
        if service_authenticator.load_credentials(service_type):
            logger.info(f"Credentials for {service_type} loaded successfully")

            # 認証情報の機密データを復号化
            credentials = service_authenticator.get_credentials(service_type)
            if credentials:
                decrypted_credentials = key_manager.decrypt_sensitive_data(credentials)
                service_authenticator.update_credentials(
                    service_type, decrypted_credentials
                )
        else:
            logger.warning(f"Failed to load credentials for {service_type}")

    # デフォルトのアクセス制御設定
    # 実際の実装では、データベースやファイルから読み込む
    logger.info("Setting up default access control")

    # 管理者ユーザーの設定
    admin_users = ["U12345678"]  # 管理者ユーザーIDのリスト
    for user_id in admin_users:
        access_control.assign_role_to_user(user_id, "admin")
        logger.info(f"Assigned admin role to user {user_id}")

    # 一般ユーザーの設定
    # 実際の実装では、Slackワークスペースから全ユーザーを取得して設定

    # ここで必要に応じてMCPコネクタを登録
    # 例: PostgreSQLコネクタの登録
    # from src.mcp.connectors.postgresql.connector import PostgreSQLConnector
    # postgres_credentials = service_authenticator.get_credentials("postgresql")
    # if postgres_credentials:
    #     postgres_connector = PostgreSQLConnector(config, postgres_credentials)
    #     mcp_client.register_connector("postgresql", postgres_connector)


# アプリケーション終了時の処理
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {config.APP_NAME}")

    # システム終了を監査ログに記録
    audit_logger.log_system_event(
        action="stop", status=Status.INFO, details={"app_name": config.APP_NAME}
    )

    # 各種リソースのクリーンアップ
    for service_type, connector in mcp_client.connectors.items():
        try:
            logger.info(f"Disconnecting from service: {service_type}")
            connector.disconnect()
            audit_logger.log_system_event(
                action="disconnect",
                status=Status.SUCCESS,
                details={"service": service_type},
            )
        except Exception as e:
            logger.error(f"Error disconnecting from service {service_type}: {e}")
            audit_logger.log_system_event(
                action="disconnect",
                status=Status.ERROR,
                details={"service": service_type, "error": str(e)},
            )


if __name__ == "__main__":
    # 開発サーバーの起動
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=config.DEBUG)
