import json
import os
import logging
import traceback
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.sanic import AsyncSlackRequestHandler
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from mcp_client.client import MCPClient
from sanic import Sanic
import uvicorn
from sanic.response import json as sanic_json

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
        self.websocket_mode = os.environ.get("WEBSOCKET_MODE") == "true"
        self.signing_secret = os.environ.get("SLACK_SIGNING_SECRET")

        if not self.bot_token or not self.app_token or not self.signing_secret:
            raise ValueError(
                "SLACK_BOT_TOKEN, SLACK_APP_TOKEN, and SLACK_SIGNING_SECRET must be set in environment variables"
            )

        # Initialize the Slack app
        self.app = AsyncApp(
            token=self.bot_token,
            signing_secret=self.signing_secret,
        )

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

        # Note: URL verification is now handled at the HTTP level in the /slack/events route
        # This event handler is kept for reference but is not used for URL verification
        @self.app.event("url_verification")
        async def handle_url_verification(event, say, client):
            """
            Handle the URL verification event from Slack.
            This is a fallback and typically not used since verification happens at the HTTP level.
            """
            logger.info("Received URL verification event through Bolt")
            return {"challenge": event.get("challenge")}

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
        if os.environ.get("WEBSOCKET_MODE") == "true":
            logger.info("Starting SlackBot in Socket Mode")
            try:
                handler = AsyncSocketModeHandler(self.app, self.app_token)
                # Start the socket mode handler
                await handler.start_async()
            except Exception as e:
                logger.error(f"Error starting SlackBot: {e}")
                logger.error(traceback.format_exc())
                raise
        else:
            logger.info("Starting SlackBot in Web Mode")
            try:
                app = Sanic("SlackBot")

                @app.route("/slack/events", methods=["POST"])
                async def slack_events(request):
                    logger.info(f"Received Slack event: {request.json}")
                    # Handle URL verification challenge
                    if request.json and request.json.get("type") == "url_verification":
                        logger.info("Received Slack URL verification challenge")
                        return sanic_json({"challenge": request.json.get("challenge")})

                    # Handle app_mention events directly
                    if (
                        request.json
                        and request.json.get("event", {}).get("type") == "message"
                    ):
                        message = request.json.get("event", {}).get("text")
                        is_app_mentioned = "<@U08TS15GH1R>" in message
                        if not is_app_mentioned:
                            return sanic_json({"ok": True})

                        logger.info("Received app_mention event via HTTP")
                        event = request.json.get("event", {})
                        user = event.get("user")
                        channel = event.get("channel")
                        thread_ts = event.get("thread_ts") or event.get("ts")

                        try:
                            # Create a client instance for API calls
                            from slack_sdk.web.async_client import AsyncWebClient

                            client = AsyncWebClient(token=self.bot_token)

                            # Fetch thread replies
                            replies_response = await client.conversations_replies(
                                channel=channel, ts=thread_ts, inclusive=True, limit=100
                            )
                            messages = replies_response.get("messages", [])
                            flattened_text = "\n".join(
                                f"{msg.get('user')}: {msg.get('text')}"
                                for msg in messages
                            )
                            metadata = {
                                "channel": channel,
                                "thread_ts": thread_ts,
                                "user": user,
                            }

                            # Generate response
                            response = await self.client.chat_loop(
                                flattened_text + "\n\n" + json.dumps(metadata)
                            )

                            # Send response back to thread
                            await client.chat_postMessage(
                                channel=channel, text=response, thread_ts=thread_ts
                            )

                            # Return a 200 OK to Slack
                            return sanic_json({"ok": True})

                        except Exception as e:
                            logger.error(f"Error handling app_mention via HTTP: {e}")
                            logger.error(traceback.format_exc())

                            # Try to send error message
                            try:
                                from slack_sdk.web.async_client import AsyncWebClient

                                client = AsyncWebClient(token=self.bot_token)
                                await client.chat_postMessage(
                                    channel=channel,
                                    text="⚠️ 応答の生成中にエラーが発生しました",
                                    thread_ts=thread_ts,
                                )
                            except Exception as err:
                                logger.error(f"Failed to send error message: {err}")

                            # Return a 200 OK to Slack (even on error)
                            return sanic_json({"ok": True})

                    return sanic_json({"ok": True})

                port = int(os.environ.get("PORT", 8080))
                config = uvicorn.Config(app, host="0.0.0.0", port=port)
                server = uvicorn.Server(config)
                await server.serve()
            except Exception as e:
                logger.error(f"Error creating SlackBot handler: {e}")
                logger.error(traceback.format_exc())
                raise
