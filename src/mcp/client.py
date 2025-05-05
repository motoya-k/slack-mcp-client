import logging
from typing import Dict, Any, Optional

from src.mcp.connector import ServiceConnector
from src.mcp.protocol import MCPProtocol
from src.mcp.exceptions import (
    ConnectorNotFoundException,
    ConnectionException,
    OperationException,
    ResourceException,
)

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCPクライアントクラス
    外部サービスとのMCPプロトコルによる通信を管理
    """

    def __init__(self, config):
        """
        初期化

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.connectors = {}
        self.protocol = MCPProtocol()

    def register_connector(
        self, service_type: str, connector: ServiceConnector
    ) -> None:
        """
        サービスコネクタを登録

        Args:
            service_type: サービスタイプ
            connector: サービスコネクタ
        """
        logger.info(f"Registering connector for service: {service_type}")
        self.connectors[service_type] = connector

    def connect(self, service_type: str) -> bool:
        """
        指定されたサービスに接続

        Args:
            service_type: サービスタイプ

        Returns:
            bool: 接続が成功した場合はTrue、失敗した場合はFalse

        Raises:
            ConnectorNotFoundException: コネクタが見つからない場合
        """
        if service_type not in self.connectors:
            error_msg = f"No connector registered for service: {service_type}"
            logger.error(error_msg)
            raise ConnectorNotFoundException(error_msg, service=service_type)

        try:
            logger.info(f"Connecting to service: {service_type}")
            connector = self.connectors[service_type]
            result = connector.connect()
            if result:
                logger.info(f"Successfully connected to service: {service_type}")
            else:
                logger.warning(f"Failed to connect to service: {service_type}")
            return result
        except Exception as e:
            logger.error(f"Error connecting to service {service_type}: {e}")
            raise ConnectionException(
                f"Error connecting to service {service_type}: {str(e)}"
            )

    def execute_operation(
        self, service: str, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        サービス操作を実行

        Args:
            service: サービス名
            operation: 操作名
            params: パラメータ

        Returns:
            Dict[str, Any]: 操作結果

        Raises:
            ConnectorNotFoundException: コネクタが見つからない場合
            OperationException: 操作エラー
        """
        if service not in self.connectors:
            error_msg = f"No connector registered for service: {service}"
            logger.error(error_msg)
            raise ConnectorNotFoundException(error_msg, service=service)

        connector = self.connectors[service]

        # 接続確認
        if not connector.is_connected():
            logger.info(f"Service {service} not connected, attempting to connect")
            connector.connect()

        try:
            logger.info(f"Executing operation {operation} on service {service}")
            result = connector.execute_operation(operation, params)
            logger.info(
                f"Operation {operation} executed successfully on service {service}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Error executing operation {operation} on service {service}: {e}"
            )
            raise OperationException(
                f"Error executing operation: {str(e)}",
                service=service,
                operation=operation,
                details={"params": params},
            )

    def get_resource(self, service: str, resource_id: str) -> Dict[str, Any]:
        """
        サービスリソースを取得

        Args:
            service: サービス名
            resource_id: リソースID

        Returns:
            Dict[str, Any]: リソース

        Raises:
            ConnectorNotFoundException: コネクタが見つからない場合
            ResourceException: リソース取得エラー
        """
        if service not in self.connectors:
            error_msg = f"No connector registered for service: {service}"
            logger.error(error_msg)
            raise ConnectorNotFoundException(error_msg, service=service)

        connector = self.connectors[service]

        # 接続確認
        if not connector.is_connected():
            logger.info(f"Service {service} not connected, attempting to connect")
            connector.connect()

        try:
            logger.info(f"Getting resource {resource_id} from service {service}")
            result = connector.get_resource(resource_id)
            logger.info(
                f"Resource {resource_id} retrieved successfully from service {service}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Error getting resource {resource_id} from service {service}: {e}"
            )
            raise ResourceException(
                f"Error getting resource: {str(e)}",
                service=service,
                resource_id=resource_id,
            )

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """
        エラーハンドリング

        Args:
            error: 例外

        Returns:
            Dict[str, Any]: エラーレスポンス
        """
        logger.error(f"Handling error: {error}")

        error_info = {"message": str(error), "type": error.__class__.__name__}

        # 特定の例外タイプに応じた追加情報
        if isinstance(error, OperationException):
            error_info["service"] = error.service
            error_info["operation"] = error.operation
            error_info["details"] = error.details
        elif isinstance(error, ResourceException):
            error_info["service"] = error.service
            error_info["resource_id"] = error.resource_id
            error_info["details"] = error.details
        elif isinstance(error, ConnectorNotFoundException):
            error_info["service"] = error.service

        return self.protocol.create_response("error", error=error_info)
