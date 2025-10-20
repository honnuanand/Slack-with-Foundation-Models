# Quick Start - CLI Version (No Slack Required!)

This guide will help you get started with the command-line chat interface in minutes.

## Step 1: Install Dependencies

```bash
pip install -r requirements-cli.txt
```

This only installs:
- `openai` - OpenAI Python client (works with Databricks!)
- `python-dotenv` - For loading environment variables

**No Slack dependencies required!**

## Step 2: Configure Databricks Credentials

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your Databricks credentials:

```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-databricks-token
```

### Getting Your Databricks Token:

1. Log into your Databricks workspace
2. Click your user profile (top right)
3. Go to **Settings** → **Developer** → **Access Tokens**
4. Click **Manage** → **Generate New Token**
5. Copy the token and paste it in your `.env` file

## Step 3: Run the Chat Interface

```bash
python chat_cli.py
```

## Usage

When you start the app, you'll see:

```
==============================================================
  Databricks Foundation Models - Chat Interface
==============================================================

Available Models:
  1. Maverick (Llama 3.1 70B)
  2. Llama 3.1 405B
  3. DBRX Instruct
  4. Mixtral 8x7B
  5. MPT 30B

Select a model (1-5) [default: 1 - Maverick]:
```

Just press Enter to use Maverick, or type a number to select another model.

### Commands

- Type your question and press Enter to chat
- Type `clear` to reset conversation history
- Type `switch` to change models
- Type `quit` or `exit` to leave

## Example Conversation

```
You: What is machine learning?