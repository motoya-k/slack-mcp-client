import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.mcp.exceptions import (
    ConnectionException,
    OperationException,
    ResourceException,
)

logger = logging.getLogger(__name__)


class ServiceConnector(ABC):
    """
    MCPサービスコネクタの抽象基底クラス
    すべてのサービス固有のコネクタはこのクラスを継承する必要があります
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        サービスに接続

        Returns:
            bool: 接続が成功した場合はTrue、失敗した場合はFalse

        Raises:
            ConnectionException: 接続エラー
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        サービスから切断
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        接続状態を確認

        Returns:
            bool: 接続されている場合はTrue、そうでない場合はFalse
        """
        pass

    def execute_operation(
        self, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        操作を実行

        Args:
            operation: 操作名
            params: パラメータ

        Returns:
            Dict[str, Any]: 操作結果

        Raises:
            OperationException: 操作エラー
        """
        if not self.is_connected():
            logger.info("Not connected, attempting to connect")
            self.connect()

        method_name = f"op_{operation}"
        if not hasattr(self, method_name):
            error_msg = f"Operation not supported: {operation}"
            logger.error(error_msg)
            raise OperationException(error_msg, operation=operation)

        try:
            logger.info(f"Executing operation: {operation}")
            method = getattr(self, method_name)
            result = method(params)
            logger.info(f"Operation {operation} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing operation {operation}: {e}")
            raise OperationException(
                f"Error executing operation: {str(e)}",
                operation=operation,
                details={"params": params},
            )

    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """
        リソースを取得

        Args:
            resource_id: リソースID

        Returns:
            Dict[str, Any]: リソース

        Raises:
            ResourceException: リソース取得エラー
        """
        if not self.is_connected():
            logger.info("Not connected, attempting to connect")
            self.connect()

        try:
            logger.info(f"Getting resource: {resource_id}")
            # リソースIDのパターンに基づいて適切なメソッドを呼び出す
            # 例: "users/123" -> get_user(123)
            parts = resource_id.split("/")

            if len(parts) < 2:
                error_msg = f"Invalid resource ID format: {resource_id}"
                logger.error(error_msg)
                raise ResourceException(error_msg, resource_id=resource_id)

            resource_type = parts[0]
            resource_key = "/".join(parts[1:])

            method_name = f"get_{resource_type}"
            if not hasattr(self, method_name):
                error_msg = f"Resource type not supported: {resource_type}"
                logger.error(error_msg)
                raise ResourceException(error_msg, resource_id=resource_id)

            method = getattr(self, method_name)
            result = method(resource_key)
            logger.info(f"Resource {resource_id} retrieved successfully")
            return result
        except ResourceException:
            # 既存のResourceExceptionはそのまま再送出
            raise
        except Exception as e:
            logger.error(f"Error getting resource {resource_id}: {e}")
            raise ResourceException(
                f"Error getting resource: {str(e)}", resource_id=resource_id
            )
