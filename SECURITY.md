# Security Policy

## Supported Versions

We release security updates for the following versions of the Vedika Python SDK:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of the Vedika Python SDK seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do Not:

- Open a public GitHub issue for security vulnerabilities
- Post about the vulnerability in public forums or social media
- Attempt to exploit the vulnerability beyond verifying its existence

### Please Do:

**Report security vulnerabilities to: security@vedika.io**

Include the following information:

1. **Type of vulnerability** (e.g., authentication bypass, API key exposure, injection attack)
2. **Full description** of the vulnerability
3. **Steps to reproduce** the issue
4. **Potential impact** of the vulnerability
5. **Suggested fix** (if you have one)
6. **Your contact information** for follow-up

### What to Expect:

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Updates**: We will send you regular updates about our progress
- **Timeline**: We aim to release a fix within 7-14 days for critical vulnerabilities
- **Credit**: We will credit you in our security advisory (unless you prefer to remain anonymous)

## Security Best Practices

### API Key Management

**Never expose your API keys:**

```python
# ❌ DON'T: Hardcode API keys
client = VedikaClient(api_key="vk_live_your_actual_key")

# ✅ DO: Use environment variables
import os
client = VedikaClient(api_key=os.getenv("VEDIKA_API_KEY"))
```

**Use .gitignore:**

```bash
# Add to .gitignore
.env
.env.local
*.key
credentials.json
```

**Rotate compromised keys immediately:**

If you accidentally expose your API key:
1. Immediately revoke it at https://vedika.io/dashboard.html
2. Generate a new key
3. Update your application with the new key
4. Review API logs for unauthorized usage

### Input Validation

**Always validate user input:**

```python
from datetime import datetime

def validate_birth_details(details: dict) -> bool:
    """Validate birth details before sending to API."""
    required_fields = ['datetime', 'latitude', 'longitude']

    # Check required fields
    if not all(field in details for field in required_fields):
        return False

    # Validate latitude (-90 to 90)
    if not -90 <= details['latitude'] <= 90:
        return False

    # Validate longitude (-180 to 180)
    if not -180 <= details['longitude'] <= 180:
        return False

    # Validate datetime format
    try:
        datetime.fromisoformat(details['datetime'].replace('Z', '+00:00'))
    except ValueError:
        return False

    return True
```

### HTTPS Only

The SDK enforces HTTPS for all API requests. Never modify the base URL to use HTTP:

```python
# ✅ HTTPS (default and required)
client = VedikaClient(
    api_key=os.getenv("VEDIKA_API_KEY"),
    base_url="https://vedika-api-854222120654.us-central1.run.app"
)

# ❌ HTTP (will fail)
# DO NOT attempt to use HTTP
```

### Rate Limiting

Respect rate limits to prevent account suspension:

```python
import time
from vedika.exceptions import RateLimitError

def safe_api_call(client, *args, **kwargs):
    """Make API call with exponential backoff on rate limit."""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            return client.ask_question(*args, **kwargs)
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise
```

### Error Handling

Never expose sensitive information in error messages:

```python
try:
    response = client.ask_question(...)
except Exception as e:
    # ❌ DON'T: Log full error with potentially sensitive data
    # logger.error(f"API call failed: {e} with data: {birth_details}")

    # ✅ DO: Log sanitized error message
    logger.error("API call failed. Check logs for details.")
    # Store detailed error in secure logs only
```

### Dependency Security

Keep dependencies up to date:

```bash
# Check for security vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade vedika-sdk requests
```

## Known Security Considerations

### Data Privacy

- **Birth details are sensitive**: Treat birth information (date, time, location) as PII
- **No data retention**: Vedika API does not store queries unless explicitly enabled
- **GDPR compliant**: The API is GDPR compliant for EU users

### API Key Scopes

- **Test keys** (`vk_test_`): Limited functionality, safe for development
- **Live keys** (`vk_live_`): Full access, use only in production
- **Never commit keys**: Use environment variables or secret managers

### Network Security

- **TLS 1.2+**: All API requests use TLS 1.2 or higher
- **Certificate validation**: The SDK validates SSL certificates
- **No proxy support**: Direct connections only for security

## Security Audit History

| Date       | Type          | Findings | Status   |
|------------|---------------|----------|----------|
| 2025-10-15 | Code Review   | None     | Passed   |
| 2025-10-01 | Dependency    | None     | Passed   |

## Contact

For security concerns or questions:

- **Email**: security@vedika.io
- **Response time**: Within 48 hours
- **PGP Key**: Available on request

---

**Last updated**: November 2025
