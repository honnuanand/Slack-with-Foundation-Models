# Databricks Foundation Models CLI Chat Interface

A simple command-line chat interface for interacting with Databricks Foundation Models using the OpenAI-compatible API format.

## Overview

This CLI tool allows you to chat with various Databricks Foundation Models directly from your terminal, including:
- Llama 4 Maverick
- Llama 3.3 70B Instruct
- Llama 3.1 405B Instruct
- Claude Sonnet 4.5
- Claude Opus 4.1
- And more!

## Key Features

- **OpenAI-Compatible API**: Uses standard OpenAI Python client syntax
- **Multiple Models**: Switch between different foundation models on the fly
- **Conversation History**: Maintains context across multiple turns
- **Color-Coded Output**: Easy-to-read terminal interface
- **Simple Setup**: Works with your existing Databricks CLI configuration

## How It Works - OpenAI Syntax

The application uses the OpenAI Python client to connect to Databricks Foundation Models:

### Client Initialization
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DATABRICKS_TOKEN"),
    base_url=f"{os.environ.get('DATABRICKS_HOST')}/serving-endpoints"
)
```

### Making API Calls
```python
response = client.chat.completions.create(
    model="databricks-meta-llama-3-3-70b-instruct",
    messages=[
        {"role": "user", "content": "What is machine learning?"}
    ],
    max_tokens=1000,
    temperature=0.7
)

# Extract the response
answer = response.choices[0].message.content
```

This is the **exact same syntax** you would use with OpenAI's API - just with a different `base_url` pointing to your Databricks workspace!

### Code Location

The OpenAI API call is in `chat_cli.py`:
- **Lines 75-78**: Client initialization with Databricks endpoint
- **Lines 51-56**: API call using `client.chat.completions.create()`
- **Line 58**: Extract response from `response.choices[0].message.content`

## Prerequisites

- Python 3.7+
- Databricks workspace with Foundation Models enabled
- Databricks personal access token

## Quick Start

### 1. Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements-cli.txt
```

This installs:
- `openai` - OpenAI Python client (works with Databricks!)
- `python-dotenv` - For loading environment variables

### 2. Configure Credentials

#### Option A: Using Existing Databricks CLI (Easiest)

If you already have the Databricks CLI configured:

```bash
# Create a personal access token
databricks tokens create --comment "chat-cli-app" --lifetime-seconds 31536000

# The token will be displayed - copy it
```

Then create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef...
```

#### Option B: Manual Setup

1. Log into your Databricks workspace
2. Go to **User Settings** → **Developer** → **Access Tokens**
3. Click **Generate New Token**
4. Copy the token and add it to your `.env` file

### 3. Run the Chat Interface

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the CLI
python chat_cli.py
```

## Usage

### Starting a Chat

When you run the application, you'll see:

```
==============================================================
  Databricks Foundation Models - Chat Interface
==============================================================

Available Models:
  1. Llama 4 Maverick
  2. Llama 3.3 70B Instruct
  3. Llama 3.1 405B Instruct
  4. Llama 3.1 8B Instruct
  5. Claude Sonnet 4.5
  6. Claude Opus 4.1
  7. GPT OSS 120B

Select a model (1-7) [default: 1 - Llama 4 Maverick]:
```

Press Enter to use the default (Llama 4 Maverick) or type a number to select another model.

### Available Commands

- **Type your question** - Just type and press Enter to chat
- **`clear`** - Reset conversation history
- **`switch`** - Change to a different model
- **`quit`** or `exit`** - Exit the application

### Example Session

```
You: What is Databricks?