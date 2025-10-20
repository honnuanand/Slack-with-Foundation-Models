"""
Comprehensive tests for chat_cli_openai.py
Tests CLI functionality, model selection, environment handling, and API interactions
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chat_cli_openai
from chat_cli_openai import (
    get_model_response,
    print_banner,
    print_models,
    main,
    Colors,
    AVAILABLE_MODELS
)


class TestEnvironmentConfiguration:
    """Test environment variable handling and MODE switching"""

    def test_databricks_mode_default(self):
        """Test that Databricks mode is default when MODE not set"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(chat_cli_openai)
            assert chat_cli_openai.MODE == "databricks"
            assert chat_cli_openai.SERVICE_NAME == "Databricks"
            assert "databricks-llama-4-maverick" in chat_cli_openai.AVAILABLE_MODELS["1"]["id"]

    def test_openai_mode_configuration(self):
        """Test OpenAI mode configuration"""
        with patch.dict(os.environ, {"MODE": "openai"}, clear=True):
            import importlib
            importlib.reload(chat_cli_openai)
            assert chat_cli_openai.MODE == "openai"
            assert chat_cli_openai.SERVICE_NAME == "OpenAI"
            assert "gpt-4o" in chat_cli_openai.AVAILABLE_MODELS["1"]["id"]

    def test_mode_case_insensitive(self):
        """Test that MODE environment variable is case insensitive"""
        with patch.dict(os.environ, {"MODE": "OPENAI"}, clear=True):
            import importlib
            importlib.reload(chat_cli_openai)
            assert chat_cli_openai.MODE == "openai"

    def test_missing_databricks_credentials(self):
        """Test error handling for missing Databricks credentials"""
        with patch.dict(os.environ, {"MODE": "databricks"}, clear=True):
            with patch("sys.exit") as mock_exit:
                with patch("builtins.print") as mock_print:
                    main()
                    mock_exit.assert_called_with(1)
                    # Check that error message was printed
                    calls = [str(call) for call in mock_print.call_args_list]
                    assert any("Missing Databricks credentials" in str(call) for call in calls)

    def test_missing_openai_credentials(self):
        """Test error handling for missing OpenAI credentials"""
        with patch.dict(os.environ, {"MODE": "openai"}, clear=True):
            with patch("sys.exit") as mock_exit:
                with patch("builtins.print") as mock_print:
                    main()
                    mock_exit.assert_called_with(1)
                    # Check that error message was printed
                    calls = [str(call) for call in mock_print.call_args_list]
                    assert any("Missing OpenAI API key" in str(call) for call in calls)


class TestGetModelResponse:
    """Test the get_model_response function"""

    def test_successful_response(self):
        """Test successful API response"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = get_model_response(mock_client, "test-model", messages)

        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

    def test_api_error_handling(self):
        """Test error handling in API calls"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        messages = [{"role": "user", "content": "Hello"}]
        result = get_model_response(mock_client, "test-model", messages)

        assert "Error: API Error" in result
        assert Colors.RED in result

    def test_empty_response_handling(self):
        """Test handling of empty API responses"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=""))]
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = get_model_response(mock_client, "test-model", messages)

        assert result == ""

    def test_response_with_special_characters(self):
        """Test handling of responses with special characters"""
        mock_client = Mock()
        mock_response = Mock()
        special_content = "Response with 特殊字符 and émojis 😀"
        mock_response.choices = [Mock(message=Mock(content=special_content))]
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = get_model_response(mock_client, "test-model", messages)

        assert result == special_content


class TestCLIInteraction:
    """Test CLI interaction and user input handling"""

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_quit_command(self, mock_openai, mock_print, mock_input):
        """Test quit command exits gracefully"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_input.side_effect = ["1", "quit"]

            with patch("sys.exit") as mock_exit:
                main()
                # Should not call sys.exit for normal quit
                mock_exit.assert_not_called()

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_exit_command(self, mock_openai, mock_print, mock_input):
        """Test exit command works as alias for quit"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_input.side_effect = ["1", "exit"]

            with patch("sys.exit") as mock_exit:
                main()
                # Should not call sys.exit for normal exit
                mock_exit.assert_not_called()

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_clear_command(self, mock_openai, mock_print, mock_input):
        """Test clear command resets conversation history"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_openai.return_value.chat.completions.create.return_value = mock_response

            mock_input.side_effect = ["1", "Hello", "clear", "quit"]

            main()

            # Check that clear message was printed
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Conversation history cleared" in str(call) for call in calls)

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_switch_command(self, mock_openai, mock_print, mock_input):
        """Test switch command changes models"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_input.side_effect = ["1", "switch", "2", "quit"]

            main()

            # Check that switch was handled
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Switched to" in str(call) or "GPT-4o Mini" in str(call) for call in calls)

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_model_selection_default(self, mock_openai, mock_print, mock_input):
        """Test default model selection when user presses enter"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_input.side_effect = ["", "quit"]  # Empty string for default

            main()

            # Check that model 1 was selected (default)
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("GPT-4o" in str(call) for call in calls)

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_invalid_model_selection(self, mock_openai, mock_print, mock_input):
        """Test handling of invalid model selection"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_input.side_effect = ["99", "1", "quit"]  # Invalid then valid

            main()

            # Check that error message was shown
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Invalid choice" in str(call) for call in calls)

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_conversation_history_management(self, mock_openai, mock_print, mock_input):
        """Test that conversation history is maintained across messages"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_response1 = Mock()
            mock_response1.choices = [Mock(message=Mock(content="First response"))]
            mock_response2 = Mock()
            mock_response2.choices = [Mock(message=Mock(content="Second response"))]

            mock_openai.return_value.chat.completions.create.side_effect = [
                mock_response1, mock_response2
            ]

            mock_input.side_effect = ["1", "First message", "Second message", "quit"]

            main()

            # Check that API was called with growing conversation history
            calls = mock_openai.return_value.chat.completions.create.call_args_list
            assert len(calls) == 2

            # First call should have 1 message
            assert len(calls[0][1]["messages"]) == 1

            # Second call should have 3 messages (user, assistant, user)
            assert len(calls[1][1]["messages"]) == 3

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_keyboard_interrupt_handling(self, mock_openai, mock_print, mock_input):
        """Test graceful handling of keyboard interrupt"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_input.side_effect = ["1", KeyboardInterrupt()]

            main()

            # Check that interrupt message was shown
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Chat interrupted" in str(call) for call in calls)

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_empty_input_handling(self, mock_openai, mock_print, mock_input):
        """Test that empty input is ignored"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_input.side_effect = ["1", "", "  ", "quit"]  # Empty and whitespace

            main()

            # API should not be called for empty inputs
            mock_openai.return_value.chat.completions.create.assert_not_called()


class TestPrintFunctions:
    """Test output formatting functions"""

    @patch("builtins.print")
    def test_print_banner(self, mock_print):
        """Test banner printing"""
        with patch.dict(os.environ, {"MODE": "openai"}):
            import importlib
            importlib.reload(chat_cli_openai)
            chat_cli_openai.print_banner()

            # Check that banner was printed with service name
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Chat Interface" in str(call) for call in calls)

    @patch("builtins.print")
    def test_print_models_databricks(self, mock_print):
        """Test model list printing for Databricks"""
        with patch.dict(os.environ, {"MODE": "databricks"}):
            import importlib
            importlib.reload(chat_cli_openai)
            chat_cli_openai.print_models()

            # Check that Databricks models are printed
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Llama" in str(call) or "Claude" in str(call) for call in calls)

    @patch("builtins.print")
    def test_print_models_openai(self, mock_print):
        """Test model list printing for OpenAI"""
        with patch.dict(os.environ, {"MODE": "openai"}):
            import importlib
            importlib.reload(chat_cli_openai)
            chat_cli_openai.print_models()

            # Check that OpenAI models are printed
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("GPT" in str(call) for call in calls)


class TestOpenAIClientInitialization:
    """Test OpenAI client initialization with different providers"""

    @patch("chat_cli_openai.OpenAI")
    @patch("builtins.input")
    def test_databricks_client_initialization(self, mock_input, mock_openai_class):
        """Test Databricks client initialization"""
        with patch.dict(os.environ, {
            "MODE": "databricks",
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token"
        }):
            mock_input.side_effect = ["1", "quit"]

            main()

            # Check OpenAI client was initialized with Databricks parameters
            mock_openai_class.assert_called_with(
                api_key="test-token",
                base_url="https://test.databricks.com/serving-endpoints"
            )

    @patch("chat_cli_openai.OpenAI")
    @patch("builtins.input")
    def test_openai_client_initialization(self, mock_input, mock_openai_class):
        """Test OpenAI client initialization"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "sk-test-key"
        }):
            mock_input.side_effect = ["1", "quit"]

            main()

            # Check OpenAI client was initialized with API key
            mock_openai_class.assert_called_with(api_key="sk-test-key")

    @patch("chat_cli_openai.OpenAI")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_client_initialization_error_handling(self, mock_print, mock_input, mock_openai_class):
        """Test error handling during client initialization"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_openai_class.side_effect = Exception("Connection failed")

            with patch("sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_with(1)

                # Check error message was printed
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("Error connecting to OpenAI" in str(call) for call in calls)


class TestColors:
    """Test ANSI color codes"""

    def test_color_codes(self):
        """Test that color codes are defined correctly"""
        assert Colors.BLUE == '\033[94m'
        assert Colors.GREEN == '\033[92m'
        assert Colors.YELLOW == '\033[93m'
        assert Colors.RED == '\033[91m'
        assert Colors.BOLD == '\033[1m'
        assert Colors.END == '\033[0m'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=chat_cli_openai", "--cov-report=html"])