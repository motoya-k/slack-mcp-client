class MCPException(Exception):
    """MCP関連の基本例外クラス"""

    pass


class ProtocolException(MCPException):
    """プロトコルエラーの例外"""

    pass


class ValidationException(MCPException):
    """バリデーションエラーの例外"""

    pass


class ConnectionException(MCPException):
    """接続エラーの例外"""

    pass


class AuthenticationException(MCPException):
    """認証エラーの例外"""

    pass


class OperationException(MCPException):
    """操作エラーの例外"""

    def __init__(self, message, service=None, operation=None, details=None):
        super().__init__(message)
        self.service = service
        self.operation = operation
        self.details = details or {}


class ResourceException(MCPException):
    """リソースエラーの例外"""

    def __init__(self, message, service=None, resource_id=None, details=None):
        super().__init__(message)
        self.service = service
        self.resource_id = resource_id
        self.details = details or {}


class ServiceUnavailableException(MCPException):
    """サービス利用不可エラーの例外"""

    def __init__(self, message, service=None):
        super().__init__(message)
        self.service = service


class TimeoutException(MCPException):
    """タイムアウトエラーの例外"""

    pass


class RetryableException(MCPException):
    """リトライ可能なエラーの例外"""

    pass


class ConnectorNotFoundException(MCPException):
    """コネクタ未検出エラーの例外"""

    def __init__(self, message, service=None):
        super().__init__(message)
        self.service = service
