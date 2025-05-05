import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.slack.exceptions import SlackAPIException, RateLimitException

logger = logging.getLogger(__name__)


class SlackClient:
    """
    Slack APIクライアントのラッパークラス
    """

    def __init__(self, token):
        """
        初期化

        Args:
            token: Slack APIトークン
        """
        self.client = WebClient(token=token)

    def post_message(self, channel, text, blocks=None, thread_ts=None):
        """
        メッセージを投稿

        Args:
            channel: 投稿先チャンネルID
            text: メッセージテキスト
            blocks: ブロックキット要素（オプション）
            thread_ts: スレッドタイムスタンプ（オプション）

        Returns:
            dict: Slack APIレスポンス

        Raises:
            SlackAPIException: API呼び出しエラー
            RateLimitException: レート制限エラー
        """
        try:
            return self.client.chat_postMessage(
                channel=channel, text=text, blocks=blocks, thread_ts=thread_ts
            )
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                logger.warning(f"Rate limit error: {e}")
                raise RateLimitException(f"Rate limited: {e}")
            else:
                logger.error(f"Error posting message: {e}")
                raise SlackAPIException(f"Failed to post message: {e}", e.response)

    def update_message(self, channel, ts, text, blocks=None):
        """
        メッセージを更新

        Args:
            channel: チャンネルID
            ts: 更新対象メッセージのタイムスタンプ
            text: 新しいメッセージテキスト
            blocks: 新しいブロックキット要素（オプション）

        Returns:
            dict: Slack APIレスポンス

        Raises:
            SlackAPIException: API呼び出しエラー
            RateLimitException: レート制限エラー
        """
        try:
            return self.client.chat_update(
                channel=channel, ts=ts, text=text, blocks=blocks
            )
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                logger.warning(f"Rate limit error: {e}")
                raise RateLimitException(f"Rate limited: {e}")
            else:
                logger.error(f"Error updating message: {e}")
                raise SlackAPIException(f"Failed to update message: {e}", e.response)

    def get_user_info(self, user_id):
        """
        ユーザー情報を取得

        Args:
            user_id: ユーザーID

        Returns:
            dict: ユーザー情報

        Raises:
            SlackAPIException: API呼び出しエラー
            RateLimitException: レート制限エラー
        """
        try:
            return self.client.users_info(user=user_id)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                logger.warning(f"Rate limit error: {e}")
                raise RateLimitException(f"Rate limited: {e}")
            else:
                logger.error(f"Error getting user info: {e}")
                raise SlackAPIException(f"Failed to get user info: {e}", e.response)

    def open_modal(self, trigger_id, view):
        """
        モーダルを開く

        Args:
            trigger_id: トリガーID
            view: モーダルビュー定義

        Returns:
            dict: Slack APIレスポンス

        Raises:
            SlackAPIException: API呼び出しエラー
            RateLimitException: レート制限エラー
        """
        try:
            return self.client.views_open(trigger_id=trigger_id, view=view)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                logger.warning(f"Rate limit error: {e}")
                raise RateLimitException(f"Rate limited: {e}")
            else:
                logger.error(f"Error opening modal: {e}")
                raise SlackAPIException(f"Failed to open modal: {e}", e.response)
