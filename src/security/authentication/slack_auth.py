import logging
import hmac
import hashlib
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SlackAuthenticator:
    """
    Slack認証を管理するクラス
    """

    def __init__(self, config):
        """
        初期化

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.signing_secret = config.SLACK_SIGNING_SECRET
        self.bot_token = config.SLACK_BOT_TOKEN

    def verify_request(self, headers: Dict[str, str], body: bytes) -> bool:
        """
        Slackリクエストの署名を検証

        Args:
            headers: リクエストヘッダー
            body: リクエストボディ

        Returns:
            bool: 署名が有効な場合はTrue、そうでない場合はFalse
        """
        # 必要なヘッダーが存在するか確認
        if (
            "X-Slack-Request-Timestamp" not in headers
            or "X-Slack-Signature" not in headers
        ):
            logger.warning("Missing required headers for Slack request verification")
            return False

        # タイムスタンプを取得
        timestamp = headers["X-Slack-Request-Timestamp"]

        # リクエストが古すぎないか確認（5分以上前のリクエストは拒否）
        current_timestamp = int(time.time())
        if abs(current_timestamp - int(timestamp)) > 60 * 5:
            logger.warning(f"Slack request too old: {timestamp}")
            return False

        # 署名の計算
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"

        # HMACを使用して署名を計算
        my_signature = (
            "v0="
            + hmac.new(
                self.signing_secret.encode("utf-8"),
                sig_basestring.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        )

        # 署名を比較
        slack_signature = headers["X-Slack-Signature"]

        is_valid = hmac.compare_digest(my_signature, slack_signature)
        if not is_valid:
            logger.warning("Invalid Slack request signature")

        return is_valid

    def get_bot_token(self) -> str:
        """
        ボットトークンを取得

        Returns:
            str: ボットトークン
        """
        return self.bot_token

    def get_user_info(self, user_id: str, client=None) -> Optional[Dict[str, Any]]:
        """
        ユーザー情報を取得

        Args:
            user_id: ユーザーID
            client: Slackクライアント（オプション）

        Returns:
            Optional[Dict[str, Any]]: ユーザー情報、取得できない場合はNone
        """
        if client is None:
            # クライアントが提供されていない場合は、ユーザー情報を取得できない
            logger.warning("No Slack client provided to get user info")
            return None

        try:
            response = client.get_user_info(user_id)
            if response.get("ok"):
                return response.get("user")
            else:
                logger.error(f"Error getting user info: {response.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Exception getting user info: {e}")
            return None

    def is_admin(self, user_info: Dict[str, Any]) -> bool:
        """
        ユーザーが管理者かどうかを確認

        Args:
            user_info: ユーザー情報

        Returns:
            bool: 管理者の場合はTrue、そうでない場合はFalse
        """
        # Slackのユーザー情報から管理者かどうかを判断
        # 実際の実装では、組織の要件に応じてカスタマイズする必要がある
        is_admin = user_info.get("is_admin", False) or user_info.get("is_owner", False)
        return is_admin
