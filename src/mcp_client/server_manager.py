"""Server connection manager for MCP clients.

This module provides the ServerConnectionManager class which handles connections
to MCP servers with different transport methods.
"""

import json
import os
import logging
from typing import Dict, Optional, Tuple, Any, List, Union
from contextlib import AsyncExitStack
import re

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ServerConnectionManager:
    """Manages connections to MCP servers with different transport methods"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.exit_stack = AsyncExitStack()
        self.server_config: Dict[str, Dict[str, Any]] = {}
        self.server_keywords: Dict[str, List[str]] = {}
        self.logger = logger or logging.getLogger(__name__)

    async def initialize(self):
        """Initialize by connecting to all servers in the config and command line args

        Args:
            connect_args: List of (name, script_path) tuples for stdio servers
            connect_http_args: List of (name, url) tuples for HTTP servers
        """
        # Connect to servers from config file
        if self.server_config:
            for server_name, server_info in self.server_config.items():
                try:
                    await self.connect_to_server_from_config(server_name, server_info)
                except Exception as e:
                    self.logger.error(
                        f"Error connecting to server '{server_name}': {str(e)}"
                    )

    def load_server_config(self, config_path: str) -> None:
        """Load server configuration from a JSON file

        Args:
            config_path: Path to the JSON configuration file
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            # Store configuration but don't connect yet
            self.server_config = config

            # Extract keywords from config if available
            for server_name, server_info in config.items():
                if "keywords" in server_info:
                    self.server_keywords[server_name] = server_info["keywords"]
        except Exception as e:
            self.logger.error(f"Error loading server configuration: {str(e)}")

    def _process_env_variables(
        self, env_config: Optional[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        """Process environment variables in the configuration

        This function handles:
        1. Using values from the system environment if env_config is None
        2. Substituting environment variables in the config values (e.g., $VAR or ${VAR})

        Args:
            env_config: Environment configuration from config file

        Returns:
            Processed environment variables dictionary
        """
        if env_config is None:
            return None

        processed_env = {}
        for key, value in env_config.items():
            if isinstance(value, str):
                # Check if the value is an environment variable reference
                if value.startswith("$"):
                    # Handle both $VAR and ${VAR} formats
                    env_var_name = (
                        value[1:] if not value.startswith("${") else value[2:-1]
                    )
                    # Get from system environment or use original as fallback
                    env_value = os.environ.get(env_var_name)
                    if env_value is not None:
                        processed_env[key] = env_value
                    else:
                        self.logger.warning(
                            f"Environment variable {env_var_name} not found for {key}"
                        )
                        processed_env[key] = value
                else:
                    processed_env[key] = value
            else:
                processed_env[key] = value

        return processed_env

    async def connect_to_server_from_config(
        self, server_name: str, server_config: Dict[str, Any]
    ):
        """Connect to an MCP server using configuration data

        Args:
            server_name: Name to identify this server connection
            server_config: Configuration dictionary for the server
        """
        transport = server_config.get("transport", "stdio")

        # Process environment variables
        env_config = self._process_env_variables(server_config.get("env"))

        if transport == "stdio":
            await self.connect_to_stdio_server(
                server_name,
                server_config.get("command"),
                server_config.get("args", []),
                env_config,
            )
        elif transport == "http":
            await self.connect_to_http_server(server_name, server_config.get("url"))
        else:
            raise ValueError(f"Unsupported transport type: {transport}")

    async def connect_to_stdio_server(
        self,
        server_name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
    ):
        """Connect to an MCP server using stdio transport

        Args:
            server_name: Name to identify this server connection
            command: Command to run (e.g., "python", "node")
            args: Command arguments (e.g., ["script.py"])
            env: Environment variables
        """
        # Check if server with this name already exists
        if server_name in self.servers:
            self.logger.info(f"Server '{server_name}' is already connected")
            return

        server_params = StdioServerParameters(command=command, args=args, env=env)

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

        await session.initialize()

        # List available tools
        response = await session.list_tools()
        tools = response.tools

        # Generate keywords from server name and tools
        keywords = self._generate_keywords_from_tools(server_name, tools)

        # If there are keywords in the config, merge them with the generated ones
        if server_name in self.server_keywords:
            keywords.extend(self.server_keywords[server_name])
            # Remove duplicates while preserving order
            keywords = list(dict.fromkeys(keywords))

        # Update server keywords
        self.server_keywords[server_name] = keywords

        # Store server information
        self.servers[server_name] = {
            "transport": "stdio",
            "command": command,
            "args": args,
            "env": env,
            "session": session,
            "stdio": stdio,
            "write": write,
            "tools": tools,
        }

        self.logger.info(
            f"Connected to stdio server '{server_name}' with tools: {[tool.name for tool in tools]}"
        )
        self.logger.info(f"Generated keywords for '{server_name}': {keywords}")

    async def connect_to_http_server(self, server_name: str, url: str):
        """Connect to an MCP server using HTTP transport

        Args:
            server_name: Name to identify this server connection
            url: URL of the HTTP server
        """
        raise NotImplementedError("HTTP transport is not implemented yet")

    def _generate_keywords_from_tools(
        self, server_name: str, tools: List[Any]
    ) -> List[str]:
        """Generate keywords from server name and tools

        This method extracts keywords from:
        1. The server name itself
        2. Tool names (split by underscore and camelCase)
        3. Common words from tool descriptions

        Args:
            server_name: Name of the server
            tools: List of tools provided by the server

        Returns:
            List of generated keywords
        """
        keywords = []

        # Add server name as a keyword
        keywords.append(server_name.lower())

        # Process each tool
        for tool in tools:
            # Add tool name (split by underscore and extract words)
            tool_name = tool.name.lower()

            # Add the whole tool name
            keywords.append(tool_name)

            # Split by underscore and add parts
            name_parts = tool_name.split("_")
            keywords.extend(name_parts)

            # Split camelCase words
            for part in name_parts:
                # Find camelCase boundaries and split
                camel_case_parts = re.findall(r"[a-z]+|[A-Z][a-z]*", part)
                keywords.extend([p.lower() for p in camel_case_parts if p])

            # Extract keywords from description if available
            if hasattr(tool, "description") and tool.description:
                # Simple keyword extraction - split description and take words longer than 3 chars
                desc_words = tool.description.lower().split()
                # Filter out common stop words and short words
                stop_words = {"the", "and", "for", "with", "this", "that", "from", "to"}
                desc_keywords = [
                    word
                    for word in desc_words
                    if len(word) > 3 and word not in stop_words
                ]
                keywords.extend(desc_keywords)

        # Remove duplicates while preserving order
        unique_keywords = list(dict.fromkeys(keywords))

        return unique_keywords

    def list_connected_servers(self) -> Dict[str, list]:
        """List all connected servers and their available tools

        Returns:
            Dictionary with server names as keys and list of tool names as values
        """
        result = {}
        for server_name, server_data in self.servers.items():
            result[server_name] = [tool.name for tool in server_data["tools"]]
        return result

    def get_server_session(self, server_name: str) -> Optional[ClientSession]:
        """Get the session for a specific server

        Args:
            server_name: Name of the server

        Returns:
            The server session or None if not found
        """
        if server_name in self.servers:
            return self.servers[server_name]["session"]
        return None

    def get_server_tools(self, server_name: str) -> List[Any]:
        """Get the tools for a specific server

        Args:
            server_name: Name of the server

        Returns:
            List of tools or empty list if not found
        """
        if server_name in self.servers:
            return self.servers[server_name]["tools"]
        return []

    def get_server_names(self) -> List[str]:
        """Get the names of all connected servers

        Returns:
            List of server names
        """
        return list(self.servers.keys())

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
