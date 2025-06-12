#!/usr/bin/env python3
"""
CLI tool to verify the functionality of the MCP client.

This script provides a command-line interface to interact with the MCP client,
allowing users to test different providers, models, and queries.
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from mcp_client.client import MCPClient, create_client
from mcp_client.server_manager import ServerConnectionManager


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable debug logging

    Returns:
        Configured logger
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("mcp-cli")


async def list_servers(client: MCPClient) -> None:
    """List all connected servers and their available tools.

    Args:
        client: The MCP client instance
    """
    servers = client.server_manager.get_servers()
    print(f"\n=== Connected Servers ({len(servers)}) ===")

    for server in servers:
        print(f"\n🔌 Server: {server.name}")
        try:
            tools = await server.list_tools()
            print(f"  Available Tools ({len(tools)}):")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
        except Exception as e:
            print(f"  Error listing tools: {e}")


async def send_query(client: MCPClient, query: str) -> None:
    """Send a query to the MCP client and display the response.

    Args:
        client: The MCP client instance
        query: The query to send
    """
    print(f"\n=== Query ===\n{query}")
    try:
        response = await client.chat_loop(query)
        print(f"\n=== Response ===\n{response}")
    except Exception as e:
        print(f"Error processing query: {e}")


async def run_interactive_mode(client: MCPClient) -> None:
    """Run an interactive chat session with the MCP client.

    Args:
        client: The MCP client instance
    """
    print("\n=== Interactive Mode ===")
    print("Type 'exit', 'quit', or Ctrl+C to exit")
    print("Type 'servers' to list connected servers and tools")

    try:
        while True:
            query = input("\n> ")
            if query.lower() in ("exit", "quit"):
                break
            elif query.lower() == "servers":
                await list_servers(client)
            else:
                await send_query(client, query)
    except KeyboardInterrupt:
        print("\nExiting interactive mode...")


"""
Example:
uv run cli.py --provider gemini --model gemini-2.0-flash --system-prompt system.md --query "What is the weather in Tokyo?"
uv run cli.py --provider claude --model claude-3-5-haiku-20241022 --system-prompt system.md --query "What is the weather in Tokyo?"
"""


async def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="MCP Client CLI")
    parser.add_argument(
        "--provider",
        choices=["anthropic", "claude", "gemini"],
        default="anthropic",
        help="AI provider to use (default: anthropic)",
    )
    parser.add_argument(
        "--model", help="Model name to use (if not specified, uses provider's default)"
    )
    parser.add_argument(
        "--system-prompt",
        dest="system_prompt_path",
        help="Path to a file containing the system prompt",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to the server configuration file (default: config.json)",
    )
    parser.add_argument(
        "--query", help="Query to send (if not provided, enters interactive mode)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--list-servers",
        action="store_true",
        dest="list_servers",
        help="List connected servers and their tools",
    )

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    # Load environment variables
    load_dotenv()

    # Check for required environment variables based on provider
    if args.provider in ("anthropic", "claude") and not os.getenv("ANTHROPIC_API_KEY"):
        logger.error(
            "ANTHROPIC_API_KEY environment variable is required for Anthropic/Claude provider"
        )
        sys.exit(1)
    elif args.provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        logger.error(
            "GEMINI_API_KEY environment variable is required for Gemini provider"
        )
        sys.exit(1)

    client = None
    try:
        # Initialize server manager
        server_manager = ServerConnectionManager(
            logger=logging.getLogger("ServerConnectionManager"),
            config_path=args.config,
        )
        # Initialize the server manager manually
        await server_manager.__aenter__()

        # Create the client
        client = MCPClient(
            server_manager=server_manager,
            logger=logging.getLogger("MCPClient"),
            provider=args.provider,
            model=args.model,
            system_prompt_path=args.system_prompt_path,
        )

        logger.info(f"Initialized MCP client with provider: {args.provider}")
        if args.model:
            logger.info(f"Using model: {args.model}")

        # List servers if requested
        if args.list_servers:
            await list_servers(client)

        # Process query or enter interactive mode
        if args.query:
            await send_query(client, args.query)
        else:
            await run_interactive_mode(client)

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
    finally:
        # Clean up server connections
        if client and client.server_manager:
            logger.info("Cleaning up server connections...")
            await client.server_manager.__aexit__(None, None, None)
            logger.info("Server connections cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
