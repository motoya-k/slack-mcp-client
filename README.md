# Slack MCP Client

A Python client for connecting Slack to Model Context Protocol (MCP) servers, enabling AI-powered interactions with various tools and services.

## Features

- Connect to multiple MCP servers simultaneously
- Support for different transport methods (stdio, HTTP)
- Manage server connections with JSON configuration
- Support for multiple AI providers (Anthropic, OpenAI, Groq, Gemini)
- Slack bot integration with Socket Mode
- Interactive chat interface with AI
- Support for both Python and JavaScript MCP servers
- Clean architecture with dependency injection

## Installation

```bash
uv venv
uv sync
```

## Configuration

### Environment Variables

Create a `.env` file based on the provided `.env.example`:

```bash
# Copy the example file
cp .env.example .env

# Edit the file with your credentials
vi .env
```

Required environment variables:

- `SLACK_BOT_TOKEN`: Your Slack bot token (xoxb-...)
- `SLACK_APP_TOKEN`: Your Slack app-level token (xapp-...)
- At least one LLM API key (based on your chosen model):
  - `ANTHROPIC_API_KEY`: For Claude models
  - `OPENAI_API_KEY`: For GPT models
  - `GROQ_API_KEY`: For Llama models
  - `GEMINI_API_KEY`: For Gemini models

### Server Configuration

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

## Usage

Run the Slack MCP Bot:

```bash
# Using the main.py script
python main.py
```

The bot will connect to Slack using Socket Mode and initialize all configured MCP servers.

## Testing with ngrok

To test your Slack bot with a public URL (required for some Slack features), you can use ngrok:

### 1. Install ngrok

```bash
# macOS with Homebrew
brew install ngrok

# Or download from https://ngrok.com/download
```

### 2. Set up ngrok authentication

```bash
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

### 3. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" > "From scratch"
3. Name your app and select your workspace
4. Under "Basic Information", note your "App Credentials"
5. Under "Socket Mode", enable Socket Mode and create an app-level token with `connections:write` scope
   - Save this token as `SLACK_APP_TOKEN` in your `.env` file
6. Under "OAuth & Permissions":
   - Add the following Bot Token Scopes:
     - `app_mentions:read`
     - `channels:history`
     - `chat:write`
     - `im:history`
     - `im:read`
     - `im:write`
   - Install the app to your workspace
   - Save the Bot User OAuth Token as `SLACK_BOT_TOKEN` in your `.env` file
7. Under "Event Subscriptions":
   - Enable events
   - Subscribe to bot events:
     - `app_mention`
     - `message.im`
8. Under "App Home", enable the Home Tab

### 4. Start your Slack MCP Bot

```bash
python main.py
```

### 5. (Optional) Use ngrok for HTTP-based MCP servers

If you have HTTP-based MCP servers running locally, you can expose them with ngrok:

```bash
# Expose a local server running on port 8000
ngrok http 8000
```

Then update your `config.json` to use the ngrok URL:

```json
{
  "example_http": {
    "transport": "http",
    "url": "https://your-ngrok-url.ngrok.io"
  }
}
```

## Development

### Architecture

The client uses a modular architecture:

- `slack_bot/config.py`: Manages configuration and environment variables
- `slack_bot/llm_client.py`: Handles communication with different LLM providers
- `slack_bot/server.py`: Manages MCP server connections and tool execution
- `slack_bot/bot.py`: Integrates with Slack API and handles message processing
- `main.py`: Entry point that ties everything together

### Project Structure

```
slack-mcp-client/
├── config.json           # Server configuration
├── main.py               # Entry point script
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Example environment variables
├── pyproject.toml        # Project metadata
├── README.md             # Project documentation
├── src/
│   ├── mcp_client/       # Original MCP client package
│   └── slack_bot/        # Slack bot implementation
│       ├── __init__.py   # Package initialization
│       ├── config.py     # Configuration management
│       ├── llm_client.py # LLM client implementation
│       ├── server.py     # Server management
│       └── bot.py        # Slack bot implementation
```

## License

MIT
