# Slack Bot

A simple Slack bot that responds with "hi!" when mentioned. This bot uses Socket Mode to connect to Slack.

## Prerequisites

- Python 3.13 or higher
- A Slack workspace where you have permissions to add apps
- Slack app with appropriate permissions

## Setup

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click "Create New App"
2. Choose "From scratch" and give your app a name and select your workspace
3. Navigate to "Socket Mode" in the sidebar and enable it
   - Note the App-Level Token that starts with `xapp-`
4. Go to "OAuth & Permissions" in the sidebar
   - Under "Bot Token Scopes", add the following permissions:
     - `app_mentions:read` - To read when the bot is mentioned
     - `chat:write` - To send messages
   - Install the app to your workspace
   - Note the Bot User OAuth Token that starts with `xoxb-`
5. Go to "Event Subscriptions" in the sidebar
   - Enable events
   - Under "Subscribe to bot events", add the `app_mention` event
   - Save changes

### 2. Configure Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

Replace `xoxb-your-bot-token` with your Bot User OAuth Token and `xapp-your-app-token` with your App-Level Token.

## Running the Bot

Run the bot using the following command from the project root:

```bash
python main.py
```

## Usage

Once the bot is running, you can mention it in any channel it's been added to:

```
@YourBotName Hello!
```

The bot will respond with:

```
hi! @YourUsername
```

## Troubleshooting

- Make sure both `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are correctly set in your `.env` file
- Ensure the bot has been added to the channel where you're mentioning it
- Check the logs for any error messages
