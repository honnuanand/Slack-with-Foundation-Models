# Test Suite Documentation

## Overview

This directory contains comprehensive test suites for the Slack Foundation Models project. The tests cover all major components including CLI interfaces, Slack bot functionality, API integrations, and example usage.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_chat_cli_openai.py    # Tests for flexible CLI interface
├── test_app_openai.py         # Tests for Slack bot
├── test_example_usage.py      # Tests for example script
└── test_integration.py        # Integration and end-to-end tests
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual functions and methods in isolation
- **Coverage**: Core functions like `get_model_response()`, environment handling, model selection
- **Mocking**: External API calls are mocked to ensure fast, reliable tests
- **Files**: All `test_*.py` files contain unit tests

### Integration Tests
- **Purpose**: Test actual API interactions and end-to-end workflows
- **Requirements**: May require API credentials (can be skipped if not available)
- **Coverage**: Real API calls, multi-component interactions
- **Marker**: `@pytest.mark.integration`

### Performance Tests
- **Purpose**: Test response times and load handling
- **Coverage**: Large conversation histories, concurrent requests
- **Marker**: `@pytest.mark.performance`

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock pytest-timeout
```

Or use the test runner:
```bash
python run_tests.py install
```

### Basic Test Execution

#### Run all tests
```bash
pytest tests/
```

#### Run with coverage report
```bash
pytest tests/ --cov --cov-report=html
```

#### Run specific test file
```bash
pytest tests/test_chat_cli_openai.py
```

#### Run specific test
```bash
pytest tests/test_chat_cli_openai.py::TestColors::test_color_codes
```

### Using the Test Runner

The `run_tests.py` script provides convenient test execution options:

#### Run all tests with coverage
```bash
python run_tests.py all
```

#### Run only unit tests
```bash
python run_tests.py unit
```

#### Run integration tests
```bash
python run_tests.py integration
```

#### Run performance tests
```bash
python run_tests.py performance
```

#### Quick check (fast tests only)
```bash
python run_tests.py quick
```

#### CI/CD compatible tests
```bash
python run_tests.py ci
```

#### Generate coverage reports
```bash
python run_tests.py coverage
```

#### Check test quality metrics
```bash
python run_tests.py quality
```

#### Create comprehensive test report
```bash
python run_tests.py report
```

### Test Markers

Tests are organized with markers for selective execution:

- `unit`: Unit tests (default for most tests)
- `integration`: Tests requiring external services
- `performance`: Performance and load tests
- `slow`: Tests that take longer to run
- `skip_ci`: Tests to skip in CI/CD pipelines

Run tests by marker:
```bash
# Only unit tests
pytest tests/ -m unit

# Only integration tests
pytest tests/ -m integration

# Exclude slow tests
pytest tests/ -m "not slow"

# CI-friendly tests
pytest tests/ -m "not skip_ci"
```

## Test Coverage

### Current Coverage Areas

1. **Environment Configuration**
   - MODE switching (Databricks vs OpenAI)
   - Environment variable validation
   - Missing credentials handling

2. **API Integration**
   - OpenAI client initialization
   - Databricks client initialization
   - API call error handling
   - Response parsing

3. **CLI Functionality**
   - User input handling
   - Command processing (quit, clear, switch)
   - Model selection
   - Conversation history management

4. **Slack Bot Features**
   - Event handlers (app_mention, message, slash commands)
   - Thread management
   - Multi-model support
   - Error recovery

5. **Edge Cases**
   - Empty inputs
   - API timeouts
   - Rate limiting
   - Network errors
   - Invalid credentials

### Coverage Reports

After running tests with coverage, view reports:

- **Terminal**: Shown automatically with `--cov` flag
- **HTML**: Open `htmlcov/index.html` in browser
- **XML**: `coverage.xml` for CI/CD tools
- **JSON**: `coverage.json` for programmatic access

### Coverage Goals

- **Target**: 80% minimum coverage
- **Current**: Run `pytest --cov` to check
- **Excluded**: Test files, virtual environments, configuration files

## Test Fixtures

Common fixtures provided in `conftest.py`:

### Environment Fixtures
- `clean_env`: Clean environment for each test
- `databricks_env`: Databricks configuration
- `openai_env`: OpenAI configuration
- `slack_env`: Slack configuration

### Mock Fixtures
- `mock_openai_client`: Pre-configured OpenAI client mock
- `mock_slack_say`: Slack say function mock
- `sample_messages`: Example conversation messages
- `sample_slack_event`: Example Slack events

### Usage Example
```python
def test_with_databricks_env(databricks_env, mock_openai_client):
    """Test using Databricks environment and mocked client"""
    # Your test code here
    pass
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        python run_tests.py install
    - name: Run tests
      run: python run_tests.py ci
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## Best Practices

### Writing New Tests

1. **Use descriptive names**: `test_api_error_handling_returns_formatted_message`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **One assertion per test** (when possible)
4. **Use fixtures** for common setup
5. **Mock external dependencies**
6. **Test both success and failure cases**

### Test Organization

1. **Group related tests** in classes
2. **Use markers** for categorization
3. **Keep tests independent** (no test should depend on another)
4. **Clean up** resources in teardown

### Debugging Tests

#### Run with verbose output
```bash
pytest tests/ -v
```

#### Show print statements
```bash
pytest tests/ -s
```

#### Debug specific test
```bash
pytest tests/test_file.py::TestClass::test_method --pdb
```

#### Show local variables on failure
```bash
pytest tests/ -l
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure parent directory is in Python path
2. **Missing dependencies**: Run `python run_tests.py install`
3. **API credential errors**: Set environment variables or use mocks
4. **Timeout errors**: Increase timeout in pytest.ini

### Environment Setup

For integration tests, create a `.env.test` file:
```env
# For Databricks mode
MODE=databricks
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token

# For OpenAI mode
MODE=openai
OPENAI_API_KEY=sk-your-key

# For Slack bot
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
```

Load in tests:
```python
from dotenv import load_dotenv
load_dotenv('.env.test')
```

## Contributing

### Adding New Tests

1. Create test file following naming convention: `test_*.py`
2. Import necessary modules and fixtures
3. Write test cases with clear documentation
4. Run tests locally before committing
5. Ensure coverage doesn't decrease

### Test Review Checklist

- [ ] Tests pass locally
- [ ] Coverage maintained or improved
- [ ] No hardcoded credentials
- [ ] Proper use of fixtures
- [ ] Clear test names and documentation
- [ ] Both positive and negative cases covered
- [ ] Appropriate markers applied

## Support

For questions or issues with tests:
1. Check this documentation
2. Review existing test examples
3. Check pytest documentation
4. Open an issue with test output and environment details