#!/bin/bash

# Setup script for Databricks secrets
# This script creates a secret scope and adds the required secrets

set -e

echo "🔐 Databricks Secrets Setup for Slack Bot"
echo "========================================="

# Default values
SCOPE_NAME="${DATABRICKS_SECRET_SCOPE:-slack-bot-secrets}"

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI is not installed. Please install it first:"
    echo "   pip install databricks-cli"
    exit 1
fi

# Check if authenticated
echo "Checking Databricks authentication..."
if ! databricks secrets list-scopes &> /dev/null; then
    echo "❌ Not authenticated to Databricks. Please run:"
    echo "   databricks configure"
    exit 1
fi

echo "✅ Authenticated to Databricks"
echo ""

# Function to safely read secrets
read_secret() {
    local prompt="$1"
    local var_name="$2"

    echo -n "$prompt"
    read -s value
    echo ""
    eval "$var_name='$value'"
}

# Check if scope exists
echo "Checking if scope '$SCOPE_NAME' exists..."
if databricks secrets list-scopes | grep -q "$SCOPE_NAME"; then
    echo "✅ Scope '$SCOPE_NAME' already exists"
    echo -n "Do you want to update the existing secrets? (y/n): "
    read update_secrets
    if [[ "$update_secrets" != "y" ]]; then
        echo "Exiting without changes."
        exit 0
    fi
else
    echo "Creating new scope '$SCOPE_NAME'..."
    databricks secrets create-scope --scope "$SCOPE_NAME" --initial-manage-principal users
    echo "✅ Scope created successfully"
fi

echo ""
echo "Now let's add the required secrets to the scope."
echo "================================================"

# Get Databricks token
echo ""
echo "1. Databricks Personal Access Token"
echo "   Generate from: User Settings → Developer → Access Tokens"
read_secret "   Enter Databricks token (dapi...): " DATABRICKS_TOKEN

# Get Slack Bot Token
echo ""
echo "2. Slack Bot User OAuth Token"
echo "   Get from: https://api.slack.com/apps → Your App → OAuth & Permissions"
read_secret "   Enter Slack Bot Token (xoxb-...): " SLACK_BOT_TOKEN

# Get Slack Signing Secret
echo ""
echo "3. Slack Signing Secret"
echo "   Get from: https://api.slack.com/apps → Your App → Basic Information"
read_secret "   Enter Slack Signing Secret: " SLACK_SIGNING_SECRET

# Store secrets
echo ""
echo "Storing secrets in Databricks scope..."

# Store Databricks token
echo "$DATABRICKS_TOKEN" | databricks secrets put-secret \
    --scope "$SCOPE_NAME" \
    --key "databricks-token" \
    --string-value

# Store Slack bot token
echo "$SLACK_BOT_TOKEN" | databricks secrets put-secret \
    --scope "$SCOPE_NAME" \
    --key "slack-bot-token" \
    --string-value

# Store Slack signing secret
echo "$SLACK_SIGNING_SECRET" | databricks secrets put-secret \
    --scope "$SCOPE_NAME" \
    --key "slack-signing-secret" \
    --string-value

echo "✅ All secrets stored successfully!"
echo ""

# Verify secrets
echo "Verifying secrets in scope '$SCOPE_NAME':"
databricks secrets list-secrets --scope "$SCOPE_NAME"

echo ""
echo "🎉 Setup complete! Your secrets are now stored in Databricks."
echo ""
echo "Next steps:"
echo "1. Deploy the app using: databricks apps deploy --config app.yaml"
echo "2. Configure Slack webhook URL to point to your Databricks App endpoint"
echo "3. Access the dashboard at your app's URL"
echo ""
echo "Environment variables for local testing:"
echo "export DATABRICKS_SECRET_SCOPE='$SCOPE_NAME'"
echo "export DATABRICKS_HOST='$(databricks host)'"