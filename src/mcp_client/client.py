"""MCP Client implementation.

This module provides the main MCPClient class which handles processing queries
using various AI providers (Anthropic, OpenAI, Gemini) and available MCP tools.
"""

import os
import logging
import asyncio
from typing import Dict, Optional, List, Any, Literal

from .server_manager import ServerConnectionManager
from .agent_manager import AgentManager


class MCPClient:
    def __init__(
        self,
        server_manager: Optional[ServerConnectionManager] = None,
        config_path: Optional[str] = "config.json",
        logger: Optional[logging.Logger] = None,
        provider: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize the MCP client

        Args:
            server_manager: Optional server connection manager
            config_path: Path to the configuration file
            logger: Optional logger
            provider: AI provider to use ('anthropic', 'openai', or 'gemini')
            model: Model name to use (if None, uses provider's default)
            api_key: API key for the provider (if None, uses environment variable)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.server_manager = server_manager or ServerConnectionManager(
            logger=self.logger
        )
        self.config_path = config_path

        # Initialize the agent manager
        agent_kwargs = {"logger": self.logger}
        if model:
            agent_kwargs["model"] = model
        if api_key:
            agent_kwargs["api_key"] = api_key

        self.agent_manager = AgentManager.create(provider, **agent_kwargs)

        # Load server configuration
        if config_path and os.path.exists(config_path):
            self.server_manager.load_server_config(config_path)

    async def initialize(self):
        """Initialize the client by connecting to all servers

        Args:
            connect_args: List of (name, script_path) tuples for stdio servers
        """
        await self.server_manager.initialize()

    def _select_appropriate_server(self, query: str, server_names: List[str]) -> str:
        """Select the most appropriate server based on the query content

        This method analyzes the query and tries to determine which server
        would be most appropriate to handle it based on dynamically generated
        and configured keywords.

        Args:
            query: The user query to process
            server_names: List of available server names

        Returns:
            The name of the selected server
        """
        query_lower = query.lower()

        # Get server keywords from the server manager
        server_keywords = self.get_server_keywords()

        # Track matched servers and their match scores
        server_matches = {}

        # Check for keyword matches for each available server
        for server_name in server_names:
            # Get keywords for this server
            keywords = server_keywords.get(server_name, [])

            if not keywords:
                # If no keywords are available for this server, add the server name itself
                keywords = [server_name.lower()]

            # Count how many keywords match in the query
            match_count = sum(1 for keyword in keywords if keyword in query_lower)

            # If there are matches, record the server and its match count
            if match_count > 0:
                server_matches[server_name] = match_count
                self.logger.debug(
                    f"Server '{server_name}' matched {match_count} keywords"
                )

        # If we have matches, select the server with the most keyword matches
        if server_matches:
            best_server = max(server_matches.items(), key=lambda x: x[1])[0]
            self.logger.info(
                f"Selected server '{best_server}' based on keyword matches"
            )
            return best_server

        # If no specific server can be determined, use the first available server
        default_server = server_names[0]
        self.logger.info(
            f"No specific server detected for query, using default: '{default_server}'"
        )
        return default_server

    def get_server_keywords(self) -> Dict[str, List[str]]:
        """Get the keywords for all servers

        Returns:
            Dictionary with server names as keys and lists of keywords as values
        """
        return self.server_manager.server_keywords

    def _query_requires_mcp(self, query: str) -> bool:
        """Determine if a query likely requires MCP tools

        This method analyzes the query to determine if it likely requires MCP tools
        or if it can be handled directly by Claude without tools.

        Args:
            query: The user query to process

        Returns:
            True if the query likely requires MCP tools, False otherwise
        """
        # Get all server keywords
        all_keywords = []
        for keywords in self.server_manager.server_keywords.values():
            all_keywords.extend(keywords)

        # If we have no keywords, we can't determine if MCP is needed
        if not all_keywords:
            return False

        # Check if any keywords appear in the query
        query_lower = query.lower()
        for keyword in all_keywords:
            if keyword in query_lower:
                return True

        # Check for phrases that might indicate tool use is needed
        tool_indicators = [
            "use tool",
            "using tool",
            "with tool",
            "execute",
            "run",
            "call function",
            "api",
            "server",
            "database",
            "fetch",
            "retrieve",
        ]

        for indicator in tool_indicators:
            if indicator in query_lower:
                return True

        return False

    async def _process_query_without_mcp(self, query: str) -> str:
        """Process a query directly without using MCP tools

        Args:
            query: The user query to process

        Returns:
            The processed response
        """
        return await self.agent_manager.process_query_without_tools(query)

    async def process_query(self, query: str, server_name: Optional[str] = None) -> str:
        """Process a query using AI and available tools from a specific server

        Args:
            query: The user query to process
            server_name: Name of the server to use (if None, automatically selects an appropriate server)

        Returns:
            The processed response
        """
        server_names = self.server_manager.get_server_names()

        # If no servers connected or query doesn't seem to require MCP, process directly
        if not server_names or (
            server_name is None and not self._query_requires_mcp(query)
        ):
            return await self._process_query_without_mcp(query)

        # If server_name is not specified, automatically select an appropriate server
        if server_name is None:
            server_name = self._select_appropriate_server(query, server_names)

        # Check if the specified server exists
        if server_name not in server_names:
            available_servers = ", ".join(server_names)
            return f"Server '{server_name}' not found. Available servers: {available_servers}"

        # Get the server session
        session = self.server_manager.get_server_session(server_name)
        if not session:
            return f"Error: Could not get session for server '{server_name}'"

        self.logger.info(f"🚀 Processing query with server '{server_name}': {query}")

        # Process the query using the agent manager with the server
        return await self.agent_manager.process_query_with_server(
            query, session, server_name
        )

    async def chat_loop(self):
        """Run an interactive chat loop"""
        has_servers = bool(self.server_manager.get_server_names())
        self.logger.info("MCP Client Started!")
        self.logger.info(f"Using AI provider: {self.agent_manager.__class__.__name__}")
        self.logger.info("Type your queries or 'quit' to exit.")

        if has_servers:
            self.logger.info("'servers' to list connected servers.")
            self.logger.info(
                "To use a specific server, prefix your query with 'server_name:'"
            )
            self.logger.info(
                "If no server is specified, an appropriate server will be automatically selected based on your query."
            )
        else:
            self.logger.info("Running in direct mode without MCP tools.")

        # Flag to track if we're currently processing a query
        processing_lock = asyncio.Lock()

        while True:
            try:
                # Use synchronous input to get the query
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                if query.lower() == "servers":
                    servers = self.server_manager.list_connected_servers()
                    if not servers:
                        self.logger.info("No servers connected.")
                    else:
                        self.logger.info("Connected servers:")
                        for server_name, tools in servers.items():
                            server_info = f"- {server_name}: {', '.join(tools)}"
                            self.logger.info(server_info)
                    continue

                # Process the query with a lock to prevent parallel processing
                async with processing_lock:
                    # Check if query specifies a server
                    server_name = None
                    server_names = self.server_manager.get_server_names()
                    self.logger.info(f"🍇 Processing query with server: {server_names}")
                    self.logger.info(f"🍇 Query: {query}")
                    if ":" in query and query.split(":", 1)[0] in server_names:
                        server_name, query = query.split(":", 1)
                        query = query.strip()

                    self.logger.info(f"🍇 Processing query with server: {server_name}")
                    response = await self.process_query(query, server_name)
                    self.logger.info("\n" + response)

            except Exception as e:
                self.logger.error(f"Error: {str(e)}", exc_info=True)
                self.logger.info(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.server_manager.cleanup()
