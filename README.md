# Slack with Foundation Models

Connect Slack to Databricks and other LLM providers that are compatible with the OpenAI API format for connectivity.

This project provides both a **Slack bot** and **CLI interface** to chat with Foundation Models from providers like Databricks, OpenAI, and any other service that supports the OpenAI-compatible API format.

## 🎯 What This Does

- **Slack Integration**: Chat with Foundation Models directly in Slack using Bolt for Python
- **CLI Interface**: Terminal-based chat interface for quick testing and development
- **OpenAI-Compatible**: Uses the standard OpenAI API format, making it easy to switch between providers
- **Flexible Provider Support**: Works with Databricks Foundation Models, OpenAI, or any OpenAI-compatible service

## 🚀 Quick Start

Choose your path:

1. **CLI Only** → See [QUICKSTART.md](QUICKSTART.md) or [CLI_README.md](CLI_README.md)
2. **Slack Bot with Databricks** → Continue below
3. **Testing with OpenAI** → See [TESTING_WITH_OPENAI.md](TESTING_WITH_OPENAI.md)
4. **Not sure which file to use?** → See [WHICH_FILE_TO_USE.md](WHICH_FILE_TO_USE.md)

## ✨ Features

- 🤖 **Multiple Providers**: Databricks, OpenAI, or any OpenAI-compatible LLM service
- 🔄 **Model Switching**: Switch between different models on the fly
- 💬 **Conversation History**: Maintains context across multiple turns
- ⚡ **Real-time Responses**: Fast, streaming responses
- 🎨 **Color-Coded Output**: Enhanced CLI experience with color formatting
- 📱 **Slack Integration**: Full Slack bot with mentions, DMs, and slash commands
- 🔌 **Standard API**: Uses OpenAI's Chat Completions API format

## 🛠️ Available Implementations

| File | Interface | Providers | Best For |
|------|-----------|-----------|----------|
| `chat_cli.py` | Terminal | Databricks only | Quick local testing with Databricks |
| `chat_cli_openai.py` | Terminal | Databricks OR OpenAI | Flexible development/testing |
| `app.py` | Slack | Databricks only | Production Slack bot with Databricks |
| `app_openai.py` | Slack | Databricks OR OpenAI | Testing Slack bot without Databricks |

## 📋 Setup - Slack Bot with Databricks

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "AI Assistant")
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

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# For Databricks
MODE=databricks
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# For Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

**Getting Databricks Credentials:**
1. **Host**: Your Databricks workspace URL
2. **Token**: Generate from User Settings → Developer → Access Tokens

### 5. Run the Slack Bot

```bash
source venv/bin/activate
python app.py
```

You should see:
```
⚡️ Bolt app is running with Databricks Foundation Models!
```

## 💡 Usage

### In Slack Channels
Mention the bot with your question:
```
@AI Assistant What is machine learning?
```

### In Direct Messages
Just type your question:
```
Explain transformers in AI
```

### Commands
- **Get help**: Say "help" or "models"
- **Switch models**: Say "use llama-70b" or "use claude-sonnet"
- **Clear history**: Say "clear" to reset conversation context

## 🔧 Testing with OpenAI Instead

Want to test the Slack bot without Databricks access? You can use OpenAI instead!

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Update your `.env`:
   ```env
   MODE=openai
   OPENAI_API_KEY=sk-your-key-here
   ```
3. Run: `python app_openai.py`

See [TESTING_WITH_OPENAI.md](TESTING_WITH_OPENAI.md) for complete instructions.

## 🏗️ How It Works - The OpenAI API Format

All implementations use the **OpenAI Chat Completions API** format:

```python
from openai import OpenAI

# For Databricks
client = OpenAI(
    api_key=DATABRICKS_TOKEN,
    base_url=f"{DATABRICKS_HOST}/serving-endpoints"
)

# For OpenAI
client = OpenAI(
    api_key=OPENAI_API_KEY
)

# Same API call for both!
response = client.chat.completions.create(
    model="model-id",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=1000,
    temperature=0.7
)
```

**Same syntax, different endpoint** - that's the power of the OpenAI-compatible API format!

## 📚 Available Models

### Databricks Foundation Models
- Llama 4 Maverick
- Llama 3.3 70B Instruct
- Llama 3.1 405B Instruct
- Claude Sonnet 4.5
- Claude Opus 4.1
- GPT OSS 120B
- And more...

### OpenAI Models
- GPT-4o
- GPT-4o Mini
- GPT-4 Turbo
- GPT-3.5 Turbo

*The actual available models depend on your workspace/account configuration*

## 📂 Project Structure

```
Slack-with-Foundation-Models/
├── app.py                    # Slack bot (Databricks only)
├── app_openai.py             # Slack bot (flexible provider)
├── chat_cli.py               # CLI (Databricks only)
├── chat_cli_openai.py        # CLI (flexible provider)
├── example_usage.py          # Simple API example
├── requirements.txt          # All dependencies
├── requirements-cli.txt      # CLI-only dependencies
├── .env.example              # Environment template
├── README.md                 # This file
├── CLI_README.md             # CLI-specific documentation
├── QUICKSTART.md             # Quick start guide
├── TESTING_WITH_OPENAI.md    # OpenAI testing guide
└── WHICH_FILE_TO_USE.md      # Decision guide
```

## 🔍 Troubleshooting

### Slack Bot Issues
- **Bot doesn't respond**: Check Socket Mode is enabled and bot is invited to channel
- **Permission errors**: Review bot token scopes and reinstall app
- **Authentication errors**: Verify SLACK_BOT_TOKEN and SLACK_APP_TOKEN

### Databricks Issues
- **Invalid credentials**: Check DATABRICKS_HOST and DATABRICKS_TOKEN
- **Model not found**: Verify the model endpoint exists in your workspace
- **Access denied**: Ensure workspace has Foundation Models enabled

### OpenAI Issues
- **Invalid API key**: Verify key at https://platform.openai.com/api-keys
- **Rate limits**: Check your usage limits and billing

## 🎓 Learn More

- [Databricks Foundation Models Documentation](https://docs.databricks.com/en/machine-learning/foundation-models/index.html)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Slack Bolt for Python](https://slack.dev/bolt-python/)

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! This project demonstrates how to:
- Build Slack bots with Foundation Models
- Use OpenAI-compatible APIs
- Switch between different LLM providers
- Maintain conversation context
- Handle streaming responses

Feel free to extend it with additional providers or features!
