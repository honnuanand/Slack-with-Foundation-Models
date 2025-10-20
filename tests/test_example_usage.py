"""
Comprehensive tests for example_usage.py
Tests simple API usage example
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestExampleUsage:
    """Test the example usage script"""

    @patch("example_usage.OpenAI")
    @patch("builtins.print")
    def test_successful_api_call(self, mock_print, mock_openai_class):
        """Test successful API call in example"""
        with patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token"
        }):
            # Setup mock response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Machine learning is..."))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            # Import and run the script
            import example_usage

            # Verify OpenAI client was initialized correctly
            mock_openai_class.assert_called_with(
                api_key="test-token",
                base_url="https://test.databricks.com/serving-endpoints"
            )

            # Verify API call was made
            mock_client.chat.completions.create.assert_called_once_with(
                model="databricks-meta-llama-3-1-70b-instruct",
                messages=[{"role": "user", "content": "What is machine learning in simple terms?"}],
                max_tokens=500,
                temperature=0.7
            )

            # Verify output was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Machine learning is..." in str(call) for call in print_calls)
            assert any("Databricks Foundation Model" in str(call) for call in print_calls)

    @patch("example_usage.OpenAI")
    @patch("builtins.print")
    def test_missing_environment_variables(self, mock_print, mock_openai_class):
        """Test behavior when environment variables are missing"""
        with patch.dict(os.environ, {}, clear=True):
            # Setup mock to simulate missing credentials
            mock_openai_class.return_value = Mock()

            # Import the script
            import importlib
            import example_usage
            importlib.reload(example_usage)

            # Verify OpenAI client was called with None values
            mock_openai_class.assert_called_with(
                api_key=None,
                base_url="None/serving-endpoints"
            )

    @patch("example_usage.OpenAI")
    @patch("builtins.print")
    def test_api_error_handling(self, mock_print, mock_openai_class):
        """Test handling of API errors"""
        with patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token"
        }):
            # Setup mock to raise an exception
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai_class.return_value = mock_client

            # Import and expect error
            with pytest.raises(Exception, match="API Error"):
                import importlib
                import example_usage
                importlib.reload(example_usage)

    @patch("example_usage.OpenAI")
    @patch("builtins.print")
    def test_empty_response_handling(self, mock_print, mock_openai_class):
        """Test handling of empty API responses"""
        with patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token"
        }):
            # Setup mock with empty response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content=""))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            # Import and run
            import importlib
            import example_usage
            importlib.reload(example_usage)

            # Verify empty response was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Response: " in str(call) for call in print_calls)

    @patch("example_usage.OpenAI")
    def test_correct_model_selection(self, mock_openai_class):
        """Test that the correct model is selected"""
        with patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token"
        }):
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            # Import and run
            import importlib
            import example_usage
            importlib.reload(example_usage)

            # Verify correct model was used
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "databricks-meta-llama-3-1-70b-instruct"

    @patch("example_usage.OpenAI")
    def test_message_format(self, mock_openai_class):
        """Test that messages are formatted correctly"""
        with patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token"
        }):
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            # Import and run
            import importlib
            import example_usage
            importlib.reload(example_usage)

            # Verify message format
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
            assert messages[0]["content"] == "What is machine learning in simple terms?"

    @patch("example_usage.OpenAI")
    def test_api_parameters(self, mock_openai_class):
        """Test that API parameters are set correctly"""
        with patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://test.databricks.com",
            "DATABRICKS_TOKEN": "test-token"
        }):
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            # Import and run
            import importlib
            import example_usage
            importlib.reload(example_usage)

            # Verify API parameters
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["max_tokens"] == 500
            assert call_args[1]["temperature"] == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=example_usage", "--cov-report=html"])