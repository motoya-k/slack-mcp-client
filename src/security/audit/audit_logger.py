import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.security.audit.models.audit_event import AuditEvent, EventType, Status

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    監査ログを記録するクラス
    """

    def __init__(self, config):
        """
        初期化

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.audit_log_file = config.AUDIT_LOG_FILE

        # 監査ログ用のロガーを設定
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)

        # ファイルハンドラの設定
        handler = logging.FileHandler(self.audit_log_file)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # 親ロガーからのメッセージを伝播しない
        self.logger.propagate = False

        logger.info(f"Audit logger initialized with log file: {self.audit_log_file}")

    def log_event(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        イベントをログに記録

        Args:
            event_type: イベントタイプ
            user_id: ユーザーID
            resource: リソース
            action: アクション
            status: ステータス
            details: 詳細情報（オプション）
            **kwargs: その他のメタデータ

        Returns:
            AuditEvent: 記録された監査イベント
        """
        # 監査イベントの作成
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            status=status,
            details=details or {},
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent"),
            session_id=kwargs.get("session_id"),
            request_id=kwargs.get("request_id"),
        )

        # イベントをJSONに変換
        event_json = json.dumps(event.to_dict())

        # ログに記録
        self.logger.info(event_json)

        return event

    def log_auth_event(
        self,
        user_id: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        認証イベントをログに記録

        Args:
            user_id: ユーザーID
            action: アクション（login, logout, failed）
            status: ステータス
            details: 詳細情報（オプション）
            **kwargs: その他のメタデータ

        Returns:
            AuditEvent: 記録された監査イベント
        """
        event_type = f"auth.{action}"
        return self.log_event(
            event_type, user_id, "auth", action, status, details, **kwargs
        )

    def log_slack_event(
        self,
        user_id: str,
        event_subtype: str,
        channel: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        Slackイベントをログに記録

        Args:
            user_id: ユーザーID
            event_subtype: イベントサブタイプ
            channel: チャンネル
            status: ステータス
            details: 詳細情報（オプション）
            **kwargs: その他のメタデータ

        Returns:
            AuditEvent: 記録された監査イベント
        """
        return self.log_event(
            EventType.SLACK_EVENT,
            user_id,
            f"slack:channel:{channel}",
            event_subtype,
            status,
            details,
            **kwargs,
        )

    def log_mcp_operation(
        self,
        user_id: str,
        service: str,
        operation: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        MCP操作をログに記録

        Args:
            user_id: ユーザーID
            service: サービス名
            operation: 操作名
            status: ステータス
            details: 詳細情報（オプション）
            **kwargs: その他のメタデータ

        Returns:
            AuditEvent: 記録された監査イベント
        """
        return self.log_event(
            EventType.MCP_OPERATION,
            user_id,
            f"mcp:service:{service}",
            operation,
            status,
            details,
            **kwargs,
        )

    def log_system_event(
        self,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        システムイベントをログに記録

        Args:
            action: アクション
            status: ステータス
            details: 詳細情報（オプション）
            **kwargs: その他のメタデータ

        Returns:
            AuditEvent: 記録された監査イベント
        """
        event_type = f"system.{action}"
        return self.log_event(
            event_type, "system", "system", action, status, details, **kwargs
        )

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        監査イベントを取得

        Args:
            start_time: 開始時間（オプション）
            end_time: 終了時間（オプション）
            event_type: イベントタイプ（オプション）
            user_id: ユーザーID（オプション）
            status: ステータス（オプション）
            limit: 取得する最大件数

        Returns:
            List[AuditEvent]: 監査イベントのリスト
        """
        events = []

        try:
            with open(self.audit_log_file, "r") as f:
                for line in f:
                    # タイムスタンプとJSONを分離
                    parts = line.strip().split(" - ", 1)
                    if len(parts) != 2:
                        continue

                    try:
                        # JSONをパース
                        event_data = json.loads(parts[1])
                        event = AuditEvent.from_dict(event_data)

                        # フィルタリング
                        if start_time and event.timestamp < start_time:
                            continue

                        if end_time and event.timestamp > end_time:
                            continue

                        if event_type and event.event_type != event_type:
                            continue

                        if user_id and event.user_id != user_id:
                            continue

                        if status and event.status != status:
                            continue

                        events.append(event)

                        # 最大件数に達したら終了
                        if len(events) >= limit:
                            break

                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in audit log: {parts[1]}")
                    except Exception as e:
                        logger.error(f"Error parsing audit log entry: {e}")

        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.audit_log_file}")
        except Exception as e:
            logger.error(f"Error reading audit log file: {e}")

        return events
