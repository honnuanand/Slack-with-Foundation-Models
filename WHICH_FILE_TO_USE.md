# Which File Should I Use?

Quick guide to choosing the right script for your use case.

## 🎯 Decision Tree

```
Do you need a Slack bot?
├─ NO → Use CLI scripts
│  ├─ Only Databricks? → chat_cli.py
│  └─ Want flexibility? → chat_cli_openai.py (set MODE in .env)
│
└─ YES → Use Slack bot scripts
   ├─ Only Databricks? → app.py
   └─ Want flexibility? → app_openai.py (set MODE in .env)
```

## 📋 File Comparison

| File | Interface | Providers | Switching | Best For |
|------|-----------|-----------|-----------|----------|
| `chat_cli.py` | Terminal | Databricks only | ❌ No | Production use with Databricks |
| `chat_cli_openai.py` | Terminal | Databricks OR OpenAI | ✅ Yes (via MODE) | Testing/development |
| `app.py` | Slack | Databricks only | ❌ No | Production Slack bot with Databricks |
| `app_openai.py` | Slack | Databricks OR OpenAI | ✅ Yes (via MODE) | Testing Slack bot without Databricks |

## 🚀 Common Scenarios

### Scenario 1: "I want to test locally with Databricks"
```bash
# Use the simple Databricks-only CLI
source venv/bin/activate
python chat_cli.py
```

**Requirements:**
- `.env` with DATABRICKS_HOST and DATABRICKS_TOKEN

---

### Scenario 2: "I want to test Slack bot without Databricks access"
```bash
# Use the flexible Slack bot with OpenAI
source venv/bin/activate
python app_openai.py
```

**Requirements:**
- Set `MODE=openai` in `.env`
- Add OPENAI_API_KEY to `.env`
- Add Slack tokens (SLACK_BOT_TOKEN, SLACK_APP_TOKEN)

---

### Scenario 3: "I want flexibility to switch between Databricks and OpenAI"
```bash
# Use the flexible CLI
source venv/bin/activate
python chat_cli_openai.py
```

**Requirements:**
- Set `MODE=databricks` or `MODE=openai` in `.env`
- Provide appropriate credentials based on MODE

---

### Scenario 4: "Production Databricks Slack bot"
```bash
# Use the production Slack bot
source venv/bin/activate
python app.py
```

**Requirements:**
- `.env` with DATABRICKS_HOST, DATABRICKS_TOKEN
- Slack tokens configured

---

## 📝 Configuration Files

### For Databricks-only scripts (`chat_cli.py`, `app.py`)
```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# Only for app.py
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

### For flexible scripts (`*_openai.py`)
```env
# Set your mode
MODE=databricks   # or MODE=openai

# Databricks config
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# OpenAI config (only needed if MODE=openai)
OPENAI_API_KEY=sk-...

# Slack config (only for app_openai.py)
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

## 🔑 Key Differences

### Architecture
All scripts use the **same OpenAI client syntax**:
```python
response = client.chat.completions.create(
    model=model_id,
    messages=messages
)
```

The difference is only in the client initialization:

**Databricks:**
```python
client = OpenAI(
    api_key=DATABRICKS_TOKEN,
    base_url=f"{DATABRICKS_HOST}/serving-endpoints"
)
```

**OpenAI:**
```python
client = OpenAI(
    api_key=OPENAI_API_KEY
    # base_url defaults to OpenAI
)
```

## 💡 Recommendations

### For Development/Testing
✅ Use `*_openai.py` scripts
- More flexible
- Easy to switch providers
- Test without Databricks access

### For Production
✅ Use `chat_cli.py` or `app.py`
- Simpler code
- Fewer dependencies
- Clearer intent
- No mode switching confusion

## 🆘 Quick Help

**Script won't start?**
- Check you have the right credentials in `.env`
- For `*_openai.py`: Make sure `MODE` is set correctly
- Activate virtual environment: `source venv/bin/activate`

**Wrong models showing up?**
- Check `MODE` setting in `.env`
- Verify you're running the right script

**Want to switch providers?**
- For `*_openai.py`: Just change `MODE` in `.env`
- For `chat_cli.py` or `app.py`: Use the `*_openai.py` version instead
