import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bolt app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Determine which service to use
MODE = os.environ.get("MODE", "databricks").lower()

# Initialize OpenAI client based on MODE
if MODE == "openai":
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    AVAILABLE_MODELS = {
        "gpt-4o": "gpt-4o",
        "gpt-4": "gpt-4-turbo",
        "gpt-3.5": "gpt-3.5-turbo",
    }
    SERVICE_NAME = "OpenAI"
    logger.info("Using OpenAI models")
else:
    openai_client = OpenAI(
        api_key=os.environ.get("DATABRICKS_TOKEN"),
        base_url=f"{os.environ.get('DATABRICKS_HOST')}/serving-endpoints"
    )
    AVAILABLE_MODELS = {
        "maverick": "databricks-llama-4-maverick",
        "llama-70b": "databricks-meta-llama-3-3-70b-instruct",
        "llama-405b": "databricks-meta-llama-3-1-405b-instruct",
        "claude-sonnet": "databricks-claude-sonnet-4-5",
        "claude-opus": "databricks-claude-opus-4-1",
    }
    SERVICE_NAME = "Databricks"
    logger.info("Using Databricks Foundation Models")

# Store conversation history per thread
conversation_history = {}

def get_model_response(model_id: str, messages: list) -> str:
    """Get response from Foundation Model using OpenAI format"""
    try:
        response = openai_client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling {SERVICE_NAME} model: {e}")
        raise

@app.message("hello")
def message_hello(message, say):
    """Respond to hello messages"""
    say(f"Hey there <@{message['user']}>! I'm your AI assistant powered by {SERVICE_NAME}. Ask me anything!")

@app.event("app_mention")
def handle_app_mentions(event, say, client):
    """Handle app mentions"""
    try:
        thread_ts = event.get("thread_ts") or event["ts"]
        user_message = event["text"]

        # Remove bot mention from message
        user_message = user_message.split(">", 1)[-1].strip()

        # Check if user is requesting a specific model
        default_model = list(AVAILABLE_MODELS.values())[0]
        selected_model = default_model

        for key, model_id in AVAILABLE_MODELS.items():
            if f"use {key}" in user_message.lower() or f"switch to {key}" in user_message.lower():
                selected_model = model_id
                say(f"Switching to {key.upper()} model!", thread_ts=thread_ts)
                return

        # Show available models if requested
        if "models" in user_message.lower() or "help" in user_message.lower():
            models_list = "\n".join([f"• `{key}` - {model_id}" for key, model_id in AVAILABLE_MODELS.items()])
            help_text = f"""*Available {SERVICE_NAME} Models:*
{models_list}

*Commands:*
• Mention me with your question to chat
• Say "use [model-name]" to switch models
• Say "help" or "models" to see this message
• Say "clear" to reset conversation history

Currently using: *{list(AVAILABLE_MODELS.keys())[0]}*"""
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

        # Get response from model
        model_id = conversation_history[thread_ts]["model"]
        response = get_model_response(
            model_id,
            conversation_history[thread_ts]["messages"]
        )

        # Add assistant response to history
        conversation_history[thread_ts]["messages"].append({
            "role": "assistant",
            "content": response
        })

        # Send response
        say(response, thread_ts=thread_ts)

    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(f"Sorry, I encountered an error: {str(e)}", thread_ts=thread_ts)

@app.command("/aichat")
def handle_aichat_command(ack, command, say):
    """Handle /aichat slash command"""
    ack()

    text = command.get("text", "").strip()

    if not text:
        models_list = "\n".join([f"• `{key}`" for key in AVAILABLE_MODELS.keys()])
        say(f"""*{SERVICE_NAME} AI Chat*

Available models:
{models_list}

Usage: `/aichat [your question]`
Or mention me in a message with your question!""")
        return

    # Process the question
    default_model = list(AVAILABLE_MODELS.values())[0]

    try:
        messages = [{"role": "user", "content": text}]
        response = get_model_response(default_model, messages)
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
            default_model = list(AVAILABLE_MODELS.values())[0]
            if thread_ts not in conversation_history:
                conversation_history[thread_ts] = {
                    "model": default_model,
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
    logger.info(f"⚡️ Bolt app is running with {SERVICE_NAME}!")
    handler.start()
