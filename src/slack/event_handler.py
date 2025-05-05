import logging
import json
from fastapi import Request, HTTPException
from typing import Dict, Any, Optional

from src.slack.verification import verify_slack_request
from src.slack.client import SlackClient
from src.slack.exceptions import (
    InvalidRequestException,
    AuthenticationException,
    EventProcessingException,
)

logger = logging.getLogger(__name__)


class SlackEventHandler:
    """
    Slackイベントを処理するハンドラークラス
    """

    def __init__(self, config):
        """
        初期化

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.signing_secret = config.SLACK_SIGNING_SECRET
        self.slack_client = SlackClient(config.SLACK_BOT_TOKEN)
        self.fast_agent = None  # 後で設定される

    async def handle_event(self, request: Request) -> Dict[str, Any]:
        """
        Slackイベントを処理

        Args:
            request: FastAPIリクエストオブジェクト

        Returns:
            Dict[str, Any]: レスポンス

        Raises:
            HTTPException: リクエスト検証エラーや処理エラー
        """
        # リクエストボディの取得
        body = await request.body()

        # リクエスト検証
        if not verify_slack_request(request.headers, body, self.signing_secret):
            logger.warning("Invalid Slack request signature")
            raise HTTPException(status_code=401, detail="Invalid request signature")

        # イベントデータの解析
        try:
            event_data = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            raise HTTPException(status_code=400, detail="Invalid JSON")

        logger.debug(f"Received Slack event: {event_data}")

        # イベントタイプに基づく処理
        event_type = event_data.get("type")

        if event_type == "url_verification":
            # URL検証チャレンジ
            return {"challenge": event_data.get("challenge")}

        elif event_type == "event_callback":
            # イベントコールバック
            return await self._process_event_callback(event_data)

        # その他のイベントタイプ
        return {"status": "received"}

    async def _process_event_callback(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        イベントコールバックの処理

        Args:
            event_data: イベントデータ

        Returns:
            Dict[str, Any]: 処理結果
        """
        event = event_data.get("event", {})
        event_type = event.get("type")

        # イベントタイプに基づく処理
        if event_type == "message":
            return await self._process_message(event)
        elif event_type == "app_mention":
            return await self._process_app_mention(event)

        # その他のイベントタイプ
        return {"status": "event_received", "event_type": event_type}

    async def _process_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        メッセージイベントの処理

        Args:
            event: メッセージイベントデータ

        Returns:
            Dict[str, Any]: 処理結果
        """
        # ボットメッセージは無視
        if event.get("bot_id"):
            return {"status": "ignored", "reason": "bot_message"}

        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text")
        ts = event.get("ts")

        logger.info(f"Received message from {user} in {channel}: {text}")

        # fast-agentが設定されている場合、イベント処理を委譲
        if self.fast_agent:
            try:
                result = self.fast_agent.process_event(event)
                return {"status": "processed", "result": result}
            except Exception as e:
                logger.error(f"Error processing event with fast-agent: {e}")
                return {"status": "error", "error": str(e)}

        # fast-agentが設定されていない場合
        return {"status": "received", "message": "Message received"}

    async def _process_app_mention(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        アプリメンションイベントの処理

        Args:
            event: アプリメンションイベントデータ

        Returns:
            Dict[str, Any]: 処理結果
        """
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text")
        ts = event.get("ts")

        logger.info(f"Received app mention from {user} in {channel}: {text}")

        # fast-agentが設定されている場合、イベント処理を委譲
        if self.fast_agent:
            try:
                result = self.fast_agent.process_event(event)
                return {"status": "processed", "result": result}
            except Exception as e:
                logger.error(f"Error processing event with fast-agent: {e}")
                # エラーメッセージをSlackに送信
                self.slack_client.post_message(
                    channel=channel,
                    text=f"エラーが発生しました: {str(e)}",
                    thread_ts=ts,
                )
                return {"status": "error", "error": str(e)}

        # fast-agentが設定されていない場合、シンプルな応答
        self.slack_client.post_message(
            channel=channel,
            text="こんにちは！何かお手伝いできることはありますか？",
            thread_ts=ts,
        )

        return {"status": "responded", "message": "Responded to app mention"}

    def send_response(
        self,
        channel: str,
        text: str,
        blocks: Optional[list] = None,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Slackにレスポンスを送信

        Args:
            channel: チャンネルID
            text: メッセージテキスト
            blocks: ブロックキット要素（オプション）
            thread_ts: スレッドタイムスタンプ（オプション）

        Returns:
            Dict[str, Any]: Slack APIレスポンス
        """
        return self.slack_client.post_message(
            channel=channel, text=text, blocks=blocks, thread_ts=thread_ts
        )
