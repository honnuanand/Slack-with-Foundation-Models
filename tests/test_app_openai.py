"""
Comprehensive tests for app_openai.py
Tests Slack bot functionality, event handlers, and API integration
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSlackBotInitialization:
    """Test Slack bot initialization and configuration"""

    @patch("app_openai.OpenAI")
    @patch("app_openai.App")
    def test_databricks_mode_initialization(self, mock_app, mock_openai):
        """Test bot initialization in Databricks mode"""
        with patch.dict(os.environ, {
            "MODE": "databricks",
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token",
            "SLACK_BOT_TOKEN": "xoxb-test"
        }):
            import importlib
            import app_openai
            importlib.reload(app_openai)

            # Check OpenAI client was initialized with Databricks settings
            mock_openai.assert_called_with(
                api_key="test-token",
                base_url="https://test.databricks.com/serving-endpoints"
            )

            # Check correct models are loaded
            assert "databricks-llama-4-maverick" in app_openai.AVAILABLE_MODELS.values()
            assert app_openai.SERVICE_NAME == "Databricks"

    @patch("app_openai.OpenAI")
    @patch("app_openai.App")
    def test_openai_mode_initialization(self, mock_app, mock_openai):
        """Test bot initialization in OpenAI mode"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "sk-test",
            "SLACK_BOT_TOKEN": "xoxb-test"
        }):
            import importlib
            import app_openai
            importlib.reload(app_openai)

            # Check OpenAI client was initialized with API key
            mock_openai.assert_called_with(api_key="sk-test")

            # Check correct models are loaded
            assert "gpt-4o" in app_openai.AVAILABLE_MODELS.values()
            assert app_openai.SERVICE_NAME == "OpenAI"

    @patch("app_openai.App")
    def test_slack_app_initialization(self, mock_app):
        """Test Slack app initialization"""
        with patch.dict(os.environ, {
            "SLACK_BOT_TOKEN": "xoxb-test-token"
        }):
            import importlib
            import app_openai
            importlib.reload(app_openai)

            mock_app.assert_called_with(token="xoxb-test-token")


class TestGetModelResponse:
    """Test the get_model_response function"""

    @patch("app_openai.openai_client")
    @patch("app_openai.logger")
    def test_successful_response(self, mock_logger, mock_client):
        """Test successful model response"""
        from app_openai import get_model_response

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = get_model_response("test-model", messages)

        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

    @patch("app_openai.openai_client")
    @patch("app_openai.logger")
    def test_api_error_handling(self, mock_logger, mock_client):
        """Test error handling in model response"""
        from app_openai import get_model_response

        mock_client.chat.completions.create.side_effect = Exception("API Error")

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(Exception, match="API Error"):
            get_model_response("test-model", messages)

        mock_logger.error.assert_called()

    @patch("app_openai.openai_client")
    def test_empty_response_handling(self, mock_client):
        """Test handling of empty model responses"""
        from app_openai import get_model_response

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=""))]
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = get_model_response("test-model", messages)

        assert result == ""


class TestSlackEventHandlers:
    """Test Slack event handlers"""

    def setup_method(self):
        """Setup for each test"""
        with patch("app_openai.App"):
            with patch("app_openai.OpenAI"):
                import app_openai
                self.app = app_openai

    def test_message_hello_handler(self):
        """Test hello message handler"""
        mock_message = {"user": "U123456"}
        mock_say = Mock()

        self.app.message_hello(mock_message, mock_say)

        mock_say.assert_called_once()
        call_args = mock_say.call_args[0][0]
        assert "Hey there <@U123456>" in call_args
        assert "AI assistant" in call_args

    @patch("app_openai.get_model_response")
    def test_app_mention_basic_question(self, mock_get_response):
        """Test handling basic question in app mention"""
        mock_get_response.return_value = "This is a test response"

        event = {
            "text": "<@U123> What is Python?",
            "ts": "1234567890.123456",
            "user": "U789"
        }
        mock_say = Mock()
        mock_client = Mock()

        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check that response was sent
        assert mock_say.call_count == 2  # Thinking + response
        final_call = mock_say.call_args_list[-1]
        assert final_call[0][0] == "This is a test response"
        assert final_call[1]["thread_ts"] == "1234567890.123456"

    @patch("app_openai.get_model_response")
    def test_app_mention_thread_continuation(self, mock_get_response):
        """Test handling messages in threads"""
        mock_get_response.return_value = "Thread response"

        event = {
            "text": "<@U123> Follow up question",
            "ts": "1234567890.123456",
            "thread_ts": "1234567890.000000",
            "user": "U789"
        }
        mock_say = Mock()
        mock_client = Mock()

        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check that thread_ts is preserved
        final_call = mock_say.call_args_list[-1]
        assert final_call[1]["thread_ts"] == "1234567890.000000"

    def test_app_mention_help_command(self):
        """Test help command in app mention"""
        event = {
            "text": "<@U123> help",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()
        mock_client = Mock()

        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check that help text was sent
        call_args = mock_say.call_args[0][0]
        assert "Available" in call_args
        assert "Models" in call_args
        assert "Commands" in call_args

    def test_app_mention_models_command(self):
        """Test models command in app mention"""
        event = {
            "text": "<@U123> models",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()
        mock_client = Mock()

        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check that models list was sent
        call_args = mock_say.call_args[0][0]
        assert "Available" in call_args
        assert any(model in call_args for model in ["maverick", "llama", "claude", "gpt"])

    def test_app_mention_clear_command(self):
        """Test clear command in app mention"""
        # First, add some conversation history
        thread_ts = "1234567890.123456"
        self.app.conversation_history[thread_ts] = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "test"}]
        }

        event = {
            "text": "<@U123> clear",
            "ts": thread_ts
        }
        mock_say = Mock()
        mock_client = Mock()

        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check that history was cleared
        assert thread_ts not in self.app.conversation_history
        call_args = mock_say.call_args[0][0]
        assert "Conversation history cleared" in call_args

    def test_app_mention_switch_model(self):
        """Test model switching in app mention"""
        event = {
            "text": "<@U123> use claude-sonnet",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()
        mock_client = Mock()

        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check that switch message was sent
        call_args = mock_say.call_args[0][0]
        assert "Switching to" in call_args

    @patch("app_openai.get_model_response")
    @patch("app_openai.logger")
    def test_app_mention_error_handling(self, mock_logger, mock_get_response):
        """Test error handling in app mention"""
        mock_get_response.side_effect = Exception("Test error")

        event = {
            "text": "<@U123> Test question",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()
        mock_client = Mock()

        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check that error message was sent
        error_call = mock_say.call_args_list[-1]
        assert "Sorry, I encountered an error" in error_call[0][0]
        mock_logger.error.assert_called()

    @patch("app_openai.get_model_response")
    def test_conversation_history_management(self, mock_get_response):
        """Test conversation history is properly maintained"""
        mock_get_response.return_value = "Response"

        thread_ts = "1234567890.123456"
        event = {
            "text": "<@U123> First message",
            "ts": thread_ts
        }
        mock_say = Mock()
        mock_client = Mock()

        # First message
        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check history was created
        assert thread_ts in self.app.conversation_history
        assert len(self.app.conversation_history[thread_ts]["messages"]) == 2  # user + assistant

        # Second message
        event["text"] = "<@U123> Second message"
        self.app.handle_app_mentions(event, mock_say, mock_client)

        # Check history was extended
        assert len(self.app.conversation_history[thread_ts]["messages"]) == 4  # 2 users + 2 assistants


class TestSlashCommand:
    """Test slash command handler"""

    def setup_method(self):
        """Setup for each test"""
        with patch("app_openai.App"):
            with patch("app_openai.OpenAI"):
                import app_openai
                self.app = app_openai

    def test_slash_command_empty(self):
        """Test slash command with no text"""
        mock_ack = Mock()
        mock_command = {"text": ""}
        mock_say = Mock()

        self.app.handle_aichat_command(mock_ack, mock_command, mock_say)

        mock_ack.assert_called_once()
        # Check that help text was sent
        call_args = mock_say.call_args[0][0]
        assert "AI Chat" in call_args
        assert "Available models" in call_args
        assert "Usage:" in call_args

    @patch("app_openai.get_model_response")
    def test_slash_command_with_question(self, mock_get_response):
        """Test slash command with a question"""
        mock_get_response.return_value = "Test response"

        mock_ack = Mock()
        mock_command = {"text": "What is Python?"}
        mock_say = Mock()

        self.app.handle_aichat_command(mock_ack, mock_command, mock_say)

        mock_ack.assert_called_once()
        mock_get_response.assert_called_once()

        # Check response format
        call_args = mock_say.call_args[0][0]
        assert "*Question:* What is Python?" in call_args
        assert "*Answer:* Test response" in call_args

    @patch("app_openai.get_model_response")
    @patch("app_openai.logger")
    def test_slash_command_error_handling(self, mock_logger, mock_get_response):
        """Test error handling in slash command"""
        mock_get_response.side_effect = Exception("API Error")

        mock_ack = Mock()
        mock_command = {"text": "Test question"}
        mock_say = Mock()

        self.app.handle_aichat_command(mock_ack, mock_command, mock_say)

        mock_ack.assert_called_once()
        mock_logger.error.assert_called()

        # Check error message was sent
        call_args = mock_say.call_args[0][0]
        assert "Sorry, I encountered an error" in call_args


class TestDirectMessages:
    """Test direct message handling"""

    def setup_method(self):
        """Setup for each test"""
        with patch("app_openai.App"):
            with patch("app_openai.OpenAI"):
                import app_openai
                self.app = app_openai

    @patch("app_openai.get_model_response")
    def test_direct_message_handling(self, mock_get_response):
        """Test handling of direct messages"""
        mock_get_response.return_value = "DM response"

        event = {
            "channel_type": "im",
            "text": "Hello bot",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()

        self.app.handle_message_events(event, mock_say)

        mock_get_response.assert_called_once()
        mock_say.assert_called_with("DM response")

    def test_ignore_channel_messages(self):
        """Test that channel messages are ignored"""
        event = {
            "channel_type": "channel",
            "text": "Hello bot",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()

        self.app.handle_message_events(event, mock_say)

        mock_say.assert_not_called()

    def test_ignore_empty_messages(self):
        """Test that empty messages are ignored"""
        event = {
            "channel_type": "im",
            "text": "",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()

        self.app.handle_message_events(event, mock_say)

        mock_say.assert_not_called()

    @patch("app_openai.get_model_response")
    def test_dm_conversation_history(self, mock_get_response):
        """Test conversation history in DMs"""
        mock_get_response.return_value = "Response"

        thread_ts = "1234567890.123456"
        event = {
            "channel_type": "im",
            "text": "First message",
            "ts": thread_ts
        }
        mock_say = Mock()

        # First message
        self.app.handle_message_events(event, mock_say)

        # Check history was created
        assert thread_ts in self.app.conversation_history
        assert len(self.app.conversation_history[thread_ts]["messages"]) == 2

        # Second message
        event["text"] = "Second message"
        self.app.handle_message_events(event, mock_say)

        # Check history was extended
        assert len(self.app.conversation_history[thread_ts]["messages"]) == 4

    @patch("app_openai.get_model_response")
    @patch("app_openai.logger")
    def test_dm_error_handling(self, mock_logger, mock_get_response):
        """Test error handling in DMs"""
        mock_get_response.side_effect = Exception("DM Error")

        event = {
            "channel_type": "im",
            "text": "Test message",
            "ts": "1234567890.123456"
        }
        mock_say = Mock()

        self.app.handle_message_events(event, mock_say)

        mock_logger.error.assert_called()
        call_args = mock_say.call_args[0][0]
        assert "Sorry, I encountered an error" in call_args


class TestSocketModeHandler:
    """Test Socket Mode handler initialization"""

    @patch("app_openai.SocketModeHandler")
    @patch("app_openai.App")
    @patch("app_openai.OpenAI")
    def test_socket_mode_initialization(self, mock_openai, mock_app, mock_handler):
        """Test Socket Mode handler is properly initialized"""
        with patch.dict(os.environ, {
            "SLACK_APP_TOKEN": "xapp-test-token",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "MODE": "openai",
            "OPENAI_API_KEY": "sk-test"
        }):
            # Import and run main
            with patch("app_openai.__name__", "__main__"):
                import importlib
                import app_openai
                importlib.reload(app_openai)

                mock_handler.assert_called_with(
                    mock_app.return_value,
                    "xapp-test-token"
                )
                mock_handler.return_value.start.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app_openai", "--cov-report=html"])