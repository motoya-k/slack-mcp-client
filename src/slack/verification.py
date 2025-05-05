import hmac
import hashlib
import time
from typing import Dict, Union, AnyStr


def verify_slack_request(
    headers: Dict[str, str], body: AnyStr, signing_secret: str
) -> bool:
    """
    Slackからのリクエストの署名を検証します。

    Args:
        headers: リクエストヘッダー
        body: リクエストボディ
        signing_secret: Slackアプリの署名シークレット

    Returns:
        bool: 署名が有効な場合はTrue、そうでない場合はFalse
    """
    # 必要なヘッダーが存在するか確認
    if "X-Slack-Request-Timestamp" not in headers or "X-Slack-Signature" not in headers:
        return False

    # タイムスタンプを取得
    timestamp = headers["X-Slack-Request-Timestamp"]

    # リクエストが古すぎないか確認（5分以上前のリクエストは拒否）
    current_timestamp = int(time.time())
    if abs(current_timestamp - int(timestamp)) > 60 * 5:
        return False

    # 署名の計算
    if isinstance(body, bytes):
        req_body = body
    else:
        req_body = body.encode("utf-8")

    # 署名ベースの作成: バージョン:タイムスタンプ:ボディ
    sig_basestring = f"v0:{timestamp}:{req_body.decode('utf-8')}"

    # HMACを使用して署名を計算
    my_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )

    # 署名を比較
    slack_signature = headers["X-Slack-Signature"]

    return hmac.compare_digest(my_signature, slack_signature)
