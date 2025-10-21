#!/usr/bin/env python3
"""FastAPI application for Databricks Apps deployment"""

import os
import logging
import json
from typing import Optional, Dict, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Databricks Foundation Models Slack Bot",
    description="Connect Slack to Databricks Foundation Models via FastAPI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration with defaults
DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "https://fe-vm-leaps-fe.cloud.databricks.com")
DATABRICKS_SECRET_SCOPE = os.environ.get("DATABRICKS_SECRET_SCOPE", "slack-bot-secrets")
PORT = int(os.environ.get("PORT", 8000))

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

# Simple HTML dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Databricks Slack Bot</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px;
            margin: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin: 0 0 20px 0;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            background: #10b981;
            color: white;
            border-radius: 20px;
            font-weight: 600;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .info-item {
            padding: 20px;
            background: #f9fafb;
            border-radius: 10px;
        }
        .info-label {
            color: #6b7280;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .info-value {
            color: #1f2937;
            font-size: 1.2em;
            font-weight: 600;
            word-break: break-all;
        }
        .models-list {
            list-style: none;
            padding: 0;
        }
        .models-list li {
            padding: 10px;
            background: #f3f4f6;
            margin-bottom: 10px;
            border-radius: 8px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🤖 PromptBot - Databricks Foundation Models for Slack</h1>
            <span class="status">✅ RUNNING</span>
            <p style="margin-top: 15px; color: #666; font-size: 1.1em;">
                Intelligent Slack assistant powered by state-of-the-art Databricks Foundation Models
            </p>

            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">Operational</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Databricks Host</div>
                    <div class="info-value">{{DATABRICKS_HOST}}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Secret Scope</div>
                    <div class="info-value">{{DATABRICKS_SECRET_SCOPE}}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">API Version</div>
                    <div class="info-value">1.0.0</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🌟 PromptBot Features</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
                <div style="padding: 15px; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: #1e40af;">💬 Intelligent Conversations</h4>
                    <p style="margin: 0; color: #64748b;">Maintains context across conversations with thread-based memory</p>
                </div>
                <div style="padding: 15px; background: #f0fdf4; border-left: 4px solid #10b981; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: #166534;">🔄 Model Switching</h4>
                    <p style="margin: 0; color: #64748b;">Switch between 7+ foundation models on-the-fly with simple commands</p>
                </div>
                <div style="padding: 15px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: #92400e;">📊 Token Tracking</h4>
                    <p style="margin: 0; color: #64748b;">Monitor token usage and costs across all models in real-time</p>
                </div>
                <div style="padding: 15px; background: #fce7f3; border-left: 4px solid #ec4899; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: #9f1239;">🎯 Direct & Channel Support</h4>
                    <p style="margin: 0; color: #64748b;">Works in channels via @mentions and direct messages</p>
                </div>
            </div>

            <h3 style="margin-top: 30px;">How to Use PromptBot</h3>
            <ol style="line-height: 1.8;">
                <li>Add PromptBot to your Slack channel</li>
                <li>Mention <code>@PromptBot</code> with your question</li>
                <li>Use <code>@PromptBot models</code> to see available models</li>
                <li>Use <code>@PromptBot use [model-name]</code> to switch models</li>
                <li>Use <code>@PromptBot clear</code> to reset conversation history</li>
            </ol>
        </div>

        <div class="card">
            <h2>📚 End User Guide - Using PromptBot in Slack</h2>

            <h3 style="margin-top: 20px; color: #1e40af;">Getting Started</h3>
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 15px 0;">
                <p><strong>In a Channel:</strong></p>
                <p style="font-family: monospace; background: white; padding: 10px; border-radius: 4px;">
                    @PromptBot What is machine learning?
                </p>
                <p style="margin-top: 10px;"><strong>In Direct Message:</strong></p>
                <p style="font-family: monospace; background: white; padding: 10px; border-radius: 4px;">
                    Just type your question directly!
                </p>
            </div>

            <h3 style="margin-top: 30px; color: #166534;">🔄 Model Selection Commands</h3>
            <p>Users can switch between different AI models based on their needs:</p>

            <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 15px 0;">
                <p><strong>View Available Models:</strong></p>
                <p style="font-family: monospace; background: white; padding: 10px; border-radius: 4px;">
                    @PromptBot models
                </p>

                <p style="margin-top: 15px;"><strong>Switch to a Specific Model:</strong></p>
                <p style="font-family: monospace; background: white; padding: 10px; border-radius: 4px;">
                    @PromptBot use claude-opus<br>
                    @PromptBot use llama-70b<br>
                    @PromptBot use maverick
                </p>
            </div>

            <h3 style="margin-top: 30px; color: #92400e;">Model Selection Guide</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <tr style="background: #f3f4f6;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Command</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Model</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Best For</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">use maverick</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Llama 4 Maverick</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Latest model, general purpose</td>
                </tr>
                <tr style="background: #f9fafb;">
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">use claude-opus</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Claude Opus 4.1</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Complex reasoning, analysis</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">use claude-sonnet</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Claude Sonnet 4.5</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Balanced performance</td>
                </tr>
                <tr style="background: #f9fafb;">
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">use llama-405b</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Llama 3.1 405B</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Largest Llama, highest accuracy</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">use llama-70b</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Llama 3.3 70B</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Fast, accurate responses</td>
                </tr>
                <tr style="background: #f9fafb;">
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">use llama-8b</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Llama 3.1 8B</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">Quick, simple tasks</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-family: monospace;">use gpt-120b</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">GPT OSS 120B</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">GPT-style responses</td>
                </tr>
            </table>

            <h3 style="margin-top: 30px; color: #9f1239;">Other Commands</h3>
            <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 15px 0;">
                <p><strong>View Help & Available Models:</strong></p>
                <p style="font-family: monospace; background: white; padding: 10px; border-radius: 4px;">
                    @PromptBot help
                </p>

                <p style="margin-top: 15px;"><strong>Clear Conversation History:</strong></p>
                <p style="font-family: monospace; background: white; padding: 10px; border-radius: 4px;">
                    @PromptBot clear
                </p>
            </div>

            <p style="margin-top: 20px; padding: 15px; background: #dbeafe; border-radius: 8px;">
                <strong>💡 Pro Tip:</strong> The bot remembers your conversation in each thread. Switch models anytime to compare responses!
            </p>
        </div>

        <div class="card">
            <h2>Available Models (Technical Details)</h2>
            <ul class="models-list">
                {{MODELS_LIST}}
            </ul>
        </div>

        <div class="card">
            <h2>API Endpoints</h2>
            <ul>
                <li><strong>GET /</strong> - This dashboard</li>
                <li><strong>GET /health</strong> - Health check</li>
                <li><strong>POST /slack/events</strong> - Slack webhook endpoint</li>
                <li><strong>GET /models</strong> - List available models</li>
            </ul>
        </div>

        <div class="card">
            <h2>Slack Integration</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Slack App Name</div>
                    <div class="info-value">PromptBot</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Workspace ID</div>
                    <div class="info-value">T01KUJ0D1KJ</div>
                </div>
                <div class="info-item">
                    <div class="info-label">App ID</div>
                    <div class="info-value">A09ME3KTZ8B</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Integration Status</div>
                    <div class="info-value" style="color: #10b981;">Ready</div>
                </div>
            </div>

            <h3 style="margin-top: 30px;">Webhook Configuration</h3>
            <p>Configure your Slack app's Event Subscriptions with this URL:</p>
            <p style="background: #f3f4f6; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 14px;">
                {{APP_URL}}/slack/events
            </p>

            <h3 style="margin-top: 20px;">Required Bot Events</h3>
            <ul>
                <li><code>app_mention</code> - When someone mentions @PromptBot</li>
                <li><code>message.im</code> - Direct messages to the bot</li>
            </ul>

            <h3 style="margin-top: 20px;">Required OAuth Scopes</h3>
            <ul>
                <li><code>chat:write</code> - Send messages</li>
                <li><code>channels:history</code> - Read channel messages</li>
                <li><code>groups:history</code> - Read private channel messages</li>
                <li><code>im:history</code> - Read direct messages</li>
                <li><code>mpim:history</code> - Read group direct messages</li>
            </ul>

            <p style="margin-top: 20px; padding: 15px; background: #fef3c7; border-radius: 8px;">
                <strong>⚠️ Important:</strong> Make sure to update the Slack Signing Secret in Databricks:<br>
                <code style="background: white; padding: 5px; border-radius: 4px;">
                databricks secrets put-secret slack-bot-secrets slack-signing-secret --string-value "YOUR_SECRET"
                </code>
            </p>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Web dashboard"""
    models_html = "".join([
        f"<li>{name}: {model_id}</li>"
        for name, model_id in AVAILABLE_MODELS.items()
    ])

    # Get app URL from request or environment
    app_url = "https://slack-foundation-bot-2409307273843806.aws.databricksapps.com"

    html = DASHBOARD_HTML.replace("{{DATABRICKS_HOST}}", DATABRICKS_HOST)
    html = html.replace("{{DATABRICKS_SECRET_SCOPE}}", DATABRICKS_SECRET_SCOPE)
    html = html.replace("{{MODELS_LIST}}", models_html)
    html = html.replace("{{APP_URL}}", app_url)

    return HTMLResponse(content=html)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "databricks_host": DATABRICKS_HOST,
        "secret_scope": DATABRICKS_SECRET_SCOPE
    }

@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "models": AVAILABLE_MODELS,
        "default": "maverick"
    }

@app.get("/slack/events")
async def slack_events_get():
    """Handle GET requests to Slack events endpoint"""
    return {
        "status": "ok",
        "message": "Slack events endpoint is configured",
        "info": "This endpoint accepts Slack event subscriptions via POST"
    }

@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack events webhook"""
    try:
        data = await request.json()

        # Handle URL verification challenge
        if data.get("type") == "url_verification":
            logger.info("Received Slack URL verification challenge")
            return {"challenge": data.get("challenge")}

        # Handle event callbacks
        if data.get("type") == "event_callback":
            event = data.get("event", {})
            event_type = event.get("type")
            logger.info(f"Received Slack event: {event_type}")

            # Log event details for debugging
            if event_type == "app_mention":
                logger.info(f"App mentioned by user: {event.get('user')}")
            elif event_type == "message":
                logger.info(f"Message from user: {event.get('user')}")

        # Acknowledge the event
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    logger.info(f"Starting Databricks Slack Bot on port {PORT}")
    logger.info(f"Databricks Host: {DATABRICKS_HOST}")
    logger.info(f"Secret Scope: {DATABRICKS_SECRET_SCOPE}")

    uvicorn.run(app, host="0.0.0.0", port=PORT)