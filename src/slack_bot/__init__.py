import json
import os
import logging
import traceback
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from mcp_client.client import MCPClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SlackBot:
    def __init__(self, client: MCPClient, config_path=None):
        """
        Initialize the Slack bot.

        Args:
            config_path: Path to configuration file (optional)
        """
        # Get Slack tokens from environment variables
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.app_token = os.environ.get("SLACK_APP_TOKEN")

        if not self.bot_token or not self.app_token:
            raise ValueError(
                "SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in environment variables"
            )

        # Initialize the Slack app
        self.app = AsyncApp(token=self.bot_token)

        # Register event handlers
        self._register_handlers()
        self.client = client

        # Register error handler
        @self.app.error
        async def error_handler(error, body, logger):
            logger.error(f"Error handling Slack event: {error}")
            logger.error(f"Event body: {body}")
            logger.error(traceback.format_exc())

        logger.info("SlackBot initialized")

    def _register_handlers(self):
        """Register event handlers for the Slack app."""

        # Handle app_mention events (when the bot is mentioned)

        @self.app.event("app_mention")
        async def handle_app_mention(event, say, client):
            """
            When the bot is mentioned in a thread, fetch the full thread (including parent message),
            flatten it, and use it as context for processing.
            """
            user = event.get("user")
            channel = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")
            logger.info(f"Received mention from user {user} in thread {thread_ts}")

            try:
                replies_response = await client.conversations_replies(
                    channel=channel, ts=thread_ts, inclusive=True, limit=100  # 適宜調整
                )
                messages = replies_response.get("messages", [])
                flattened_text = "\n".join(
                    f"{msg.get('user')}: {msg.get('text')}" for msg in messages
                )
                metadata = {
                    "channel": channel,
                    "thread_ts": thread_ts,
                    "user": user,
                }
            except Exception as e:
                logger.error(f"Failed to fetch thread replies: {e}")
                await say(
                    text="⚠️ スレッドの取得中にエラーが発生しました", thread_ts=thread_ts
                )
                return

            try:
                response = await self.client.chat_loop(
                    flattened_text + "\n\n" + json.dumps(metadata)
                )
                await say(text=response, thread_ts=thread_ts)
            except Exception as e:
                logger.error(f"Failed to generate response: {e}")
                await say(
                    text="⚠️ 応答の生成中にエラーが発生しました", thread_ts=thread_ts
                )

    async def start(self):
        """Start the Slack bot using Socket Mode."""
        logger.info("Starting SlackBot in Socket Mode")
        try:
            handler = AsyncSocketModeHandler(self.app, self.app_token)

            # Start the socket mode handler
            await handler.start_async()
        except Exception as e:
            logger.error(f"Error starting SlackBot: {e}")
            logger.error(traceback.format_exc())
            raise
