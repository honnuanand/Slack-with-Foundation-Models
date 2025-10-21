# Complete Slack App Setup Guide

This guide provides step-by-step instructions for setting up a Slack app to work with the Databricks Foundation Models bot.

## Prerequisites

- Admin access to a Slack workspace
- Databricks workspace with Foundation Models enabled
- Databricks personal access token

## Step 1: Create a New Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter your app details:
   - **App Name**: `PromptBot` (or your preferred name)
   - **Pick a workspace**: Select your Slack workspace
5. Click **"Create App"**

## Step 2: Configure OAuth & Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"** and add ALL of these scopes:

### Required Bot Token Scopes

- ✅ `app_mentions:read` - Read messages that mention your app
- ✅ `chat:write` - Send messages as the bot
- ✅ `im:history` - View messages in direct messages
- ✅ `im:read` - View basic info about direct messages
- ✅ `im:write` - Send messages in direct messages
- ✅ `channels:history` - View messages in public channels
- ✅ `groups:history` - View messages in private channels
- ✅ `mpim:history` - View messages in group direct messages

**Important:** `chat:write` is critical - without it, the bot can receive messages but cannot respond!

## Step 3: Enable Socket Mode

Socket Mode allows your app to connect without a public URL.

1. In the left sidebar, click **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to **ON**
3. When prompted, create an app-level token:
   - **Token Name**: `socket-token`
   - **Scope**: Select `connections:write`
   - Click **"Generate"**
4. **COPY THE TOKEN** (starts with `xapp-`)
   - Save this as `SLACK_APP_TOKEN` in your `.env` file
5. Click **"Done"**

## Step 4: Configure Event Subscriptions

1. In the left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **ON**
3. Under **"Subscribe to bot events"**, click **"Add Bot User Event"**
4. Add these events:
   - `app_mention` - Listen for @mentions of your bot
   - `message.im` - Listen for direct messages
5. Click **"Save Changes"** at the bottom

## Step 5: Configure App Home

1. In the left sidebar, click **"App Home"**
2. Scroll to **"Your App's Presence in Slack"**:
   - **Display Name (Bot Name)**: PromptBot
   - **Default username**: promptbot (lowercase)
3. Scroll to **"Show Tabs"** section:
   - **Home Tab**: Toggle ON ✅
   - **Messages Tab**: Toggle ON ✅
   - **Important**: Check the box below Messages Tab:
     - ✅ "Allow users to send Slash commands and messages from the messages tab"
4. Click **"Save Changes"**

**Note:** Even with Messages Tab enabled, direct messages may not work due to Slack limitations. Use channel mentions instead.

## Step 6: Install App to Workspace

1. In the left sidebar, click **"Install App"**
2. Click **"Install to Workspace"**
3. Review the permissions and click **"Allow"**
4. **COPY THE BOT TOKEN** (starts with `xoxb-`)
   - Save this as `SLACK_BOT_TOKEN` in your `.env` file

## Step 7: Configure Environment Variables

Create or update your `.env` file with the tokens:

```env
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...your-databricks-token

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
```

## Step 8: Run the Bot

1. Install dependencies:
   ```bash
   pip install slack-bolt openai python-dotenv
   ```

2. Run the bot:
   ```bash
   python app.py
   ```

3. You should see:
   ```
   INFO:__main__:⚡️ Bolt app is running with Databricks Foundation Models!
   INFO:slack_bolt.App:⚡️ Bolt app is running!
   ```

## Step 9: Test the Bot

### In a Channel (Recommended)

1. Go to any channel in your Slack workspace
2. Invite the bot: `/invite @PromptBot`
3. Send a message mentioning the bot:
   ```
   @PromptBot What is Python?
   ```

### In Direct Messages

**Note:** Direct messages may show "Sending messages to this app has been turned off" even when properly configured. This is a known Slack limitation. Use channel mentions instead.

### Available Commands

- `@PromptBot help` - Show available models and commands
- `@PromptBot models` - List available Foundation Models
- `@PromptBot use claude-opus` - Switch to a different model
- `@PromptBot clear` - Clear conversation history

## Troubleshooting

### Bot doesn't respond

1. **Check Socket Mode**: Ensure Socket Mode is enabled
2. **Check Scopes**: Verify all required scopes are added, especially `chat:write`
3. **Reinstall App**: After adding scopes, always reinstall the app
4. **Check Logs**: Look for errors in your terminal

### "missing_scope" error in logs

This means you're missing required permissions:
1. Add the missing scope in OAuth & Permissions
2. **Reinstall the app** (critical!)
3. Restart the bot

### "Sending messages to this app has been turned off"

This is a Slack limitation with the Messages Tab. Solutions:
1. Use channel mentions instead (@PromptBot)
2. Create a private channel for bot interactions
3. Use slash commands if configured

### Model not found errors

Ensure your `AVAILABLE_MODELS` dictionary in `app.py` contains valid model IDs for your Databricks workspace. Check available models with:
```bash
databricks serving-endpoints list
```

## Available Models (FE VM Workspace)

The bot is configured with these Databricks Foundation Models:

- `maverick` → Llama 4 Maverick
- `llama-70b` → Llama 3.3 70B Instruct
- `llama-405b` → Llama 3.1 405B Instruct
- `llama-8b` → Llama 3.1 8B Instruct
- `claude-sonnet` → Claude Sonnet 4.5
- `claude-opus` → Claude Opus 4.1
- `gpt-120b` → GPT OSS 120B

## Security Notes

- Never commit your `.env` file with real tokens
- Rotate tokens periodically
- Use environment variables for all sensitive data
- Consider implementing rate limiting for production use

## Additional Resources

- [Slack Bolt for Python Documentation](https://slack.dev/bolt-python/)
- [Slack API Documentation](https://api.slack.com/)
- [Databricks Foundation Models](https://docs.databricks.com/en/machine-learning/foundation-models/index.html)