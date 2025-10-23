#!/usr/bin/env python3
"""
Slack Bot with Databricks Foundation Models using Socket Mode + Dashboard
Based on: https://github.com/slack-samples/bolt-python-assistant-template
"""

import os
import logging
from typing import List, Dict
from dotenv import load_dotenv
import openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import threading
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "fe-vm-leaps-fe.cloud.databricks.com")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
PORT = int(os.environ.get("PORT", 8000))

logger.info(f"Config - Databricks: {DATABRICKS_HOST}")
logger.info(f"Slack Bot Token: {'✓' if SLACK_BOT_TOKEN else '✗'}")
logger.info(f"Slack App Token: {'✓' if SLACK_APP_TOKEN else '✗'}")

# Initialize Slack app and FastAPI
slack_app = App(token=SLACK_BOT_TOKEN)
fastapi_app = FastAPI(title="PromptBot Dashboard", version="1.0.0")

# Available models
AVAILABLE_MODELS = {
    "maverick": "databricks-llama-4-maverick",
    "llama-70b": "databricks-meta-llama-3-3-70b-instruct",
    "llama-405b": "databricks-meta-llama-3-1-405b-instruct",
    "llama-8b": "databricks-meta-llama-3-1-8b-instruct",
    "claude-sonnet": "databricks-claude-sonnet-4-5",
    "claude-opus": "databricks-claude-opus-4-1",
    "gpt-120b": "databricks-gpt-oss-120b",
}

# Metrics tracking
class Metrics:
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.model_usage = {model: 0 for model in AVAILABLE_MODELS.keys()}
        self.unique_users = set()
        self.start_time = datetime.now()

metrics = Metrics()

# User preferences and history
user_model_preferences = {}
conversation_history = {}

DEFAULT_SYSTEM_CONTENT = """You are a helpful AI assistant powered by Databricks Foundation Models.
You can answer questions, help with coding, explain concepts, and assist with various tasks.
Be concise, accurate, and friendly."""


def call_llm(
    messages_in_thread: List[Dict[str, str]],
    model_id: str = "databricks-llama-4-maverick",
    system_content: str = DEFAULT_SYSTEM_CONTENT,
):
    """Call Databricks Foundation Model using OpenAI-compatible API"""
    openai_client = openai.OpenAI(
        api_key=DATABRICKS_TOKEN,
        base_url=f"https://{DATABRICKS_HOST}/serving-endpoints"
    )

    messages = [{"role": "system", "content": system_content}]
    messages.extend(messages_in_thread)

    response = openai_client.chat.completions.create(
        model=model_id,
        messages=messages,
        stream=True,
        max_tokens=1000,
        temperature=0.7
    )

    return response


def get_model_for_user(user_id: str) -> tuple[str, str]:
    """Get the model name and ID for a user"""
    model_name = user_model_preferences.get(user_id, "maverick")
    model_id = AVAILABLE_MODELS[model_name]
    return model_name, model_id


@slack_app.event("app_mention")
def handle_app_mention(event, say, client):
    """Handle @mentions of the bot"""
    logger.info(f"App mention: {event}")

    user_id = event["user"]
    channel_id = event["channel"]
    text = event["text"]
    thread_ts = event.get("thread_ts") or event["ts"]

    # Track metrics
    metrics.total_requests += 1
    metrics.unique_users.add(user_id)

    # Remove bot mention from text
    text = text.split(">", 1)[-1].strip() if ">" in text else text.strip()

    # Handle commands
    if "help" in text.lower() or text == "":
        model_name, model_id = get_model_for_user(user_id)
        models_list = "\n".join([f"• `@PromptBot use {k}` - {v}" for k, v in AVAILABLE_MODELS.items()])
        help_text = f"""*PromptBot Help* 🤖

*Current Model:* {model_name} ({model_id})
*Dashboard:* https://slack-foundation-bot-2409307273843806.aws.databricksapps.com

*Commands:*
• `@PromptBot help` - Show this message
• `@PromptBot models` - List all models
• `@PromptBot use [model-name]` - Switch models
• `@PromptBot clear` - Clear history

*Available Models:*
{models_list}"""
        say(text=help_text, thread_ts=thread_ts)
        return

    if "models" in text.lower():
        model_name, model_id = get_model_for_user(user_id)
        models_list = "\n".join([f"• *{k}*: {v}" for k, v in AVAILABLE_MODELS.items()])
        models_text = f"""*Available Models:*

{models_list}

*Current:* {model_name} ({model_id})

Use `@PromptBot use [model-name]` to switch."""
        say(text=models_text, thread_ts=thread_ts)
        return

    if "clear" in text.lower():
        model_name, _ = get_model_for_user(user_id)
        if thread_ts in conversation_history:
            del conversation_history[thread_ts]
        say(text=f"✅ History cleared! (Using: {model_name})", thread_ts=thread_ts)
        return

    if "use " in text.lower():
        for model_name in AVAILABLE_MODELS.keys():
            if model_name in text.lower():
                user_model_preferences[user_id] = model_name
                model_id = AVAILABLE_MODELS[model_name]
                metrics.model_usage[model_name] += 1
                say(text=f"✅ Switched to {model_name} ({model_id})", thread_ts=thread_ts)
                return
        say(text="❌ Model not found. Use `@PromptBot models` to see options.", thread_ts=thread_ts)
        return

    # Get conversation history
    if thread_ts not in conversation_history:
        conversation_history[thread_ts] = []

    # Add user message to history
    conversation_history[thread_ts].append({"role": "user", "content": text})

    # Get model for user
    model_name, model_id = get_model_for_user(user_id)
    metrics.model_usage[model_name] += 1

    try:
        # Post initial message
        result = client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"_Thinking with {model_name}..._"
        )
        message_ts = result["ts"]

        # Call LLM and stream response
        returned_message = call_llm(conversation_history[thread_ts], model_id)

        # Collect streamed response
        full_response = ""
        token_count = 0

        # Loop over OpenAI chat completion streamed chunk
        for chunk in returned_message:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = getattr(chunk.choices[0], "delta", None)
                if delta and hasattr(delta, "content"):
                    content = delta.content
                    if content:
                        full_response += content
                        token_count += 1

        # Update metrics
        metrics.total_tokens += token_count

        # Update conversation history
        conversation_history[thread_ts].append({"role": "assistant", "content": full_response})

        # Update message with full response
        final_text = f"{full_response}\n\n_Using {model_name} ({model_id})_"
        client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=final_text
        )

    except Exception as e:
        logger.error(f"Error calling LLM: {e}", exc_info=True)
        say(text=f"❌ Error: {str(e)}", thread_ts=thread_ts)


@slack_app.event("message")
def handle_message(event, say, client):
    """Handle direct messages to the bot"""
    logger.info(f"Message event: {event}")

    # Ignore bot messages
    if event.get("bot_id"):
        return

    # Only handle DMs (channel_type == "im")
    if event.get("channel_type") != "im":
        return

    user_id = event["user"]
    channel_id = event["channel"]
    text = event["text"]
    thread_ts = event.get("thread_ts") or event["ts"]

    # Track metrics
    metrics.total_requests += 1
    metrics.unique_users.add(user_id)

    # Handle commands (same as app_mention)
    if "help" in text.lower():
        model_name, model_id = get_model_for_user(user_id)
        models_list = "\n".join([f"• `use {k}` - {v}" for k, v in AVAILABLE_MODELS.items()])
        help_text = f"""*PromptBot Help* 🤖

*Current Model:* {model_name} ({model_id})
*Dashboard:* https://slack-foundation-bot-2409307273843806.aws.databricksapps.com

*Commands:*
• `help` - Show this message
• `models` - List all models
• `use [model-name]` - Switch models
• `clear` - Clear history

*Available Models:*
{models_list}"""
        say(text=help_text, channel=channel_id)
        return

    if "models" in text.lower():
        model_name, model_id = get_model_for_user(user_id)
        models_list = "\n".join([f"• *{k}*: {v}" for k, v in AVAILABLE_MODELS.items()])
        models_text = f"""*Available Models:*

{models_list}

*Current:* {model_name} ({model_id})

Use `use [model-name]` to switch."""
        say(text=models_text, channel=channel_id)
        return

    if "clear" in text.lower():
        model_name, _ = get_model_for_user(user_id)
        if thread_ts in conversation_history:
            del conversation_history[thread_ts]
        say(text=f"✅ History cleared! (Using: {model_name})", channel=channel_id)
        return

    if "use " in text.lower():
        for model_name in AVAILABLE_MODELS.keys():
            if model_name in text.lower():
                user_model_preferences[user_id] = model_name
                model_id = AVAILABLE_MODELS[model_name]
                metrics.model_usage[model_name] += 1
                say(text=f"✅ Switched to {model_name} ({model_id})", channel=channel_id)
                return
        say(text="❌ Model not found. Use `models` to see options.", channel=channel_id)
        return

    # Get conversation history
    if thread_ts not in conversation_history:
        conversation_history[thread_ts] = []

    # Add user message to history
    conversation_history[thread_ts].append({"role": "user", "content": text})

    # Get model for user
    model_name, model_id = get_model_for_user(user_id)
    metrics.model_usage[model_name] += 1

    try:
        # Post initial message
        result = client.chat_postMessage(
            channel=channel_id,
            text=f"_Thinking with {model_name}..._"
        )
        message_ts = result["ts"]

        # Call LLM and stream response
        returned_message = call_llm(conversation_history[thread_ts], model_id)

        # Collect streamed response
        full_response = ""
        token_count = 0

        # Loop over OpenAI chat completion streamed chunk
        for chunk in returned_message:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = getattr(chunk.choices[0], "delta", None)
                if delta and hasattr(delta, "content"):
                    content = delta.content
                    if content:
                        full_response += content
                        token_count += 1

        # Update metrics
        metrics.total_tokens += token_count

        # Update conversation history
        conversation_history[thread_ts].append({"role": "assistant", "content": full_response})

        # Update message with full response
        final_text = f"{full_response}\n\n_Using {model_name} ({model_id})_"
        client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=final_text
        )

    except Exception as e:
        logger.error(f"Error calling LLM: {e}", exc_info=True)
        say(text=f"❌ Error: {str(e)}", channel=channel_id)


# Dashboard HTML
DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>PromptBot Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            display: flex;
        }

        /* Sidebar Navigation */
        .sidebar {
            width: 260px;
            background: rgba(255, 255, 255, 0.98);
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            overflow-y: auto;
            padding: 30px 0;
        }
        .sidebar-header {
            padding: 0 25px 25px 25px;
            border-bottom: 2px solid #e5e7eb;
        }
        .sidebar-header h1 {
            font-size: 1.4em;
            color: #667eea;
            margin-bottom: 5px;
        }
        .sidebar-header .status-badge {
            display: inline-block;
            padding: 4px 12px;
            background: #10b981;
            color: white;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
        }
        .nav-menu {
            list-style: none;
            padding: 20px 0;
        }
        .nav-item {
            padding: 12px 25px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
            color: #64748b;
            font-weight: 500;
        }
        .nav-item:hover {
            background: #f8fafc;
            color: #667eea;
        }
        .nav-item.active {
            background: #ede9fe;
            border-left-color: #667eea;
            color: #667eea;
        }
        .nav-icon {
            display: inline-block;
            width: 20px;
            margin-right: 10px;
        }

        /* Main Content */
        .main-content {
            margin-left: 260px;
            padding: 40px;
            width: calc(100% - 260px);
        }
        .container { max-width: 1200px; margin: 0 auto; }

        /* Section Management */
        .section {
            display: none;
        }
        .section.active {
            display: block;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 { color: #333; margin: 0 0 15px 0; font-size: 2.2em; }
        h2 { color: #333; margin: 0 0 20px 0; font-size: 1.8em; }
        h3 { color: #555; margin: 20px 0 15px 0; }
        .status {
            display: inline-block;
            padding: 8px 16px;
            background: #10b981;
            color: white;
            border-radius: 20px;
            font-weight: 600;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .metric-card {
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 2em;
            font-weight: 700;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .feature-card {
            padding: 15px;
            border-left: 4px solid;
            border-radius: 8px;
        }
        .feature-card h4 { margin: 0 0 10px 0; }
        .feature-card p { margin: 0; color: #64748b; }
        .blue { background: #f0f9ff; border-color: #3b82f6; }
        .blue h4 { color: #1e40af; }
        .green { background: #f0fdf4; border-color: #10b981; }
        .green h4 { color: #166534; }
        .yellow { background: #fef3c7; border-color: #f59e0b; }
        .yellow h4 { color: #92400e; }
        .pink { background: #fce7f3; border-color: #ec4899; }
        .pink h4 { color: #9f1239; }
        .model-usage {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .model-stat {
            padding: 15px;
            background: #f3f4f6;
            border-radius: 8px;
            text-align: center;
        }
        .model-stat-name {
            font-weight: 600;
            color: #374151;
            margin-bottom: 5px;
        }
        .model-stat-count {
            font-size: 1.5em;
            color: #667eea;
            font-weight: 700;
        }
        code {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border: 1px solid #e5e7eb;
        }
        th {
            background: #f3f4f6;
            font-weight: 600;
        }
        tr:nth-child(even) { background: #f9fafb; }
    </style>
</head>
<body>
    <!-- Sidebar Navigation -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>🤖 PromptBot</h1>
            <span class="status-badge">✅ RUNNING</span>
        </div>
        <ul class="nav-menu">
            <li class="nav-item active" onclick="showSection('overview')">
                <span class="nav-icon">📊</span> Overview
            </li>
            <li class="nav-item" onclick="showSection('features')">
                <span class="nav-icon">🌟</span> Features
            </li>
            <li class="nav-item" onclick="showSection('model-usage')">
                <span class="nav-icon">📈</span> Model Usage
            </li>
            <li class="nav-item" onclick="showSection('user-guide')">
                <span class="nav-icon">📚</span> User Guide
            </li>
            <li class="nav-item" onclick="showSection('technical')">
                <span class="nav-icon">🔧</span> Technical Details
            </li>
            <li class="nav-item" onclick="showSection('system-info')">
                <span class="nav-icon">ℹ️</span> System Info
            </li>
        </ul>
        <div style="padding: 20px 25px; border-top: 2px solid #e5e7eb;">
            <p style="font-size: 0.75em; color: #9ca3af; margin-bottom: 15px; font-weight: 600; text-transform: uppercase;">External Links</p>
            <a href="https://github.com/honnuanand/Slack-with-Foundation-Models" target="_blank" style="display: block; padding: 10px 0; color: #667eea; text-decoration: none; font-weight: 500; transition: all 0.2s;">
                <span style="margin-right: 8px;">📦</span> GitHub Repo
            </a>
            <a href="/docs" target="_blank" style="display: block; padding: 10px 0; color: #667eea; text-decoration: none; font-weight: 500; transition: all 0.2s;">
                <span style="margin-right: 8px;">📖</span> API Docs
            </a>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <div class="container">
            <!-- Overview Section -->
            <div id="overview" class="section active">
                <div class="card">
                    <h1>🤖 PromptBot Dashboard</h1>
                    <p style="margin-top:15px;color:#666;font-size:1.1em">
                        Intelligent Slack assistant powered by Databricks Foundation Models via Socket Mode
                    </p>

                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">Total Requests</div>
                            <div class="metric-value">{{TOTAL_REQUESTS}}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Total Tokens</div>
                            <div class="metric-value">{{TOTAL_TOKENS}}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Unique Users</div>
                            <div class="metric-value">{{UNIQUE_USERS}}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Active Conversations</div>
                            <div class="metric-value">{{ACTIVE_CONVERSATIONS}}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Features Section -->
            <div id="features" class="section">
                <div class="card">
                    <h2>🌟 PromptBot Features</h2>
                    <div class="features-grid">
                        <div class="feature-card blue">
                            <h4>💬 Intelligent Conversations</h4>
                            <p>Maintains context across conversations with thread-based memory</p>
                        </div>
                        <div class="feature-card green">
                            <h4>🔄 Model Switching</h4>
                            <p>Switch between 7+ foundation models on-the-fly</p>
                        </div>
                        <div class="feature-card yellow">
                            <h4>📊 Real-time Metrics</h4>
                            <p>Monitor usage and performance in this dashboard</p>
                        </div>
                        <div class="feature-card pink">
                            <h4>🎯 Socket Mode</h4>
                            <p>WebSocket connection for instant, reliable responses</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Model Usage Section -->
            <div id="model-usage" class="section">
                <div class="card">
                    <h2>📊 Model Usage Statistics</h2>
                    <div class="model-usage">
                        {{MODEL_STATS}}
                    </div>
                </div>
            </div>

            <!-- User Guide Section -->
            <div id="user-guide" class="section">
                <div class="card">
                    <h2>📚 End User Guide</h2>
                    <h3 style="color:#1e40af">Getting Started</h3>
            <div style="background:#f8fafc;padding:20px;border-radius:8px;margin:15px 0">
                <p><strong>In a Channel:</strong></p>
                <p style="font-family:monospace;background:white;padding:10px;border-radius:4px;margin:10px 0">@PromptBot What is machine learning?</p>
                <p style="margin-top:15px"><strong>In Direct Message:</strong></p>
                <p style="font-family:monospace;background:white;padding:10px;border-radius:4px;margin:10px 0">Just type your question!</p>
            </div>

            <h3 style="color:#166534">🔄 Model Selection</h3>
            <div style="background:#f0fdf4;padding:20px;border-radius:8px;margin:15px 0">
                <p><strong>View Models:</strong></p>
                <p style="font-family:monospace;background:white;padding:10px;border-radius:4px;margin:10px 0">@PromptBot models</p>
                <p style="margin-top:15px"><strong>Switch Models:</strong></p>
                <div style="font-family:monospace;background:white;padding:10px;border-radius:4px;margin:10px 0">
                    @PromptBot use claude-opus<br>
                    @PromptBot use llama-70b<br>
                    @PromptBot use maverick
                </div>
            </div>

            <h3 style="color:#92400e">📖 Model Selection Guide</h3>
            <table>
                <tr>
                    <th>Command</th>
                    <th>Model</th>
                    <th>Best For</th>
                </tr>
                <tr>
                    <td style="font-family:monospace">use maverick</td>
                    <td>Llama 4 Maverick</td>
                    <td>Latest, general purpose</td>
                </tr>
                <tr>
                    <td style="font-family:monospace">use claude-opus</td>
                    <td>Claude Opus 4.1</td>
                    <td>Complex reasoning, detailed analysis</td>
                </tr>
                <tr>
                    <td style="font-family:monospace">use claude-sonnet</td>
                    <td>Claude Sonnet 4.5</td>
                    <td>Balanced performance, speed</td>
                </tr>
                <tr>
                    <td style="font-family:monospace">use llama-405b</td>
                    <td>Llama 3.1 405B</td>
                    <td>Highest accuracy, complex tasks</td>
                </tr>
                <tr>
                    <td style="font-family:monospace">use llama-70b</td>
                    <td>Llama 3.3 70B</td>
                    <td>Fast, accurate responses</td>
                </tr>
                <tr>
                    <td style="font-family:monospace">use llama-8b</td>
                    <td>Llama 3.1 8B</td>
                    <td>Quick, simple tasks</td>
                </tr>
                <tr>
                    <td style="font-family:monospace">use gpt-120b</td>
                    <td>GPT OSS 120B</td>
                    <td>GPT-style responses</td>
                </tr>
            </table>

            <h3 style="color:#9f1239;margin-top:25px">Other Commands</h3>
            <div style="background:#fef3c7;padding:20px;border-radius:8px;margin:15px 0">
                <p><strong>Help:</strong></p>
                <p style="font-family:monospace;background:white;padding:10px;border-radius:4px;margin:10px 0">@PromptBot help</p>
                <p style="margin-top:15px"><strong>Clear Conversation History:</strong></p>
                <p style="font-family:monospace;background:white;padding:10px;border-radius:4px;margin:10px 0">@PromptBot clear</p>
            </div>

            <div style="margin-top:20px;padding:15px;background:#dbeafe;border-radius:8px">
                <strong>💡 Pro Tip:</strong> The bot remembers your conversation in each thread! You can have context-aware discussions.
            </div>
                </div>
            </div>

            <!-- Technical Details Section -->
            <div id="technical" class="section">
                <div class="card">
                    <h2>🔧 Available Models (Technical Details)</h2>
            <ul style="list-style:none;padding:0">
                <li style="padding:12px 15px;background:#f3f4f6;margin-bottom:10px;border-radius:8px;font-family:monospace">
                    <strong>maverick:</strong> databricks-llama-4-maverick
                </li>
                <li style="padding:12px 15px;background:#f3f4f6;margin-bottom:10px;border-radius:8px;font-family:monospace">
                    <strong>claude-opus:</strong> databricks-claude-opus-4-1
                </li>
                <li style="padding:12px 15px;background:#f3f4f6;margin-bottom:10px;border-radius:8px;font-family:monospace">
                    <strong>claude-sonnet:</strong> databricks-claude-sonnet-4-5
                </li>
                <li style="padding:12px 15px;background:#f3f4f6;margin-bottom:10px;border-radius:8px;font-family:monospace">
                    <strong>llama-405b:</strong> databricks-meta-llama-3-1-405b-instruct
                </li>
                <li style="padding:12px 15px;background:#f3f4f6;margin-bottom:10px;border-radius:8px;font-family:monospace">
                    <strong>llama-70b:</strong> databricks-meta-llama-3-3-70b-instruct
                </li>
                <li style="padding:12px 15px;background:#f3f4f6;margin-bottom:10px;border-radius:8px;font-family:monospace">
                    <strong>llama-8b:</strong> databricks-meta-llama-3-1-8b-instruct
                </li>
                <li style="padding:12px 15px;background:#f3f4f6;margin-bottom:10px;border-radius:8px;font-family:monospace">
                    <strong>gpt-120b:</strong> databricks-gpt-oss-120b
                </li>
            </ul>
                </div>
            </div>

            <!-- System Info Section -->
            <div id="system-info" class="section">
                <div class="card">
                    <h2>ℹ️ System Information</h2>

            <h3 style="color:#1e40af;margin-top:20px">Connection Mode</h3>
            <p><strong>Mode:</strong> Socket Mode (WebSocket)</p>
            <p style="color:#666;margin-top:5px">Uses persistent WebSocket connection for instant, reliable message delivery</p>

            <h3 style="color:#1e40af;margin-top:20px">Slack Workspace</h3>
            <p><strong>Workspace:</strong> db-sandbox</p>
            <p><strong>Team ID:</strong> TR115R2H0</p>
            <p><strong>Bot User ID:</strong> U09MJE1D31U</p>
            <p><strong>Bot ID:</strong> B09MQ2TJ2BE</p>
            <p><strong>App ID:</strong> A09ME3KTZ8B</p>

            <h3 style="color:#1e40af;margin-top:20px">Databricks Configuration</h3>
            <p><strong>Host:</strong> {{DATABRICKS_HOST}}</p>
            <p><strong>Secret Scope:</strong> slack-bot-secrets</p>
            <p><strong>Secrets Used:</strong> databricks-token, slack-bot-token, slack-app-token</p>

            <h3 style="color:#1e40af;margin-top:20px">Required OAuth Scopes</h3>
            <div style="background:#f3f4f6;padding:15px;border-radius:8px;margin-top:10px">
                <ul style="margin-left:20px;line-height:1.8">
                    <li><code>app_mentions:read</code> - Read @mentions</li>
                    <li><code>chat:write</code> - Send messages</li>
                    <li><code>im:history</code> - Read DM history</li>
                    <li><code>im:read</code> - View DM info</li>
                    <li><code>im:write</code> - Send DMs</li>
                    <li><code>connections:write</code> - Socket Mode connection (App-level token)</li>
                </ul>
            </div>

            <h3 style="color:#1e40af;margin-top:20px">Event Subscriptions</h3>
            <div style="background:#f3f4f6;padding:15px;border-radius:8px;margin-top:10px">
                <p><strong>Socket Mode:</strong> Enabled ✅</p>
                <p style="margin-top:10px"><strong>Subscribed Events:</strong></p>
                <ul style="margin-left:20px;line-height:1.8">
                    <li><code>app_mention</code> - Bot @mentions in channels</li>
                    <li><code>message.im</code> - Direct messages to bot</li>
                </ul>
            </div>

            <h3 style="color:#1e40af;margin-top:20px">Deployment Information</h3>
            <p><strong>App URL:</strong> <a href="https://slack-foundation-bot-2409307273843806.aws.databricksapps.com" target="_blank">https://slack-foundation-bot-2409307273843806.aws.databricksapps.com</a></p>
            <p><strong>Dashboard:</strong> This page (auto-refreshes every 30 seconds)</p>
            <p><strong>Health Check:</strong> <a href="/health" target="_blank">/health</a></p>
            <p><strong>Metrics API:</strong> <a href="/metrics" target="_blank">/metrics</a></p>
            <p><strong>Uptime:</strong> {{UPTIME}}</p>
            <p><strong>Last Updated:</strong> {{TIMESTAMP}}</p>

            <h3 style="color:#166534;margin-top:20px">🔧 Configuration Management</h3>
            <div style="background:#f0fdf4;padding:20px;border-radius:8px;margin-top:10px">
                <p><strong>Update Slack Tokens:</strong></p>
                <p style="margin-top:10px">1. Get new tokens from <a href="https://api.slack.com/apps/A09ME3KTZ8B" target="_blank">Slack App Config</a></p>
                <p style="margin-top:5px">2. Update app.yml with new token values</p>
                <p style="margin-top:5px">3. Redeploy the app</p>

                <p style="margin-top:20px"><strong>Databricks CLI Commands:</strong></p>
                <pre style="background:white;padding:10px;border-radius:4px;overflow-x:auto;margin-top:10px;font-size:0.9em">databricks apps get slack-foundation-bot
databricks apps deploy slack-foundation-bot \
  --source-code-path /Workspace/Users/anand.rao@databricks.com/apps/slack-bot-clean \
  --mode SNAPSHOT</pre>
            </div>

            <h3 style="color:#92400e;margin-top:20px">📝 Slack App Configuration</h3>
            <div style="background:#fef3c7;padding:20px;border-radius:8px;margin-top:10px">
                <p><strong>Slack App Settings:</strong> <a href="https://api.slack.com/apps/A09ME3KTZ8B" target="_blank">https://api.slack.com/apps/A09ME3KTZ8B</a></p>

                <p style="margin-top:15px"><strong>Key Configuration Pages:</strong></p>
                <ul style="margin-left:20px;line-height:1.8;margin-top:10px">
                    <li><a href="https://api.slack.com/apps/A09ME3KTZ8B/oauth" target="_blank">OAuth & Permissions</a> - Get Bot Token (xoxb-...)</li>
                    <li><a href="https://api.slack.com/apps/A09ME3KTZ8B/general" target="_blank">App-Level Tokens</a> - Get App Token (xapp-...)</li>
                    <li><a href="https://api.slack.com/apps/A09ME3KTZ8B/socket-mode" target="_blank">Socket Mode</a> - Enable/Disable Socket Mode</li>
                    <li><a href="https://api.slack.com/apps/A09ME3KTZ8B/event-subscriptions" target="_blank">Event Subscriptions</a> - Manage bot events</li>
                </ul>

                <p style="margin-top:20px;padding:15px;background:#dbeafe;border-radius:8px">
                    <strong>💡 Note:</strong> Socket Mode must be ENABLED for this bot to work. Event Subscriptions (webhooks) should be DISABLED when using Socket Mode.
                </p>
            </div>

            <h3 style="color:#9f1239;margin-top:20px">🚀 How to Update Tokens</h3>
            <div style="background:#fce7f3;padding:20px;border-radius:8px;margin-top:10px">
                <p><strong>Step 1: Get New Tokens from Slack</strong></p>
                <ol style="margin-left:20px;line-height:1.8;margin-top:10px">
                    <li>Go to <a href="https://api.slack.com/apps/A09ME3KTZ8B/oauth" target="_blank">OAuth & Permissions</a></li>
                    <li>Copy the <strong>Bot User OAuth Token</strong> (starts with xoxb-)</li>
                    <li>Go to <a href="https://api.slack.com/apps/A09ME3KTZ8B/general" target="_blank">App-Level Tokens</a></li>
                    <li>Copy your app token (starts with xapp-) or create one with <code>connections:write</code> scope</li>
                </ol>

                <p style="margin-top:20px"><strong>Step 2: Update app.yml</strong></p>
                <pre style="background:white;padding:10px;border-radius:4px;overflow-x:auto;margin-top:10px;font-size:0.85em">env:
  - name: SLACK_BOT_TOKEN
    value: "xoxb-YOUR-NEW-TOKEN-HERE"
  - name: SLACK_APP_TOKEN
    value: "xapp-YOUR-NEW-TOKEN-HERE"</pre>

                <p style="margin-top:20px"><strong>Step 3: Redeploy</strong></p>
                <pre style="background:white;padding:10px;border-radius:4px;overflow-x:auto;margin-top:10px;font-size:0.85em">databricks workspace import-dir . /Workspace/Users/anand.rao@databricks.com/apps/slack-bot-clean --overwrite
databricks apps deploy slack-foundation-bot \
  --source-code-path /Workspace/Users/anand.rao@databricks.com/apps/slack-bot-clean \
  --mode SNAPSHOT</pre>
            </div>
                </div>
            </div>

        </div>
    </div>

    <script>
        function showSection(sectionId) {
            // Hide all sections
            const sections = document.querySelectorAll('.section');
            sections.forEach(section => section.classList.remove('active'));

            // Show selected section
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
            }

            // Update nav active state
            const navItems = document.querySelectorAll('.nav-item');
            navItems.forEach(item => item.classList.remove('active'));
            event.target.closest('.nav-item').classList.add('active');
        }
    </script>
</body>
</html>"""


@fastapi_app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Render dashboard"""
    # Calculate uptime
    uptime = datetime.now() - metrics.start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    uptime_str = f"{hours}h {minutes}m"

    # Generate model stats HTML
    model_stats_html = ""
    for model_name, count in metrics.model_usage.items():
        model_stats_html += f"""
        <div class="model-stat">
            <div class="model-stat-name">{model_name}</div>
            <div class="model-stat-count">{count}</div>
        </div>
        """

    html = DASHBOARD_HTML
    html = html.replace("{{TOTAL_REQUESTS}}", str(metrics.total_requests))
    html = html.replace("{{TOTAL_TOKENS}}", str(metrics.total_tokens))
    html = html.replace("{{UNIQUE_USERS}}", str(len(metrics.unique_users)))
    html = html.replace("{{ACTIVE_CONVERSATIONS}}", str(len(conversation_history)))
    html = html.replace("{{MODEL_STATS}}", model_stats_html)
    html = html.replace("{{DATABRICKS_HOST}}", DATABRICKS_HOST)
    html = html.replace("{{UPTIME}}", uptime_str)
    html = html.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return HTMLResponse(content=html)


@fastapi_app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "socket_mode",
        "requests": metrics.total_requests,
        "tokens": metrics.total_tokens,
        "users": len(metrics.unique_users)
    }


@fastapi_app.get("/metrics")
async def get_metrics():
    """Get metrics as JSON"""
    return {
        "total_requests": metrics.total_requests,
        "total_tokens": metrics.total_tokens,
        "unique_users": len(metrics.unique_users),
        "active_conversations": len(conversation_history),
        "model_usage": metrics.model_usage,
        "uptime_seconds": (datetime.now() - metrics.start_time).total_seconds()
    }


def run_fastapi():
    """Run FastAPI server in background thread"""
    uvicorn.run(fastapi_app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    logger.info("Starting PromptBot with Socket Mode + Dashboard...")

    # Start FastAPI in background thread
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    logger.info(f"Dashboard server starting on port {PORT}...")

    # Start Socket Mode handler (blocks main thread)
    logger.info("Starting Socket Mode handler...")
    handler = SocketModeHandler(slack_app, SLACK_APP_TOKEN)
    handler.start()
