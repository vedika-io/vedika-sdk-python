# Contributing to Vedika Python SDK

Thank you for your interest in contributing to the Vedika Python SDK! We welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, error messages)
- **Describe the behavior you observed** and what you expected
- **Include your environment details** (Python version, OS, SDK version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful** to most users
- **List some examples** of how it would be used

### Pull Requests

We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the style guide
6. Submit your pull request!

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- virtualenv (recommended)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/vedika-sdk-python.git
cd vedika-sdk-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Project Structure

```
vedika-sdk-python/
├── vedika/              # Main package
│   ├── __init__.py      # Package exports
│   ├── client.py        # VedikaClient class
│   ├── models.py        # Data models
│   └── exceptions.py    # Custom exceptions
├── tests/               # Test suite
├── examples/            # Example scripts
├── docs/                # Documentation
└── setup.py             # Package configuration
```

## Pull Request Process

1. **Update documentation**: If you've changed APIs or added features, update the README.md and docstrings
2. **Add tests**: Ensure your changes are covered by tests
3. **Run tests**: Make sure all tests pass
4. **Update CHANGELOG.md**: Add a note about your changes under "Unreleased"
5. **Follow code style**: Use Black for formatting, flake8 for linting
6. **Write clear commit messages**: Use conventional commit format

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(client): add support for batch queries
fix(models): handle null values in birth chart response
docs(readme): update installation instructions
```

## Style Guide

### Python Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Formatting**: Use [Black](https://black.readthedocs.io/)
- **Linting**: Use [flake8](https://flake8.pycqa.org/)
- **Type hints**: Use type hints for all function signatures
- **Docstrings**: Use Google-style docstrings

### Code Formatting

```bash
# Format code with Black
black vedika/ tests/

# Check with flake8
flake8 vedika/ tests/

# Type check with mypy
mypy vedika/
```

### Example Code

```python
from typing import Dict, Any, Optional


def example_function(
    param1: str,
    param2: int,
    param3: Optional[Dict[str, Any]] = None
) -> str:
    """
    Brief description of the function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2
        param3: Description of param3 (optional)

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative

    Example:
        >>> result = example_function("test", 42)
        >>> print(result)
        'test-42'
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")

    return f"{param1}-{param2}"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vedika --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::test_ask_question
```

### Writing Tests

- Use pytest for testing
- Aim for >90% code coverage
- Test both success and failure cases
- Use fixtures for common setup
- Mock external API calls

Example test:

```python
import pytest
from vedika import VedikaClient
from vedika.exceptions import AuthenticationError


def test_client_requires_api_key():
    """Test that VedikaClient raises error without API key."""
    with pytest.raises(AuthenticationError):
        VedikaClient(api_key=None)


def test_ask_question_success(mock_api_response):
    """Test successful question query."""
    client = VedikaClient(api_key="vk_test_key")
    response = client.ask_question(
        question="Test question",
        birth_details={
            "datetime": "1990-06-15T14:30:00+05:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
    )

    assert response.answer is not None
    assert response.confidence > 0
```

## Documentation

### Docstring Guidelines

Use Google-style docstrings:

```python
def function_name(arg1: str, arg2: int) -> bool:
    """
    Brief description (one line).

    Longer description if needed (can be multiple paragraphs).

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When arguments are invalid

    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
```

### README Updates

If you add new features:

1. Update the feature list in README.md
2. Add code examples showing usage
3. Update the table of contents if needed

## Questions?

- Open an issue for questions
- Email support@vedika.io
- Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Vedika! 🙏
