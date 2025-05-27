#!/usr/bin/env python3

import os
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from mcp_client.client import create_client
from slack_bot import SlackBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()
    client = None
    try:
        # Initialize the bot without config path as we're using environment variables
        client = await create_client()
        bot = SlackBot(client)
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        # Clean up server connections
        if client and client.server_manager:
            logger.info("Cleaning up server connections...")
            await client.server_manager.__aexit__(None, None, None)
            logger.info("Server connections cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
