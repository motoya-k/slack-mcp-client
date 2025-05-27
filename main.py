#!/usr/bin/env python3
"""Command-line interface for the Slack MCP Client.

This module provides the main entry point for the Slack MCP Client.
"""

import asyncio
import logging
from dotenv import load_dotenv

from mcp_client.server_manager import ServerConnectionManager
from mcp_client.client import MCPClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the Slack MCP Client."""
    load_dotenv()

    async with ServerConnectionManager(
        logger=logging.getLogger("ServerConnectionManager"),
        config_path="config.json",
    ) as server_manager:
        # Create client with system prompt
        # client = MCPClient(
        #     server_manager=server_manager,
        #     logger=logging.getLogger("MCPClient"),
        #     provider="gemini",
        #     model="gemini-2.5-pro-preview-05-06",
        #     system_prompt_path="system.md",
        # )
        client = MCPClient(
            server_manager=server_manager,
            logger=logging.getLogger("MCPClient"),
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            system_prompt_path="system.md",
        )
        await client.chat_loop()

        print("🐘 Application running...")

    # The __aexit__ method of ServerConnectionManager will handle cleanup automatically
    # when exiting the 'async with' block.


def run():
    """Run the Slack MCP Client."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
