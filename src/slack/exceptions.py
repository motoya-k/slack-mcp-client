class SlackException(Exception):
    """Slack関連の基本例外クラス"""

    pass


class InvalidRequestException(SlackException):
    """無効なリクエストの例外"""

    pass


class AuthenticationException(SlackException):
    """認証エラーの例外"""

    pass


class RateLimitException(SlackException):
    """レート制限の例外"""

    pass


class SlackAPIException(SlackException):
    """Slack API呼び出しエラーの例外"""

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class CommandProcessingException(SlackException):
    """コマンド処理エラーの例外"""

    pass


class EventProcessingException(SlackException):
    """イベント処理エラーの例外"""

    pass
