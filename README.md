# Databricks Foundation Models Chat Interface

Chat with Databricks Foundation Models including Maverick (Llama 3.1 70B) and other available models. Available in two versions:

1. **CLI Version** (`chat_cli.py`) - Simple terminal interface, no Slack required ✅ **Start here!**
2. **Slack Bot** (`app.py`) - Full Slack integration using Bolt for Python

## Features

- 🤖 Chat with Databricks Foundation Models (Maverick, DBRX, Mixtral, etc.)
- 🔄 Switch between different models on the fly
- 💬 Maintains conversation history
- ⚡ Real-time responses
- 🎨 Color-coded terminal output (CLI) or Slack formatting (Bot)

## Available Models

- **Maverick** (Default) - Llama 3.1 70B Instruct
- **Llama 405B** - Llama 3.1 405B Instruct
- **DBRX** - Databricks DBRX Instruct
- **Mixtral** - Mixtral 8x7B Instruct
- **MPT** - MPT 30B Instruct

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Databricks AI Assistant")
4. Select your workspace

### 3. Configure Slack App

#### Bot Token Scopes
Add these OAuth scopes under "OAuth & Permissions":
- `app_mentions:read`
- `chat:write`
- `im:history`
- `im:read`
- `im:write`
- `channels:history`
- `groups:history`
- `mpim:history`

#### Event Subscriptions
Enable events and subscribe to:
- `app_mention`
- `message.im`

#### Socket Mode
1. Enable Socket Mode under "Socket Mode"
2. Generate an App-Level Token with `connections:write` scope

#### Install App
Install the app to your workspace under "Install App"

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-databricks-token-here
```

#### Getting Databricks Credentials:
1. **Host**: Your Databricks workspace URL
2. **Token**: Generate from User Settings → Access Tokens

### 5. Run the App

```bash
python app.py
```

You should see:
```
⚡️ Bolt app is running with Databricks Foundation Models!
```

## Usage

### In Channels
Mention the bot with your question:
```
@Databricks AI What is machine learning?
```

### In Direct Messages
Just type your question:
```
Explain transformers in AI
```

### Commands

- **Get help**: Mention the bot and say "help" or "models"
- **Switch models**: Say "use llama-405b" or "use dbrx"
- **Clear history**: Say "clear" to reset conversation context

### Slash Command (Optional)
Use `/dbchat` followed by your question:
```
/dbchat What are the benefits of using Databricks?
```

## Project Structure

```
bolttest/
├── app.py              # Main Bolt application
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── .env              # Your actual credentials (not committed)
└── README.md         # This file
```

## Troubleshooting

### Bot doesn't respond
- Check that Socket Mode is enabled
- Verify event subscriptions are configured
- Ensure the bot is invited to the channel (`/invite @YourBot`)

### Databricks errors
- Verify your Databricks token is valid
- Check that Foundation Model endpoints are available in your workspace
- Ensure your workspace has access to Foundation Models

### Permission errors
- Review bot token scopes in Slack app settings
- Reinstall the app after adding new scopes

## Development

To add more models, update the `AVAILABLE_MODELS` dictionary in `app.py`:

```python
AVAILABLE_MODELS = {
    "your-model-name": "databricks-model-endpoint-id",
}
```

## License

MIT
