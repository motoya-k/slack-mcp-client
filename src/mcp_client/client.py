"""MCP Client implementation.

This module provides the main MCPClient class which handles processing queries
using various AI providers (Anthropic, OpenAI, Gemini) and available MCP tools.
"""

import os
import logging
import asyncio
from typing import Dict, Optional, List, Any, Literal

from dotenv import load_dotenv

from .server_manager import ServerConnectionManager
from .agent_manager import create_agent


class MCPClient:
    def __init__(
        self,
        server_manager: Optional[ServerConnectionManager] = None,
        logger: Optional[logging.Logger] = None,
        provider: str = "anthropic",
        model: Optional[str] = None,
        system_prompt_path: Optional[str] = None,
    ):
        """Initialize the MCP client

        Args:
            server_manager: Optional server connection manager
            logger: Optional logger
            provider: AI provider to use ('anthropic', 'openai', or 'gemini')
            model: Model name to use (if None, uses provider's default)
            system_prompt_path: Path to a file containing the system prompt
        """
        self.logger = logger
        self.server_manager = server_manager

        # Initialize the agent manager
        agent_kwargs = {"logger": self.logger}
        if model:
            agent_kwargs["model"] = model

        self.agent_manager = create_agent(
            provider, system_prompt_path=system_prompt_path, **agent_kwargs
        )

    async def chat_loop(self, query: str):
        """Run an interactive chat loop"""
        servers = self.server_manager.get_servers()
        response = await self.agent_manager.process_query(query, servers)
        return response


async def create_client() -> MCPClient:
    load_dotenv()
    # Don't use async with here - we need the server_manager to stay active
    server_manager = ServerConnectionManager(
        logger=logging.getLogger("ServerConnectionManager"),
        config_path="config.json",
    )
    # Initialize the server manager manually
    await server_manager.__aenter__()

    client = MCPClient(
        server_manager=server_manager,
        logger=logging.getLogger("MCPClient"),
        provider="anthropic",
        model="claude-3-7-sonnet-20250219",
        system_prompt_path="system.md",
    )
    return client
