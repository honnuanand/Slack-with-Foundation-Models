"""
Pytest fixtures and configuration for all tests
Provides reusable test components and setup/teardown logic
"""

import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def clean_env():
    """Provide a clean environment for each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def databricks_env(clean_env):
    """Set up Databricks environment variables"""
    os.environ.update({
        "MODE": "databricks",
        "DATABRICKS_HOST": "https://test.databricks.com",
        "DATABRICKS_TOKEN": "test-databricks-token"
    })
    yield os.environ


@pytest.fixture
def openai_env(clean_env):
    """Set up OpenAI environment variables"""
    os.environ.update({
        "MODE": "openai",
        "OPENAI_API_KEY": "sk-test-openai-key"
    })
    yield os.environ


@pytest.fixture
def slack_env(clean_env):
    """Set up Slack environment variables"""
    os.environ.update({
        "SLACK_BOT_TOKEN": "xoxb-test-bot-token",
        "SLACK_APP_TOKEN": "xapp-test-app-token"
    })
    yield os.environ


@pytest.fixture
def full_databricks_env(databricks_env, slack_env):
    """Complete environment for Databricks + Slack"""
    yield os.environ


@pytest.fixture
def full_openai_env(openai_env, slack_env):
    """Complete environment for OpenAI + Slack"""
    yield os.environ


# ============================================================================
# Mock Objects Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with common setup"""
    client = Mock()
    response = Mock()
    response.choices = [Mock(message=Mock(content="Test response"))]
    client.chat.completions.create.return_value = response
    return client


@pytest.fixture
def mock_openai_client_with_error():
    """Mock OpenAI client that raises errors"""
    client = Mock()
    client.chat.completions.create.side_effect = Exception("API Error")
    return client


@pytest.fixture
def mock_slack_say():
    """Mock Slack say function"""
    return Mock()


@pytest.fixture
def mock_slack_ack():
    """Mock Slack ack function"""
    return Mock()


@pytest.fixture
def mock_slack_client():
    """Mock Slack client"""
    return Mock()


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_messages():
    """Sample conversation messages"""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "What can you help me with?"}
    ]


@pytest.fixture
def sample_slack_event():
    """Sample Slack mention event"""
    return {
        "type": "app_mention",
        "user": "U123456789",
        "text": "<@U987654321> Hello bot!",
        "ts": "1234567890.123456",
        "channel": "C123456789",
        "event_ts": "1234567890.123456"
    }


@pytest.fixture
def sample_slack_event_with_thread():
    """Sample Slack mention event in a thread"""
    return {
        "type": "app_mention",
        "user": "U123456789",
        "text": "<@U987654321> Follow up question",
        "ts": "1234567890.234567",
        "thread_ts": "1234567890.123456",
        "channel": "C123456789",
        "event_ts": "1234567890.234567"
    }


@pytest.fixture
def sample_slack_dm_event():
    """Sample Slack direct message event"""
    return {
        "type": "message",
        "channel_type": "im",
        "user": "U123456789",
        "text": "Hello bot!",
        "ts": "1234567890.123456",
        "channel": "D123456789"
    }


@pytest.fixture
def sample_slack_command():
    """Sample Slack slash command"""
    return {
        "token": "verification_token",
        "team_id": "T123456",
        "team_domain": "test-team",
        "channel_id": "C123456789",
        "channel_name": "general",
        "user_id": "U123456789",
        "user_name": "testuser",
        "command": "/aichat",
        "text": "What is Python?",
        "response_url": "https://hooks.slack.com/commands/1234/5678",
        "trigger_id": "123456789.123456789.abcd"
    }


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def temp_env_file(temp_dir):
    """Create a temporary .env file"""
    env_path = os.path.join(temp_dir, ".env")
    with open(env_path, "w") as f:
        f.write("MODE=databricks\n")
        f.write("DATABRICKS_HOST=https://test.databricks.com\n")
        f.write("DATABRICKS_TOKEN=test-token\n")
    return env_path


# ============================================================================
# Patch Fixtures
# ============================================================================

@pytest.fixture
def patch_openai_class():
    """Patch OpenAI class"""
    with patch("openai.OpenAI") as mock_class:
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked response"))]
        mock_instance.chat.completions.create.return_value = mock_response
        mock_class.return_value = mock_instance
        yield mock_class


@pytest.fixture
def patch_input():
    """Patch built-in input function"""
    with patch("builtins.input") as mock_input:
        yield mock_input


@pytest.fixture
def patch_print():
    """Patch built-in print function"""
    with patch("builtins.print") as mock_print:
        yield mock_print


# ============================================================================
# Utility Functions
# ============================================================================

@pytest.fixture
def capture_logs():
    """Capture log messages during tests"""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    # Get all loggers
    loggers = [
        logging.getLogger("app_openai"),
        logging.getLogger("chat_cli_openai"),
        logging.getLogger()
    ]

    for logger in loggers:
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    yield log_capture

    for logger in loggers:
        logger.removeHandler(handler)


@pytest.fixture
def mock_time():
    """Mock time for performance tests"""
    with patch("time.time") as mock_time_func:
        mock_time_func.return_value = 1234567890.0
        yield mock_time_func


# ============================================================================
# Test Markers and Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "skip_ci: mark test to skip in CI/CD"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Auto-mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Auto-mark performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)

        # Auto-mark unit tests
        if "unit" in item.nodeid or "Test" in item.nodeid:
            if not any(mark.name in ["integration", "performance"] for mark in item.iter_markers()):
                item.add_marker(pytest.mark.unit)