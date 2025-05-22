# Slack MCP Client

A Python client for connecting to and interacting with Model Context Protocol (MCP) servers.

## Features

- Connect to multiple MCP servers simultaneously
- Support for different transport methods (stdio, HTTP)
- Manage server connections with JSON configuration
- Support for multiple AI providers (Anthropic, OpenAI, Gemini)
- Interactive chat interface with AI
- Support for both Python and JavaScript MCP servers
- Clean architecture with dependency injection

## Installation

```bash
uv sync
```

## Usage

### Using JSON Configuration (Recommended)

Create a `config.json` file with transport-specific configurations:

```json
{
  "weather": {
    "transport": "stdio",
    "command": "python",
    "args": ["src/weather.py"],
    "env": null
  },
  "calculator": {
    "transport": "stdio",
    "command": "node",
    "args": ["src/calculator.js"],
    "env": null
  },
  "example_http": {
    "transport": "http",
    "url": "http://localhost:8000"
  }
}
```

Then simply run the client:

```bash
# Using the installed command
slack-mcp-client

# Or using the main.py script with different AI providers
uv run main.py
```

The client will automatically load the `config.json` file and connect to all configured servers.

### Interactive Chat Commands

- Type `servers` to list all connected servers and their tools
- To use a specific server, prefix your query with the server name: `weather: What's the forecast for New York?`
- Type `quit` to exit the client

## Transport Methods

### stdio Transport

The stdio transport method runs a local command (like `python script.py` or `node script.js`) and communicates with the MCP server through standard input/output.

Configuration parameters:
- `transport`: Set to "stdio"
- `command`: The command to run (e.g., "python", "node")
- `args`: List of command arguments (e.g., ["script.py"])
- `env`: Optional environment variables

### HTTP Transport

The HTTP transport method connects to an MCP server running as an HTTP service.

Configuration parameters:
- `transport`: Set to "http"
- `url`: The URL of the HTTP MCP server

## Development

### Architecture

The client uses a dependency injection pattern to separate concerns:

- `ServerConnectionManager`: Handles all server connections and transport methods
- `AgentManager`: Abstracts different AI providers (Anthropic, OpenAI, Gemini)
- `MCPClient`: Manages the chat interface and query processing

This separation makes the code more maintainable, testable, and flexible.

### Project Structure

```
slack-mcp-client/
├── config.json           # Server configuration
├── main.py               # Entry point script
├── setup.py              # Setup script
├── pyproject.toml        # Project metadata
├── README.md             # Project documentation
├── src/
│   └── mcp_client/ # Main package
│       ├── __init__.py   # Package initialization
│       ├── client.py     # MCPClient implementation
│       ├── server_manager.py # ServerConnectionManager implementation
│       ├── agent_manager.py # AgentManager implementation
│       └── cli.py        # Command-line interface
```

### Using the API

```python
import asyncio
from mcp_client import MCPClient, ServerConnectionManager

async def main():
    # Create server manager and client
    server_manager = ServerConnectionManager()
    
    # Use Anthropic (default)
    client = MCPClient(server_manager, "config.json")
    
    # Or use OpenAI
    # client = MCPClient(server_manager, "config.json", provider="openai")
    
    # Or use Gemini with a specific model
    # client = MCPClient(server_manager, "config.json", provider="gemini", model="gemini-1.5-pro")
    
    # Initialize and connect to servers
    await client.initialize()
    
    # Process queries
    response = await client.process_query("What's the weather like?", "weather")
    print(response)
    
    # Clean up
    await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using Different AI Providers

The client supports multiple AI providers through the `AgentManager` class:

```python
from mcp_client import AgentManager, AnthropicAgentManager, OpenAIAgentManager, GeminiAgentManager

# Create an agent manager for a specific provider
agent = AgentManager.create("anthropic")  # or "openai" or "gemini"

# Or create provider-specific instances directly
anthropic_agent = AnthropicAgentManager(model="claude-3-5-sonnet-20241022")
openai_agent = OpenAIAgentManager(model="gpt-4o")
gemini_agent = GeminiAgentManager(model="gemini-1.5-pro")

# Then use it with MCPClient
client = MCPClient(server_manager, agent_manager=agent)
```

## License

MIT

## References

- [Model Context Protocol (MCP) Python SDK](https://github.com/modelcontextprotocol/python-sdk)
