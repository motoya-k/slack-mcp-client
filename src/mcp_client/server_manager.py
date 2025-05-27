import asyncio
import json
import os
import logging
from typing import Dict, Optional, Any, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        parameters: Dict[str, Any],
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: Dict[str, Any] = input_schema
        self.parameters: Dict[str, Any] = parameters

    def get_name(self) -> str:
        """Get the name of the tool."""
        return self.name

    def get_description(self) -> str:
        """Get the description of the tool."""
        return self.description

    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema of the tool."""
        return self.input_schema

    def get_parameters(self) -> Dict[str, Any]:
        """Get the parameters of the tool."""
        return self.parameters

    def format_for_llm(self) -> str:
        """Format tool information for LLM.

        Returns:
            A formatted string describing the tool.
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""


class Server:
    """Manages MCP server connections and tool execution."""

    def __init__(
        self, name: str, config: Dict[str, Any], logger: Optional[logging.Logger] = None
    ) -> None:
        self.name: str = name
        self.config: Dict[str, Any] = config
        self.logger = logger or logging.getLogger(__name__)
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def __aenter__(self):
        """Connect to the server."""
        env_config = self._process_env_variables(self.config.get("env"))

        transport = self.config.get("transport", "stdio")
        if transport == "stdio":
            await self._connect_to_stdio_server(
                self.config.get("command"),
                self.config.get("args", []),
                env_config,
            )
        elif transport == "http":
            await self._connect_to_http_server(self.config.get("url"))
        else:
            raise ValueError(f"Unsupported transport type: {transport}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the server."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
                self.logger.info(f"✨ Cleaned up server {self.name}")
            except Exception as e:
                self.logger.error(f"Error during cleanup of server {self.name}: {e}")

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
                if value.startswith("$"):
                    env_var_name = (
                        value[1:] if not value.startswith("${") else value[2:-1]
                    )
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

    async def _connect_to_stdio_server(
        self,
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
        server_params = StdioServerParameters(command=command, args=args, env=env)

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
        except Exception as e:
            self.logger.error(f"Error initializing server {self.name}: {e}")
            # No need to call cleanup here, __aexit__ will handle it
            raise

    async def _connect_to_http_server(self, url: str):
        """Connect to an MCP server using HTTP transport

        Args:
            url: URL of the HTTP server
        """
        raise NotImplementedError("HTTP transport is not implemented yet")

    async def list_tools(self) -> List[Tool]:
        """List available tools from the server."""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []
        for item in tools_response.tools:
            tools.append(
                Tool(item.name, item.description, item.inputSchema, item.annotations)
            )
        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ):
        """Call a tool on the server."""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                self.logger.info(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)
                return result
            except Exception as e:
                attempt += 1
                self.logger.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                if attempt < retries:
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error("Max retries reached. Failing.")
                    raise


class ServerConnectionManager:
    """Manages connections to MCP servers with different transport methods"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        config_path="config.json",
    ):
        self.servers: List[Server] = []
        self.logger = logger or logging.getLogger(__name__)
        self.config_path = config_path
        self.server_config: Dict[str, Any] = {}
        self._server_exit_stack: AsyncExitStack = AsyncExitStack()

    async def __aenter__(self):
        """Initialize by connecting to all servers in the config and command line args"""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            self.server_config = config
        except Exception as e:
            self.logger.error(f"Error loading server configuration: {str(e)}")
            raise

        for server_name, server_config in self.server_config.items():
            server = await self._server_exit_stack.enter_async_context(
                Server(server_name, server_config, logger=self.logger)
            )
            self.servers.append(server)

        self.logger.info(f"Connected to {len(self.servers)} servers")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all server connections."""
        self.logger.info("🧹 Cleaning up server connections...")
        await self._server_exit_stack.aclose()
        self.logger.info("✨ Server connections cleaned up.")

    def list_connected_servers(self) -> Dict[str, list]:
        """List all connected servers and their available tools

        Returns:
            Dictionary with server names as keys and list of tool names as values
        """
        result = {}
        for server in self.servers:
            result[server.name] = []
        return result

    def get_servers(self) -> List[Server]:
        """Get the servers

        Returns:
            List of server names
        """
        return self.servers
