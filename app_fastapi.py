"""
FastAPI application for Databricks Apps deployment
Integrates with Slack using webhooks and provides REST API endpoints
Includes web dashboard with metrics and token usage tracking
"""

import os
import logging
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
import httpx
import hashlib
import hmac
import time
import tiktoken  # For token counting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Databricks Foundation Models Slack Bot",
    description="Connect Slack to Databricks Foundation Models via FastAPI",
    version="1.0.0"
)

# Add CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get configuration from environment or Databricks secrets
def get_secret(key: str, default: str = None) -> str:
    """Get secret from environment or Databricks scope"""
    # First try environment variable
    value = os.environ.get(key)
    if value:
        return value

    # Try Databricks secrets if scope is configured
    scope_name = os.environ.get("DATABRICKS_SECRET_SCOPE")
    if scope_name:
        try:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            value = w.dbutils.secrets.get(scope=scope_name, key=key.lower())
            if value:
                return value
        except Exception as e:
            logger.warning(f"Could not get secret {key} from scope {scope_name}: {e}")

    if default:
        return default
    raise ValueError(f"Secret {key} not found in environment or Databricks scope")

# Configuration
SLACK_BOT_TOKEN = get_secret("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = get_secret("SLACK_SIGNING_SECRET")
DATABRICKS_HOST = get_secret("DATABRICKS_HOST", "https://e2-demo-field-eng.cloud.databricks.com")
DATABRICKS_TOKEN = get_secret("DATABRICKS_TOKEN")

# Initialize OpenAI client with Databricks endpoint
openai_client = OpenAI(
    api_key=DATABRICKS_TOKEN,
    base_url=f"{DATABRICKS_HOST}/serving-endpoints"
)

# Available Databricks Foundation Models
AVAILABLE_MODELS = {
    "maverick": "databricks-llama-4-maverick",
    "llama-70b": "databricks-meta-llama-3-3-70b-instruct",
    "llama-405b": "databricks-meta-llama-3-1-405b-instruct",
    "llama-8b": "databricks-meta-llama-3-1-8b-instruct",
    "claude-sonnet": "databricks-claude-sonnet-4-5",
    "claude-opus": "databricks-claude-opus-4-1",
    "gpt-120b": "databricks-gpt-oss-120b",
}

# Store conversation history (in production, use a database)
conversation_history: Dict[str, Dict] = {}

# Metrics tracking
class Metrics:
    def __init__(self):
        self.total_requests = 0
        self.total_tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.model_usage = defaultdict(int)
        self.user_requests = defaultdict(int)
        self.hourly_requests = defaultdict(int)
        self.errors = 0
        self.start_time = datetime.utcnow()
        self.last_request_time = None
        self.response_times = []
        self.conversations_started = 0
        self.messages_per_model = defaultdict(int)
        self.tokens_per_model = defaultdict(int)

    def record_request(self, user_id: str, model: str, input_tokens: int, output_tokens: int, response_time: float):
        """Record metrics for a request"""
        self.total_requests += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens_used = self.total_input_tokens + self.total_output_tokens
        self.model_usage[model] += 1
        self.user_requests[user_id] += 1
        self.messages_per_model[model] += 1
        self.tokens_per_model[model] += (input_tokens + output_tokens)

        current_hour = datetime.utcnow().strftime("%Y-%m-%d %H:00")
        self.hourly_requests[current_hour] += 1

        self.last_request_time = datetime.utcnow()
        self.response_times.append(response_time)

        # Keep only last 100 response times for average calculation
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

    def get_stats(self) -> Dict:
        """Get current statistics"""
        uptime = datetime.utcnow() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "unique_users": len(self.user_requests),
            "active_conversations": len(conversation_history),
            "model_usage": dict(self.model_usage),
            "messages_per_model": dict(self.messages_per_model),
            "tokens_per_model": dict(self.tokens_per_model),
            "errors": self.errors,
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split('.')[0],
            "last_request": self.last_request_time.isoformat() if self.last_request_time else None,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "hourly_requests": dict(list(self.hourly_requests.items())[-24:])  # Last 24 hours
        }

# Initialize metrics
metrics = Metrics()

# Token counter
def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    thread_id: str
    message: str
    model: Optional[str] = "maverick"
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    thread_id: str
    timestamp: str

class SlackEvent(BaseModel):
    type: str
    text: Optional[str] = None
    user: Optional[str] = None
    ts: Optional[str] = None
    thread_ts: Optional[str] = None
    channel: Optional[str] = None

class SlackChallenge(BaseModel):
    token: str
    challenge: str
    type: str

# Utility functions
def verify_slack_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    """Verify Slack request signature"""
    if abs(time.time() - float(timestamp)) > 60 * 5:
        return False

    sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    my_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, signature)

def get_model_response(model_id: str, messages: List[Dict], user_id: str = "unknown") -> tuple[str, int, int]:
    """Get response from Databricks Foundation Model and track metrics"""
    try:
        # Count input tokens
        input_text = " ".join([msg["content"] for msg in messages])
        input_tokens = count_tokens(input_text)

        start_time = time.time()
        response = openai_client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )
        response_time = time.time() - start_time

        response_text = response.choices[0].message.content
        output_tokens = count_tokens(response_text)

        # Record metrics
        metrics.record_request(user_id, model_id, input_tokens, output_tokens, response_time)

        return response_text, input_tokens, output_tokens
    except Exception as e:
        metrics.errors += 1
        logger.error(f"Error calling Databricks model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def send_slack_message(channel: str, text: str, thread_ts: Optional[str] = None):
    """Send message to Slack channel"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            json={
                "channel": channel,
                "text": text,
                "thread_ts": thread_ts
            }
        )
        if not response.json().get("ok"):
            logger.error(f"Failed to send Slack message: {response.json()}")

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Web dashboard with metrics and status"""
    stats = metrics.get_stats()

    # Create HTML dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Databricks Foundation Models - Slack Bot Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            .header {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }}
            .status {{
                display: inline-block;
                padding: 8px 16px;
                background: #10b981;
                color: white;
                border-radius: 20px;
                font-weight: 600;
                margin-top: 10px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
            }}
            .metric-label {{
                color: #6b7280;
                font-size: 0.9em;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .metric-value {{
                color: #1f2937;
                font-size: 2em;
                font-weight: bold;
            }}
            .metric-value.tokens {{
                color: #3b82f6;
            }}
            .metric-value.users {{
                color: #10b981;
            }}
            .metric-value.errors {{
                color: #ef4444;
            }}
            .chart-container {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }}
            .chart-title {{
                color: #333;
                font-size: 1.5em;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            .models-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .model-card {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }}
            .model-name {{
                font-weight: 600;
                color: #333;
                margin-bottom: 15px;
                font-size: 1.2em;
            }}
            .model-stats {{
                display: flex;
                justify-content: space-between;
                margin-top: 10px;
            }}
            .model-stat {{
                text-align: center;
            }}
            .model-stat-value {{
                font-size: 1.5em;
                font-weight: bold;
                color: #3b82f6;
            }}
            .model-stat-label {{
                font-size: 0.8em;
                color: #6b7280;
                margin-top: 5px;
            }}
            .footer {{
                text-align: center;
                color: white;
                margin-top: 50px;
                padding: 20px;
            }}
            .refresh-btn {{
                background: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                margin-left: 20px;
            }}
            .refresh-btn:hover {{
                background: #2563eb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Databricks Foundation Models - Slack Bot</h1>
                <span class="status">✅ ONLINE</span>
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                <p style="margin-top: 15px; color: #666;">
                    Connected to: <strong>{DATABRICKS_HOST}</strong><br>
                    Uptime: <strong>{stats['uptime_formatted']}</strong>
                </p>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Requests</div>
                    <div class="metric-value">{stats['total_requests']:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Tokens Used</div>
                    <div class="metric-value tokens">{stats['total_tokens_used']:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Input Tokens</div>
                    <div class="metric-value">{stats['total_input_tokens']:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Output Tokens</div>
                    <div class="metric-value">{stats['total_output_tokens']:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Unique Users</div>
                    <div class="metric-value users">{stats['unique_users']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Active Conversations</div>
                    <div class="metric-value">{stats['active_conversations']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value">{stats['avg_response_time_ms']} ms</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Errors</div>
                    <div class="metric-value errors">{stats['errors']}</div>
                </div>
            </div>

            <div class="chart-container">
                <h2 class="chart-title">📊 Model Usage Distribution</h2>
                <canvas id="modelChart" width="400" height="100"></canvas>
            </div>

            <div class="chart-container">
                <h2 class="chart-title">📈 Hourly Request Volume</h2>
                <canvas id="hourlyChart" width="400" height="100"></canvas>
            </div>

            <div class="models-grid">
                {"".join([f'''
                <div class="model-card">
                    <div class="model-name">{model_name.replace('databricks-', '')}</div>
                    <div class="model-stats">
                        <div class="model-stat">
                            <div class="model-stat-value">{stats['messages_per_model'].get(model_id, 0)}</div>
                            <div class="model-stat-label">Messages</div>
                        </div>
                        <div class="model-stat">
                            <div class="model-stat-value">{stats['tokens_per_model'].get(model_id, 0):,}</div>
                            <div class="model-stat-label">Tokens</div>
                        </div>
                    </div>
                </div>
                ''' for model_name, model_id in AVAILABLE_MODELS.items()])}
            </div>

            <div class="footer">
                <p>Last Request: {stats['last_request'] or 'No requests yet'}</p>
                <p style="margin-top: 10px;">Powered by Databricks Foundation Models & FastAPI</p>
            </div>
        </div>

        <script>
            // Model Usage Chart
            const modelCtx = document.getElementById('modelChart').getContext('2d');
            const modelData = {json.dumps(stats['model_usage'])};
            new Chart(modelCtx, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(modelData),
                    datasets: [{{
                        data: Object.values(modelData),
                        backgroundColor: [
                            '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                            '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'right'
                        }}
                    }}
                }}
            }});

            // Hourly Requests Chart
            const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
            const hourlyData = {json.dumps(stats['hourly_requests'])};
            new Chart(hourlyCtx, {{
                type: 'line',
                data: {{
                    labels: Object.keys(hourlyData),
                    datasets: [{{
                        label: 'Requests',
                        data: Object.values(hourlyData),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});

            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint for Databricks Apps"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "databricks_connected": bool(DATABRICKS_TOKEN),
        "slack_configured": bool(SLACK_BOT_TOKEN)
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Direct chat endpoint for testing"""
    thread_id = request.thread_id

    # Initialize conversation history for this thread
    if thread_id not in conversation_history:
        conversation_history[thread_id] = {
            "model": AVAILABLE_MODELS.get(request.model, AVAILABLE_MODELS["maverick"]),
            "messages": []
        }

    # Add user message to history
    conversation_history[thread_id]["messages"].append({
        "role": "user",
        "content": request.message
    })

    # Get response from model
    model_endpoint = conversation_history[thread_id]["model"]
    response, input_tokens, output_tokens = get_model_response(
        model_endpoint,
        conversation_history[thread_id]["messages"],
        user_id=request.user_id or "api"
    )

    # Add assistant response to history
    conversation_history[thread_id]["messages"].append({
        "role": "assistant",
        "content": response
    })

    return ChatResponse(
        response=response,
        model=model_endpoint,
        thread_id=thread_id,
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack events webhook"""
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    # Verify Slack signature
    if not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()

    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}

    # Handle events
    if data.get("type") == "event_callback":
        event = data.get("event", {})

        # Handle app mentions
        if event.get("type") == "app_mention":
            background_tasks.add_task(
                handle_mention,
                event
            )

        # Handle direct messages
        elif event.get("type") == "message" and event.get("channel_type") == "im":
            background_tasks.add_task(
                handle_direct_message,
                event
            )

    return {"status": "ok"}

async def handle_mention(event: dict):
    """Handle app mentions in background"""
    try:
        thread_ts = event.get("thread_ts") or event.get("ts")
        channel = event.get("channel")
        user_message = event.get("text", "").split(">", 1)[-1].strip()

        # Check for special commands
        if "help" in user_message.lower() or "models" in user_message.lower():
            await send_help_message(channel, thread_ts)
            return

        if "clear" in user_message.lower():
            if thread_ts in conversation_history:
                del conversation_history[thread_ts]
            await send_slack_message(channel, "Conversation history cleared!", thread_ts)
            return

        # Check for model switching
        for key, model_id in AVAILABLE_MODELS.items():
            if f"use {key}" in user_message.lower():
                if thread_ts not in conversation_history:
                    conversation_history[thread_ts] = {"model": model_id, "messages": []}
                else:
                    conversation_history[thread_ts]["model"] = model_id
                await send_slack_message(channel, f"Switched to {key.upper()} model!", thread_ts)
                return

        # Process regular message
        if thread_ts not in conversation_history:
            conversation_history[thread_ts] = {
                "model": AVAILABLE_MODELS["maverick"],
                "messages": []
            }

        # Add user message and get response
        conversation_history[thread_ts]["messages"].append({
            "role": "user",
            "content": user_message
        })

        model_endpoint = conversation_history[thread_ts]["model"]
        response, input_tokens, output_tokens = get_model_response(
            model_endpoint,
            conversation_history[thread_ts]["messages"],
            user_id=event.get("user", "slack")
        )

        conversation_history[thread_ts]["messages"].append({
            "role": "assistant",
            "content": response
        })

        # Get model name for display
        model_name = next((k for k, v in AVAILABLE_MODELS.items() if v == model_endpoint), "unknown")

        # Send response with model info
        response_with_info = f"{response}\n\n_—Powered by Databricks `{model_name}` ({model_endpoint})_"
        await send_slack_message(channel, response_with_info, thread_ts)

    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        await send_slack_message(
            event.get("channel"),
            f"Sorry, I encountered an error: {str(e)}",
            event.get("thread_ts") or event.get("ts")
        )

async def handle_direct_message(event: dict):
    """Handle direct messages"""
    # Similar to handle_mention but for DMs
    await handle_mention(event)

async def send_help_message(channel: str, thread_ts: str):
    """Send help message with available models"""
    models_list = "\n".join([
        f"• `{key}` → *{model_id.replace('databricks-', '')}*"
        for key, model_id in AVAILABLE_MODELS.items()
    ])

    help_text = f"""🤖 *Databricks Foundation Models Bot*

*Connection Status:* ✅ Connected to Databricks
*Endpoint:* `{DATABRICKS_HOST}`

*Available Models:*
{models_list}

*Commands:*
• Mention me with your question to chat
• Say "use [model-name]" to switch models
• Say "help" or "models" to see this message
• Say "clear" to reset conversation history

_Deployed as Databricks App with FastAPI_"""

    await send_slack_message(channel, help_text, thread_ts)

@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "models": AVAILABLE_MODELS,
        "default": "maverick"
    }

@app.post("/clear/{thread_id}")
async def clear_conversation(thread_id: str):
    """Clear conversation history for a thread"""
    if thread_id in conversation_history:
        del conversation_history[thread_id]
        return {"status": "cleared", "thread_id": thread_id}
    return {"status": "not_found", "thread_id": thread_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)