#!/usr/bin/env python3
"""Command-line interface for the Slack MCP Client.

This module provides the main entry point for the Slack MCP Client.
"""

import asyncio
import logging
from dotenv import load_dotenv

from mcp_client.server_manager import ServerConnectionManager
from mcp_client.client import MCPClient


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("mcp_client")


async def main():
    """Main entry point for the Slack MCP Client."""
    # Load environment variables
    load_dotenv()

    # Setup logging
    logger = setup_logging()

    # Create server manager and client
    server_manager = ServerConnectionManager(logger=logger)
    # Anthropic
    # client = MCPClient(
    #     server_manager=server_manager,
    #     config_path="config.json",
    #     logger=logger,
    #     provider="anthropic",
    #     model="claude-3-5-sonnet-20240620",
    # )
    # Gemini
    client = MCPClient(
        server_manager=server_manager,
        config_path="config.json",
        logger=logger,
        provider="gemini",
        model="gemini-2.0-flash",
    )
    # OpenAI
    # client = MCPClient(
    #     server_manager=server_manager,
    #     config_path="config.json",
    #     logger=logger,
    #     provider="openai",
    #     model="gpt-4o",
    # )

    try:
        # Initialize client (connects to all servers in config and command line)
        await client.initialize()

        # Continue even if no servers connected
        if not server_manager.get_server_names():
            logger.warning(
                f"No servers connected. Running in direct mode without MCP tools."
            )

        # Start chat loop
        await client.chat_loop()
    finally:
        await client.cleanup()


def run():
    """Run the Slack MCP Client."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
