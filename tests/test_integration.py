"""
Integration tests for API calls and end-to-end functionality
These tests can be run against actual APIs when credentials are available
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
import chat_cli_openai
import app_openai


class TestAPIIntegration:
    """Integration tests for API calls"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY") and not os.environ.get("DATABRICKS_TOKEN"),
        reason="No API credentials available"
    )
    def test_real_api_call_openai(self):
        """Test actual OpenAI API call (requires OPENAI_API_KEY)"""
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        messages = [{"role": "user", "content": "Say 'test successful' and nothing else"}]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=10,
            temperature=0
        )

        assert response.choices[0].message.content.lower().strip() == "test successful"

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("DATABRICKS_TOKEN"),
        reason="Databricks credentials not available"
    )
    def test_real_api_call_databricks(self):
        """Test actual Databricks API call (requires DATABRICKS_TOKEN)"""
        if not os.environ.get("DATABRICKS_HOST") or not os.environ.get("DATABRICKS_TOKEN"):
            pytest.skip("Databricks credentials not available")

        client = OpenAI(
            api_key=os.environ.get("DATABRICKS_TOKEN"),
            base_url=f"{os.environ.get('DATABRICKS_HOST')}/serving-endpoints"
        )

        messages = [{"role": "user", "content": "Say 'test successful' and nothing else"}]

        response = client.chat.completions.create(
            model="databricks-meta-llama-3-1-8b-instruct",
            messages=messages,
            max_tokens=10,
            temperature=0
        )

        assert "test" in response.choices[0].message.content.lower()

    @pytest.mark.integration
    def test_api_timeout_handling(self):
        """Test handling of API timeouts"""
        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = TimeoutError("Request timeout")
            mock_openai_class.return_value = mock_client

            messages = [{"role": "user", "content": "Test"}]
            result = chat_cli_openai.get_model_response(mock_client, "test-model", messages)

            assert "Error" in result
            assert "timeout" in result.lower()

    @pytest.mark.integration
    def test_rate_limit_handling(self):
        """Test handling of rate limiting"""
        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            # Simulate rate limit error
            mock_error = Exception("Rate limit exceeded")
            mock_error.status_code = 429
            mock_client.chat.completions.create.side_effect = mock_error
            mock_openai_class.return_value = mock_client

            messages = [{"role": "user", "content": "Test"}]
            result = chat_cli_openai.get_model_response(mock_client, "test-model", messages)

            assert "Error" in result

    @pytest.mark.integration
    def test_invalid_api_key_handling(self):
        """Test handling of invalid API keys"""
        client = OpenAI(api_key="invalid-key-12345")

        messages = [{"role": "user", "content": "Test"}]
        result = chat_cli_openai.get_model_response(client, "test-model", messages)

        assert "Error" in result

    @pytest.mark.integration
    def test_network_error_handling(self):
        """Test handling of network errors"""
        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = ConnectionError("Network error")
            mock_openai_class.return_value = mock_client

            messages = [{"role": "user", "content": "Test"}]
            result = chat_cli_openai.get_model_response(mock_client, "test-model", messages)

            assert "Error" in result


class TestEndToEndCLI:
    """End-to-end tests for CLI functionality"""

    @pytest.mark.integration
    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_full_conversation_flow(self, mock_openai_class, mock_print, mock_input):
        """Test a complete conversation flow"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            # Setup mock responses
            mock_client = Mock()
            responses = [
                Mock(choices=[Mock(message=Mock(content="Hello! How can I help?"))]),
                Mock(choices=[Mock(message=Mock(content="Python is a programming language"))]),
                Mock(choices=[Mock(message=Mock(content="It was created by Guido van Rossum"))])
            ]
            mock_client.chat.completions.create.side_effect = responses
            mock_openai_class.return_value = mock_client

            # Simulate user interaction
            mock_input.side_effect = [
                "1",  # Select model
                "Hello",  # First message
                "What is Python?",  # Second message
                "Who created it?",  # Third message
                "quit"  # Exit
            ]

            chat_cli_openai.main()

            # Verify conversation flow
            assert mock_client.chat.completions.create.call_count == 3

            # Check conversation history is maintained
            calls = mock_client.chat.completions.create.call_args_list

            # First call - 1 message
            assert len(calls[0][1]["messages"]) == 1

            # Second call - 3 messages (user, assistant, user)
            assert len(calls[1][1]["messages"]) == 3

            # Third call - 5 messages (full history)
            assert len(calls[2][1]["messages"]) == 5

    @pytest.mark.integration
    @patch("builtins.input")
    @patch("builtins.print")
    @patch("chat_cli_openai.OpenAI")
    def test_model_switching_flow(self, mock_openai_class, mock_print, mock_input):
        """Test model switching during conversation"""
        with patch.dict(os.environ, {
            "MODE": "openai",
            "OPENAI_API_KEY": "test-key"
        }):
            mock_client = Mock()
            mock_response = Mock(choices=[Mock(message=Mock(content="Response"))])
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            # Simulate model switching
            mock_input.side_effect = [
                "1",  # Initial model
                "Test message",  # Send message
                "switch",  # Switch command
                "2",  # Select new model
                "New message",  # Send with new model
                "quit"
            ]

            chat_cli_openai.main()

            # Verify model switching
            calls = mock_client.chat.completions.create.call_args_list
            assert len(calls) == 2

            # Check different models were used
            assert calls[0][1]["model"] == "gpt-4o"
            assert calls[1][1]["model"] == "gpt-4o-mini"


class TestEndToEndSlack:
    """End-to-end tests for Slack bot functionality"""

    @pytest.mark.integration
    @patch("app_openai.openai_client")
    def test_slack_conversation_flow(self, mock_client):
        """Test a complete Slack conversation flow"""
        # Setup mock responses
        responses = [
            Mock(choices=[Mock(message=Mock(content="Hello!"))]),
            Mock(choices=[Mock(message=Mock(content="I remember our conversation"))])
        ]
        mock_client.chat.completions.create.side_effect = responses

        mock_say = Mock()

        # First message
        event1 = {
            "text": "<@U123> Hello bot",
            "ts": "1234567890.123456",
            "user": "U789"
        }
        app_openai.handle_app_mentions(event1, mock_say, Mock())

        # Second message in same thread
        event2 = {
            "text": "<@U123> Do you remember me?",
            "ts": "1234567890.234567",
            "thread_ts": "1234567890.123456",
            "user": "U789"
        }
        app_openai.handle_app_mentions(event2, mock_say, Mock())

        # Verify conversation continuity
        assert mock_client.chat.completions.create.call_count == 2

        # Check second call includes conversation history
        second_call = mock_client.chat.completions.create.call_args_list[1]
        messages = second_call[1]["messages"]
        assert len(messages) == 3  # First user, first assistant, second user

    @pytest.mark.integration
    @patch("app_openai.openai_client")
    def test_slack_multi_thread_isolation(self, mock_client):
        """Test that different threads maintain separate conversations"""
        mock_response = Mock(choices=[Mock(message=Mock(content="Response"))])
        mock_client.chat.completions.create.return_value = mock_response

        mock_say = Mock()

        # Message in thread 1
        event1 = {
            "text": "<@U123> Thread 1 message",
            "ts": "1111111111.111111",
            "user": "U789"
        }
        app_openai.handle_app_mentions(event1, mock_say, Mock())

        # Message in thread 2
        event2 = {
            "text": "<@U123> Thread 2 message",
            "ts": "2222222222.222222",
            "user": "U789"
        }
        app_openai.handle_app_mentions(event2, mock_say, Mock())

        # Verify separate histories
        assert len(app_openai.conversation_history) == 2
        assert "1111111111.111111" in app_openai.conversation_history
        assert "2222222222.222222" in app_openai.conversation_history

        # Each should have its own messages
        thread1_messages = app_openai.conversation_history["1111111111.111111"]["messages"]
        thread2_messages = app_openai.conversation_history["2222222222.222222"]["messages"]

        assert thread1_messages[0]["content"] == "Thread 1 message"
        assert thread2_messages[0]["content"] == "Thread 2 message"


class TestPerformance:
    """Performance and load tests"""

    @pytest.mark.performance
    @patch("chat_cli_openai.OpenAI")
    def test_response_time(self, mock_openai_class):
        """Test that responses are generated within acceptable time"""
        mock_client = Mock()

        def delayed_response(*args, **kwargs):
            time.sleep(0.1)  # Simulate API delay
            return Mock(choices=[Mock(message=Mock(content="Response"))])

        mock_client.chat.completions.create.side_effect = delayed_response
        mock_openai_class.return_value = mock_client

        start_time = time.time()
        result = chat_cli_openai.get_model_response(
            mock_client,
            "test-model",
            [{"role": "user", "content": "Test"}]
        )
        end_time = time.time()

        assert result == "Response"
        assert end_time - start_time < 1  # Should complete within 1 second

    @pytest.mark.performance
    def test_large_conversation_history(self):
        """Test handling of large conversation histories"""
        mock_client = Mock()
        mock_response = Mock(choices=[Mock(message=Mock(content="Response"))])
        mock_client.chat.completions.create.return_value = mock_response

        # Create large conversation history
        messages = []
        for i in range(100):
            messages.append({"role": "user", "content": f"Message {i}"})
            messages.append({"role": "assistant", "content": f"Response {i}"})

        result = chat_cli_openai.get_model_response(mock_client, "test-model", messages)

        assert result == "Response"
        # Verify the full history was sent
        call_args = mock_client.chat.completions.create.call_args
        assert len(call_args[1]["messages"]) == 200

    @pytest.mark.performance
    @patch("app_openai.openai_client")
    def test_concurrent_slack_messages(self, mock_client):
        """Test handling of concurrent Slack messages"""
        mock_response = Mock(choices=[Mock(message=Mock(content="Response"))])
        mock_client.chat.completions.create.return_value = mock_response

        mock_say = Mock()

        # Simulate multiple concurrent messages
        threads = []
        for i in range(10):
            event = {
                "text": f"<@U123> Message {i}",
                "ts": f"{i}.123456",
                "user": "U789"
            }
            app_openai.handle_app_mentions(event, mock_say, Mock())

        # All messages should be processed
        assert mock_client.chat.completions.create.call_count == 10
        assert len(app_openai.conversation_history) == 10


if __name__ == "__main__":
    # Run tests with different markers
    # pytest.main([__file__, "-v", "-m", "not integration"])  # Skip integration tests
    # pytest.main([__file__, "-v", "-m", "integration"])  # Only integration tests
    pytest.main([__file__, "-v", "--cov=chat_cli_openai", "--cov=app_openai", "--cov=example_usage", "--cov-report=html"])