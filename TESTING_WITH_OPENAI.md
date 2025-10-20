# Testing with OpenAI

Want to test the Slack bot in your personal Slack workspace but don't have access to Databricks Foundation Models? No problem! The app uses the OpenAI-compatible API format, so you can easily switch to using actual OpenAI models.

## Why This Works

Both implementations use the **exact same OpenAI client syntax**:

```python
response = client.chat.completions.create(
    model=model_id,
    messages=messages,
    max_tokens=1000,
    temperature=0.7
)
```

The only difference is:
- **Databricks**: `base_url` points to your Databricks workspace
- **OpenAI**: `base_url` uses the default OpenAI endpoint

## Setup for OpenAI Testing

### 1. Get an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 2. Update Your `.env` File

```env
# Set mode to openai
MODE=openai

# Add your OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Slack Configuration (for Slack bot)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# Databricks config (comment out when using OpenAI)
# DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
# DATABRICKS_TOKEN=dapi...
```

### 3. Run the App

#### For CLI Testing:
```bash
source venv/bin/activate
python chat_cli_openai.py
```

#### For Slack Bot Testing:
```bash
source venv/bin/activate
python app_openai.py
```

## Available OpenAI Models

When running in OpenAI mode, you'll have access to:

1. **GPT-4o** - Latest and most capable
2. **GPT-4o Mini** - Faster and more affordable
3. **GPT-4 Turbo** - Previous generation flagship
4. **GPT-3.5 Turbo** - Fast and cost-effective

## Switching Between Databricks and OpenAI

Just change the `MODE` in your `.env` file:

```env
# For Databricks
MODE=databricks
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# For OpenAI
MODE=openai
OPENAI_API_KEY=sk-...
```

## File Differences

| Use Case | CLI Script | Slack Bot | Config |
|----------|-----------|-----------|--------|
| **Databricks Only** | `chat_cli.py` | `app.py` | DATABRICKS_HOST + TOKEN |
| **Flexible (DB or OpenAI)** | `chat_cli_openai.py` | `app_openai.py` | MODE + credentials |

## Cost Considerations

**OpenAI Pricing** (as of 2024):
- GPT-4o: ~$0.005 per 1K input tokens
- GPT-4o Mini: ~$0.00015 per 1K input tokens
- GPT-3.5 Turbo: ~$0.0005 per 1K input tokens

**Databricks**:
- Pricing varies by workspace and model
- Often bundled with your Databricks subscription

## Example: Testing Slack Bot with OpenAI

1. Create a test Slack workspace (free at slack.com)
2. Set up your Slack app following the main README
3. Configure `.env` with OpenAI credentials:
   ```env
   MODE=openai
   OPENAI_API_KEY=sk-your-key
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_APP_TOKEN=xapp-your-token
   ```
4. Run: `python app_openai.py`
5. Test in Slack by mentioning your bot!

## Code Comparison

The core API call is **identical** in both:

### Databricks Version
```python
client = OpenAI(
    api_key=os.environ.get("DATABRICKS_TOKEN"),
    base_url=f"{os.environ.get('DATABRICKS_HOST')}/serving-endpoints"
)

response = client.chat.completions.create(
    model="databricks-llama-4-maverick",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### OpenAI Version
```python
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
    # base_url defaults to OpenAI's endpoint
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Same method, same syntax, different endpoint!** 🎯

## Benefits of This Approach

✅ **Easy Testing** - Test Slack integration without Databricks access
✅ **Portability** - Same code works with multiple providers
✅ **Flexibility** - Switch providers with one env variable
✅ **Standard API** - Uses industry-standard OpenAI format
✅ **Future-Proof** - Easy to add more providers (Azure OpenAI, Anthropic, etc.)

## Troubleshooting

### "Invalid API key" error with OpenAI
- Make sure your key starts with `sk-`
- Verify it's active at https://platform.openai.com/api-keys

### Models not responding
- Check you have credits in your OpenAI account
- Verify the model name is correct (case-sensitive)

### Slack bot not responding
- Ensure `MODE=openai` is set in `.env`
- Check logs for authentication errors
- Verify SLACK_BOT_TOKEN and SLACK_APP_TOKEN are correct
