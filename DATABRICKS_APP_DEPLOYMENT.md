# Databricks App Deployment Guide

Deploy the Slack Bot as a robust Databricks App with web dashboard, metrics, and token tracking!

## 🎯 Features

### Web Dashboard
- **Real-time Metrics**: View requests, tokens used, response times
- **Model Usage**: Track which models are being used most
- **Token Analytics**: Monitor input/output token consumption
- **User Statistics**: See unique users and active conversations
- **Hourly Trends**: Visualize request patterns over time
- **Auto-refresh**: Dashboard updates every 30 seconds

### Production Features
- **Secret Management**: Uses Databricks Secrets for credentials
- **Health Checks**: Built-in health endpoints for monitoring
- **Auto-scaling**: Scales between 1-3 instances based on load
- **Error Tracking**: Monitor errors and response times
- **CORS Support**: API accessible from web applications

## 📋 Prerequisites

1. **Databricks Workspace** with Apps enabled
2. **Databricks CLI** installed and configured
3. **Slack App** created and configured
4. **Python 3.11+** (for local testing)

## 🚀 Deployment Steps

### 1. Set Up Databricks Secrets

Run the automated setup script:

```bash
./setup_databricks_secrets.sh
```

Or manually create secrets:

```bash
# Create secret scope
databricks secrets create-scope --scope slack-bot-secrets

# Add secrets
databricks secrets put-secret --scope slack-bot-secrets \
  --key databricks-token --string-value "dapi..."

databricks secrets put-secret --scope slack-bot-secrets \
  --key slack-bot-token --string-value "xoxb-..."

databricks secrets put-secret --scope slack-bot-secrets \
  --key slack-signing-secret --string-value "your-signing-secret"
```

### 2. Deploy the App

```bash
# Deploy using Databricks CLI
databricks apps deploy --config app.yaml

# Or using the Databricks UI:
# 1. Go to Compute → Apps
# 2. Click "Create App"
# 3. Upload app.yaml
# 4. Click "Deploy"
```

### 3. Configure Slack Webhooks

1. Get your app URL from Databricks:
   ```bash
   databricks apps get databricks-slack-bot
   ```

2. In your Slack App settings:
   - Go to **Event Subscriptions**
   - Set Request URL to: `https://your-app-url.databricks.app/slack/events`
   - Verify the URL (should show "Verified")

3. Subscribe to bot events:
   - `app_mention`
   - `message.im`

### 4. Test the Deployment

1. **Check Health**:
   ```bash
   curl https://your-app-url.databricks.app/health
   ```

2. **View Dashboard**:
   - Open: `https://your-app-url.databricks.app/`
   - You'll see the metrics dashboard

3. **Test Slack Integration**:
   - Mention your bot in Slack
   - Check the dashboard for metrics updates

## 📊 Dashboard Features

### Main Metrics
- **Total Requests**: Number of API calls made
- **Total Tokens Used**: Combined input + output tokens
- **Input/Output Tokens**: Separate tracking
- **Unique Users**: Number of distinct users
- **Active Conversations**: Current thread count
- **Average Response Time**: Performance metric
- **Errors**: Error count tracking

### Visualizations
- **Model Usage Pie Chart**: See which models are most popular
- **Hourly Request Line Chart**: Track usage patterns
- **Per-Model Statistics**: Messages and tokens per model

## 🔧 Configuration

### Environment Variables

Set in `app.yaml` or Databricks App configuration:

```yaml
env:
  # Port for FastAPI server
  PORT: "8000"

  # Databricks workspace
  DATABRICKS_HOST: "https://your-workspace.cloud.databricks.com"

  # Secret scope name
  DATABRICKS_SECRET_SCOPE: "slack-bot-secrets"
```

### Scaling Configuration

Adjust in `app.yaml`:

```yaml
resources:
  instances:
    min: 1
    max: 3
    target_cpu_utilization: 70
```

## 🧪 Local Testing

1. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn openai httpx tiktoken
   ```

2. **Set environment variables**:
   ```bash
   export DATABRICKS_TOKEN="dapi..."
   export SLACK_BOT_TOKEN="xoxb-..."
   export SLACK_SIGNING_SECRET="..."
   export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
   ```

3. **Run locally**:
   ```bash
   python app_fastapi.py
   ```

4. **Access dashboard**:
   - Open: http://localhost:8000

## 📡 API Endpoints

### Web Interface
- `GET /` - Dashboard with metrics and visualizations

### Health & Status
- `GET /health` - Health check endpoint
- `GET /metrics` - Raw metrics data (JSON)

### Chat API
- `POST /chat` - Direct chat endpoint for testing
- `POST /slack/events` - Slack webhook endpoint

### Management
- `GET /models` - List available models
- `POST /clear/{thread_id}` - Clear conversation history

## 🔒 Security

### Secret Management
- All credentials stored in Databricks Secrets
- No hardcoded tokens in code
- Scope-based access control

### Slack Verification
- Request signature verification
- Timestamp validation (5-minute window)
- HMAC-based authentication

## 📈 Monitoring

### Built-in Metrics
- Request counts and rates
- Token usage tracking
- Response time monitoring
- Error rate tracking
- User activity metrics

### Health Checks
- Readiness probe: `/health`
- Liveness probe: `/health`
- Auto-restart on failures

## 🐛 Troubleshooting

### App Won't Start
1. Check secrets are configured:
   ```bash
   databricks secrets list-secrets --scope slack-bot-secrets
   ```

2. Verify environment variables:
   ```bash
   databricks apps logs databricks-slack-bot
   ```

### Slack Not Responding
1. Verify webhook URL is correct
2. Check Slack signing secret matches
3. Ensure bot has required scopes
4. Check app logs for errors

### Dashboard Shows No Data
1. Make some test requests first
2. Check browser console for errors
3. Verify CORS is enabled

### High Token Usage
1. Monitor per-model usage in dashboard
2. Adjust max_tokens in code if needed
3. Consider implementing rate limiting

## 🚦 Production Best Practices

1. **Set up monitoring alerts** for error rates
2. **Implement rate limiting** for API endpoints
3. **Use a database** for conversation history (not in-memory)
4. **Set up log aggregation** for debugging
5. **Configure auto-scaling** based on load patterns
6. **Regular secret rotation** for security
7. **Backup conversation history** if needed

## 📝 Example Usage

### Test the Chat API
```bash
curl -X POST https://your-app-url.databricks.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-123",
    "message": "What is machine learning?",
    "model": "maverick"
  }'
```

### Check Metrics
```bash
curl https://your-app-url.databricks.app/metrics
```

## 🎉 Success Indicators

Your deployment is successful when:
- ✅ Health endpoint returns `{"status": "healthy"}`
- ✅ Dashboard shows metrics updating
- ✅ Slack bot responds to mentions
- ✅ Token tracking shows usage
- ✅ No errors in app logs

## 📚 Next Steps

1. **Customize the dashboard** with your branding
2. **Add more models** to AVAILABLE_MODELS
3. **Implement caching** for frequently asked questions
4. **Add user authentication** for dashboard access
5. **Set up alerting** for high token usage
6. **Create usage reports** for cost tracking

## 🆘 Support

- Check logs: `databricks apps logs databricks-slack-bot`
- View status: `databricks apps get databricks-slack-bot`
- Restart app: `databricks apps restart databricks-slack-bot`

Enjoy your production-ready Slack bot with comprehensive monitoring! 🚀