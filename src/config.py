import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # アプリケーション設定
    APP_NAME = "slack-mcp-client"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Slack設定
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

    # fast-agent設定
    FAST_AGENT_API_KEY = os.getenv("FAST_AGENT_API_KEY")
    FAST_AGENT_TIMEOUT = int(os.getenv("FAST_AGENT_TIMEOUT", "30"))

    # AWS設定
    AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
    AWS_SECRET_MANAGER_ENABLED = (
        os.getenv("AWS_SECRET_MANAGER_ENABLED", "False").lower() == "true"
    )

    # ログ設定
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")

    # PostgreSQL設定
    PG_HOST = os.getenv("PG_HOST", "localhost")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DATABASE = os.getenv("PG_DATABASE", "mcp_client")
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

    # Gmail設定
    GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE")

    # Notion設定
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
