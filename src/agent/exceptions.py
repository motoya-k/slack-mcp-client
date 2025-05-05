class FastAgentException(Exception):
    """fast-agent関連の基本例外クラス"""

    pass


class InitializationException(FastAgentException):
    """初期化エラーの例外"""

    pass


class EventProcessingException(FastAgentException):
    """イベント処理エラーの例外"""

    pass


class TaskExecutionException(FastAgentException):
    """タスク実行エラーの例外"""

    pass


class ConnectionException(FastAgentException):
    """接続エラーの例外"""

    pass


class AuthenticationException(FastAgentException):
    """認証エラーの例外"""

    pass


class TimeoutException(FastAgentException):
    """タイムアウトエラーの例外"""

    pass


class ValidationException(FastAgentException):
    """バリデーションエラーの例外"""

    pass


class ResourceNotFoundException(FastAgentException):
    """リソース未検出エラーの例外"""

    pass


class ServiceUnavailableException(FastAgentException):
    """サービス利用不可エラーの例外"""

    pass
