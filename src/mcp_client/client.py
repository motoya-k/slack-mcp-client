"""MCP Client implementation.

This module provides the main MCPClient class which handles processing queries
using various AI providers (Anthropic, OpenAI, Gemini) and available MCP tools.
"""

import os
import logging
import asyncio
from typing import Dict, Optional, List, Any, Literal

from .server_manager import ServerConnectionManager
from .agent_manager import create_agent


class MCPClient:
    def __init__(
        self,
        server_manager: Optional[ServerConnectionManager] = None,
        logger: Optional[logging.Logger] = None,
        provider: str = "anthropic",
        model: Optional[str] = None,
    ):
        """Initialize the MCP client

        Args:
            server_manager: Optional server connection manager
            logger: Optional logger
            provider: AI provider to use ('anthropic', 'openai', or 'gemini')
            model: Model name to use (if None, uses provider's default)
        """
        self.logger = logger
        self.server_manager = server_manager

        # Initialize the agent manager
        agent_kwargs = {"logger": self.logger}
        if model:
            agent_kwargs["model"] = model

        self.agent_manager = create_agent(provider, **agent_kwargs)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        query = input("")
        servers = self.server_manager.get_servers()
        response = await self.agent_manager.process_query(query, servers)

        print(f"😺 MCP Client response: {response}")
