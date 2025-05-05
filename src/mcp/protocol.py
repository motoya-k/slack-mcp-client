import json
import logging
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class MCPProtocol:
    """
    MCPプロトコルの基本実装
    """

    VERSION = "1.0"

    @staticmethod
    def create_request(
        service: str, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        リクエストメッセージを作成

        Args:
            service: サービス名
            operation: 操作名
            params: パラメータ

        Returns:
            Dict[str, Any]: リクエストメッセージ
        """
        return {
            "protocol": "mcp",
            "version": MCPProtocol.VERSION,
            "service": service,
            "operation": operation,
            "params": params,
        }

    @staticmethod
    def create_resource_request(service: str, resource_id: str) -> Dict[str, Any]:
        """
        リソースリクエストメッセージを作成

        Args:
            service: サービス名
            resource_id: リソースID

        Returns:
            Dict[str, Any]: リソースリクエストメッセージ
        """
        return {
            "protocol": "mcp",
            "version": MCPProtocol.VERSION,
            "service": service,
            "resource_id": resource_id,
        }

    @staticmethod
    def create_response(
        status: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        レスポンスメッセージを作成

        Args:
            status: ステータス（"success" または "error"）
            data: レスポンスデータ（成功時）
            error: エラー情報（エラー時）

        Returns:
            Dict[str, Any]: レスポンスメッセージ
        """
        response = {"protocol": "mcp", "version": MCPProtocol.VERSION, "status": status}

        if status == "success" and data is not None:
            response["data"] = data
        elif status == "error" and error is not None:
            response["error"] = error

        return response

    @staticmethod
    def serialize(message: Dict[str, Any]) -> str:
        """
        メッセージをシリアライズ

        Args:
            message: メッセージ辞書

        Returns:
            str: シリアライズされたメッセージ
        """
        return json.dumps(message)

    @staticmethod
    def deserialize(message_str: str) -> Dict[str, Any]:
        """
        メッセージをデシリアライズ

        Args:
            message_str: シリアライズされたメッセージ

        Returns:
            Dict[str, Any]: デシリアライズされたメッセージ

        Raises:
            ValueError: JSONデコードエラー
        """
        try:
            return json.loads(message_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize message: {e}")
            raise ValueError(f"Invalid message format: {e}")

    @staticmethod
    def validate_request(message: Dict[str, Any]) -> bool:
        """
        リクエストメッセージを検証

        Args:
            message: リクエストメッセージ

        Returns:
            bool: 有効な場合はTrue、そうでない場合はFalse
        """
        required_fields = ["protocol", "version", "service"]

        # 必須フィールドの存在確認
        for field in required_fields:
            if field not in message:
                logger.error(f"Missing required field: {field}")
                return False

        # プロトコル名の確認
        if message["protocol"] != "mcp":
            logger.error(f"Invalid protocol: {message['protocol']}")
            return False

        # バージョンの確認
        if message["version"] != MCPProtocol.VERSION:
            logger.error(f"Unsupported version: {message['version']}")
            return False

        # 操作またはリソースIDのいずれかが必要
        if "operation" not in message and "resource_id" not in message:
            logger.error("Either operation or resource_id is required")
            return False

        # 操作の場合はパラメータが必要
        if "operation" in message and "params" not in message:
            logger.error("Params are required for operation")
            return False

        return True

    @staticmethod
    def validate_response(message: Dict[str, Any]) -> bool:
        """
        レスポンスメッセージを検証

        Args:
            message: レスポンスメッセージ

        Returns:
            bool: 有効な場合はTrue、そうでない場合はFalse
        """
        required_fields = ["protocol", "version", "status"]

        # 必須フィールドの存在確認
        for field in required_fields:
            if field not in message:
                logger.error(f"Missing required field: {field}")
                return False

        # プロトコル名の確認
        if message["protocol"] != "mcp":
            logger.error(f"Invalid protocol: {message['protocol']}")
            return False

        # バージョンの確認
        if message["version"] != MCPProtocol.VERSION:
            logger.error(f"Unsupported version: {message['version']}")
            return False

        # ステータスの確認
        if message["status"] not in ["success", "error"]:
            logger.error(f"Invalid status: {message['status']}")
            return False

        # 成功の場合はデータが必要
        if message["status"] == "success" and "data" not in message:
            logger.error("Data is required for success status")
            return False

        # エラーの場合はエラー情報が必要
        if message["status"] == "error" and "error" not in message:
            logger.error("Error information is required for error status")
            return False

        return True
