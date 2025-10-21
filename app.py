import os
import logging
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bolt app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Initialize OpenAI client with Databricks endpoint
openai_client = OpenAI(
    api_key=os.environ.get("DATABRICKS_TOKEN"),
    base_url=f"{os.environ.get('DATABRICKS_HOST')}/serving-endpoints"
)

# Available Databricks Foundation Models (FE VM workspace)
AVAILABLE_MODELS = {
    "maverick": "databricks-llama-4-maverick",
    "llama-70b": "databricks-meta-llama-3-3-70b-instruct",
    "llama-405b": "databricks-meta-llama-3-1-405b-instruct",
    "llama-8b": "databricks-meta-llama-3-1-8b-instruct",
    "claude-sonnet": "databricks-claude-sonnet-4-5",
    "claude-opus": "databricks-claude-opus-4-1",
    "gpt-120b": "databricks-gpt-oss-120b",
}

# Store conversation history per thread
conversation_history = {}

def get_model_response(model_id: str, messages: list) -> str:
    """Get response from Databricks Foundation Model using OpenAI format"""
    try:
        response = openai_client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling Databricks model: {e}")
        raise

@app.message("hello")
def message_hello(message, say):
    """Respond to hello messages"""
    say(f"Hey there <@{message['user']}>! I'm your Databricks AI assistant powered by Foundation Models. Ask me anything!")

@app.event("app_mention")
def handle_app_mentions(event, say, client):
    """Handle app mentions"""
    try:
        thread_ts = event.get("thread_ts") or event["ts"]
        user_message = event["text"]

        # Remove bot mention from message
        user_message = user_message.split(">", 1)[-1].strip()

        # Check if user is requesting a specific model
        selected_model = AVAILABLE_MODELS["maverick"]  # Default
        for key, model_id in AVAILABLE_MODELS.items():
            if f"use {key}" in user_message.lower() or f"switch to {key}" in user_message.lower():
                selected_model = model_id
                say(f"Switching to {key.upper()} model!", thread_ts=thread_ts)
                return

        # Show available models if requested
        if "models" in user_message.lower() or "help" in user_message.lower():
            # Get current model for this thread
            current_model_id = conversation_history.get(thread_ts, {}).get("model", AVAILABLE_MODELS["maverick"])
            current_model_name = next((k for k, v in AVAILABLE_MODELS.items() if v == current_model_id), "maverick")

            models_list = "\n".join([
                f"• `{key}` → *{model_id.replace('databricks-', '')}*"
                for key, model_id in AVAILABLE_MODELS.items()
            ])
            help_text = f"""🤖 *Databricks Foundation Models Bot*

*Connection Status:* ✅ Connected to Databricks FE VM
*Endpoint:* `{os.environ.get('DATABRICKS_HOST')}`

*Available Models:*
{models_list}

*Currently Selected:* `{current_model_name}` → *{current_model_id}*

*Commands:*
• Mention me with your question to chat
• Say "use [model-name]" to switch models (e.g., "use claude-opus")
• Say "help" or "models" to see this message
• Say "clear" to reset conversation history

_Using OpenAI-compatible API format for all models_"""
            say(help_text, thread_ts=thread_ts)
            return

        # Clear conversation history if requested
        if "clear" in user_message.lower():
            if thread_ts in conversation_history:
                del conversation_history[thread_ts]
            say("Conversation history cleared!", thread_ts=thread_ts)
            return

        # Initialize conversation history for this thread
        if thread_ts not in conversation_history:
            conversation_history[thread_ts] = {
                "model": selected_model,
                "messages": []
            }

        # Add user message to history
        conversation_history[thread_ts]["messages"].append({
            "role": "user",
            "content": user_message
        })

        # Show typing indicator
        say("_Thinking..._", thread_ts=thread_ts)

        # Get response from Databricks model
        model_endpoint = conversation_history[thread_ts]["model"]
        response = get_model_response(
            model_endpoint,
            conversation_history[thread_ts]["messages"]
        )

        # Add assistant response to history
        conversation_history[thread_ts]["messages"].append({
            "role": "assistant",
            "content": response
        })

        # Get model name for display
        model_name = next((k for k, v in AVAILABLE_MODELS.items() if v == model_endpoint), "unknown")

        # Send response with model info
        response_with_info = f"{response}\n\n_—Powered by Databricks `{model_name}` ({model_endpoint})_"
        say(response_with_info, thread_ts=thread_ts)

    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(f"Sorry, I encountered an error: {str(e)}", thread_ts=thread_ts)

@app.command("/dbchat")
def handle_dbchat_command(ack, command, say):
    """Handle /dbchat slash command"""
    ack()

    text = command.get("text", "").strip()

    if not text:
        models_list = "\n".join([f"• `{key}`" for key in AVAILABLE_MODELS.keys()])
        say(f"""*Databricks Foundation Models Chat*

Available models:
{models_list}

Usage: `/dbchat [your question]`
Or mention me in a message with your question!""")
        return

    # Process the question
    thread_ts = command.get("ts")
    selected_model = AVAILABLE_MODELS["maverick"]

    try:
        messages = [{"role": "user", "content": text}]
        response = get_model_response(selected_model, messages)
        say(f"*Question:* {text}\n\n*Answer:* {response}")
    except Exception as e:
        logger.error(f"Error in slash command: {e}")
        say(f"Sorry, I encountered an error: {str(e)}")

@app.event("message")
def handle_message_events(event, say):
    """Handle direct messages to the bot"""
    # Only respond to DMs, not channel messages
    if event.get("channel_type") == "im":
        user_message = event.get("text", "")
        thread_ts = event.get("ts")

        if not user_message:
            return

        try:
            # Initialize conversation for this DM
            if thread_ts not in conversation_history:
                conversation_history[thread_ts] = {
                    "model": AVAILABLE_MODELS["maverick"],
                    "messages": []
                }

            # Add user message
            conversation_history[thread_ts]["messages"].append({
                "role": "user",
                "content": user_message
            })

            # Get response
            response = get_model_response(
                conversation_history[thread_ts]["model"],
                conversation_history[thread_ts]["messages"]
            )

            # Add assistant response
            conversation_history[thread_ts]["messages"].append({
                "role": "assistant",
                "content": response
            })

            say(response)

        except Exception as e:
            logger.error(f"Error in DM: {e}")
            say(f"Sorry, I encountered an error: {str(e)}")

if __name__ == "__main__":
    # Start the app using Socket Mode
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    logger.info("⚡️ Bolt app is running with Databricks Foundation Models!")
    handler.start()
