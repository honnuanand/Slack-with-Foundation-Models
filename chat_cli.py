#!/usr/bin/env python3
"""
Command-line chat interface for Databricks Foundation Models
No Slack required - perfect for testing!
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Available Databricks Foundation Models (based on FE VM workspace)
AVAILABLE_MODELS = {
    "1": {"name": "Llama 4 Maverick", "id": "databricks-llama-4-maverick"},
    "2": {"name": "Llama 3.3 70B Instruct", "id": "databricks-meta-llama-3-3-70b-instruct"},
    "3": {"name": "Llama 3.1 405B Instruct", "id": "databricks-meta-llama-3-1-405b-instruct"},
    "4": {"name": "Llama 3.1 8B Instruct", "id": "databricks-meta-llama-3-1-8b-instruct"},
    "5": {"name": "Claude Sonnet 4.5", "id": "databricks-claude-sonnet-4-5"},
    "6": {"name": "Claude Opus 4.1", "id": "databricks-claude-opus-4-1"},
    "7": {"name": "GPT OSS 120B", "id": "databricks-gpt-oss-120b"},
}

# ANSI color codes for terminal
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Print welcome banner"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("  Databricks Foundation Models - Chat Interface")
    print(f"{'='*60}{Colors.END}\n")

def print_models():
    """Print available models"""
    print(f"{Colors.YELLOW}Available Models:{Colors.END}")
    for key, model in AVAILABLE_MODELS.items():
        print(f"  {key}. {model['name']}")
    print()

def get_model_response(client: OpenAI, model_id: str, messages: list) -> str:
    """Get response from Databricks Foundation Model using OpenAI format"""
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"{Colors.RED}Error: {str(e)}{Colors.END}"

def main():
    """Main chat loop"""
    # Check for required environment variables
    if not os.environ.get("DATABRICKS_HOST") or not os.environ.get("DATABRICKS_TOKEN"):
        print(f"{Colors.RED}Error: Missing Databricks credentials!{Colors.END}")
        print("Please set DATABRICKS_HOST and DATABRICKS_TOKEN in your .env file")
        print("\nExample .env file:")
        print("DATABRICKS_HOST=https://your-workspace.cloud.databricks.com")
        print("DATABRICKS_TOKEN=your-databricks-token")
        sys.exit(1)

    # Initialize OpenAI client with Databricks endpoint
    try:
        client = OpenAI(
            api_key=os.environ.get("DATABRICKS_TOKEN"),
            base_url=f"{os.environ.get('DATABRICKS_HOST')}/serving-endpoints"
        )
        print(f"{Colors.GREEN}✓ Connected to Databricks{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}Error connecting to Databricks: {e}{Colors.END}")
        sys.exit(1)

    print_banner()
    print_models()

    # Select model
    while True:
        model_choice = input(f"{Colors.BOLD}Select a model (1-7) [default: 1 - Llama 4 Maverick]: {Colors.END}").strip()
        if not model_choice:
            model_choice = "1"
        if model_choice in AVAILABLE_MODELS:
            selected_model = AVAILABLE_MODELS[model_choice]
            break
        print(f"{Colors.RED}Invalid choice. Please select 1-7.{Colors.END}")

    print(f"\n{Colors.GREEN}Selected: {selected_model['name']}{Colors.END}")
    print(f"{Colors.BLUE}Model ID: {selected_model['id']}{Colors.END}\n")

    # Initialize conversation history
    conversation_history = []

    print(f"{Colors.YELLOW}Commands:{Colors.END}")
    print("  • Type your message and press Enter to chat")
    print("  • Type 'clear' to reset conversation history")
    print("  • Type 'switch' to change models")
    print("  • Type 'quit' or 'exit' to leave")
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")

    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}{Colors.GREEN}You: {Colors.END}").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"\n{Colors.BLUE}Thanks for chatting! Goodbye!{Colors.END}\n")
                break

            if user_input.lower() == 'clear':
                conversation_history = []
                print(f"{Colors.YELLOW}Conversation history cleared!{Colors.END}\n")
                continue

            if user_input.lower() == 'switch':
                print()
                print_models()
                model_choice = input(f"{Colors.BOLD}Select a model (1-7): {Colors.END}").strip()
                if model_choice in AVAILABLE_MODELS:
                    selected_model = AVAILABLE_MODELS[model_choice]
                    conversation_history = []  # Clear history when switching models
                    print(f"{Colors.GREEN}Switched to: {selected_model['name']}{Colors.END}\n")
                else:
                    print(f"{Colors.RED}Invalid choice.{Colors.END}\n")
                continue

            # Add user message to history
            conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # Show thinking indicator
            print(f"{Colors.BLUE}Assistant: {Colors.END}", end="", flush=True)
            print(f"{Colors.YELLOW}[Thinking...]{Colors.END}", end="\r", flush=True)

            # Get response from model
            response = get_model_response(
                client,
                selected_model['id'],
                conversation_history
            )

            # Clear thinking indicator and show response
            print(f"{Colors.BLUE}Assistant: {Colors.END}{response}\n")

            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": response
            })

        except KeyboardInterrupt:
            print(f"\n\n{Colors.BLUE}Chat interrupted. Goodbye!{Colors.END}\n")
            break
        except Exception as e:
            print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}\n")

if __name__ == "__main__":
    main()
