from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class AuditEvent:
    """
    監査イベントを表すデータクラス
    """

    # 基本情報
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = ""
    user_id: str = ""
    resource: str = ""
    action: str = ""
    status: str = ""

    # 詳細情報
    details: Dict[str, Any] = field(default_factory=dict)

    # メタデータ
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        監査イベントを辞書として取得

        Returns:
            Dict[str, Any]: 監査イベントの辞書
        """
        result = {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "user_id": self.user_id,
            "resource": self.resource,
            "action": self.action,
            "status": self.status,
            "details": self.details,
        }

        # オプションフィールドを追加
        if self.ip_address:
            result["ip_address"] = self.ip_address

        if self.user_agent:
            result["user_agent"] = self.user_agent

        if self.session_id:
            result["session_id"] = self.session_id

        if self.request_id:
            result["request_id"] = self.request_id

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """
        辞書から監査イベントを作成

        Args:
            data: 監査イベントの辞書

        Returns:
            AuditEvent: 監査イベントオブジェクト
        """
        # タイムスタンプの変換
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        else:
            timestamp = datetime.now()

        return cls(
            timestamp=timestamp,
            event_type=data.get("event_type", ""),
            user_id=data.get("user_id", ""),
            resource=data.get("resource", ""),
            action=data.get("action", ""),
            status=data.get("status", ""),
            details=data.get("details", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
        )


# イベントタイプの定義
class EventType:
    # 認証関連
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"

    # Slack関連
    SLACK_EVENT = "slack.event"
    SLACK_COMMAND = "slack.command"
    SLACK_INTERACTION = "slack.interaction"

    # MCP関連
    MCP_OPERATION = "mcp.operation"
    MCP_RESOURCE = "mcp.resource"

    # PostgreSQL関連
    DB_QUERY = "db.query"
    DB_MODIFY = "db.modify"

    # Gmail関連
    MAIL_SEND = "mail.send"
    MAIL_READ = "mail.read"

    # Notion関連
    NOTION_READ = "notion.read"
    NOTION_WRITE = "notion.write"

    # システム関連
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG = "system.config"


# ステータスの定義
class Status:
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
