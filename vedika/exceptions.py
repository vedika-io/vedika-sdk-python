"""
Vedika API Exceptions
Custom exception classes for the Vedika Astrology API.
"""


class VedikaAPIError(Exception):
    """
    Base exception for all Vedika API errors.

    This is the parent class for all Vedika SDK exceptions.
    Catch this to handle any SDK-related error.

    Example:
        >>> try:
        ...     response = client.ask_question(...)
        ... except VedikaAPIError as e:
        ...     print(f"API error: {e}")
    """

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[HTTP {self.status_code}] {self.message}"
        return self.message


class AuthenticationError(VedikaAPIError):
    """
    Authentication failed - invalid API key.

    Raised when:
    - API key is missing
    - API key is invalid
    - API key is expired

    Solution:
    - Get a valid API key from https://vedika.io/dashboard.html
    - Check that your key starts with vk_test_ or vk_live_
    - Ensure you haven't accidentally exposed your key

    Example:
        >>> try:
        ...     client = VedikaClient(api_key="invalid_key")
        ... except AuthenticationError:
        ...     print("Please provide a valid API key")
    """

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, status_code=401)


class RateLimitError(VedikaAPIError):
    """
    Rate limit exceeded.

    Raised when:
    - Too many requests in a short time period
    - Account rate limit reached

    Solution:
    - Wait a moment before retrying
    - Implement exponential backoff
    - Upgrade your plan for higher limits

    Rate limits:
    - Free tier: 10 requests/minute
    - Starter: 60 requests/minute
    - Professional: 300 requests/minute
    - Enterprise: Custom limits

    Example:
        >>> import time
        >>> try:
        ...     response = client.ask_question(...)
        ... except RateLimitError:
        ...     time.sleep(60)  # Wait 1 minute
        ...     response = client.ask_question(...)  # Retry
    """

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class InsufficientCreditsError(VedikaAPIError):
    """
    Insufficient credits in account.

    Raised when:
    - Account has run out of credits
    - Query would exceed available credits

    Solution:
    - Add more credits at https://vedika.io/dashboard.html
    - Check your credit balance before making requests
    - Add funds at xalen.io/dashboard to continue

    Credit costs:
    - Simple queries: ~500 tokens ($0.19)
    - Standard queries: ~800 tokens ($0.35)
    - Complex queries: ~1,500 tokens ($0.65)

    Example:
        >>> try:
        ...     response = client.ask_question(...)
        ... except InsufficientCreditsError:
        ...     print("Please add credits at https://vedika.io/dashboard.html")
    """

    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(message, status_code=402)


class ValidationError(VedikaAPIError):
    """
    Request validation failed - invalid input.

    Raised when:
    - Birth details are invalid or missing
    - Date/time format is incorrect
    - Latitude/longitude out of range
    - Required fields are missing

    Solution:
    - Check that datetime is in ISO 8601 format
    - Verify latitude is between -90 and 90
    - Verify longitude is between -180 and 180
    - Ensure timezone is a valid IANA timezone

    Valid input examples:
    - datetime: "1990-06-15T14:30:00+05:30"
    - latitude: 28.6139 (Delhi)
    - longitude: 77.2090 (Delhi)
    - timezone: "Asia/Kolkata"

    Example:
        >>> try:
        ...     response = client.ask_question(
        ...         question="Career prospects?",
        ...         birth_details={
        ...             "datetime": "invalid-date",  # Wrong format!
        ...             "latitude": 28.6139,
        ...             "longitude": 77.2090
        ...         }
        ...     )
        ... except ValidationError as e:
        ...     print(f"Invalid input: {e}")
    """

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class TimeoutError(VedikaAPIError):
    """
    Request timeout - server took too long to respond.

    Raised when:
    - Request exceeds configured timeout
    - Complex query takes longer than expected
    - Server is experiencing high load

    Solution:
    - Increase timeout for complex queries
    - Retry the request
    - Contact support if issue persists

    Typical response times:
    - Simple queries: 2-5 seconds
    - Standard queries: 5-15 seconds
    - Complex queries: 20-40 seconds

    Example:
        >>> # Increase timeout for complex queries
        >>> client = VedikaClient(
        ...     api_key="vk_test_...",
        ...     timeout=120  # 2 minutes
        ... )
        >>>
        >>> try:
        ...     response = client.ask_question(
        ...         question="Comprehensive life analysis",
        ...         birth_details=birth_info
        ...     )
        ... except TimeoutError:
        ...     print("Query timed out, please try again")
    """

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, status_code=408)


class ServerError(VedikaAPIError):
    """
    Internal server error.

    Raised when:
    - Server encountered an unexpected error
    - Service is temporarily unavailable
    - Database or ephemeris error

    Solution:
    - Retry the request (automatic with SDK)
    - Wait a few moments if service is down
    - Contact support@vedika.io if issue persists

    The SDK automatically retries failed requests up to 3 times
    with exponential backoff.

    Example:
        >>> try:
        ...     response = client.ask_question(...)
        ... except ServerError:
        ...     print("Server error, please try again later")
    """

    def __init__(self, message: str = "Internal server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class NetworkError(VedikaAPIError):
    """
    Network connectivity error.

    Raised when:
    - Cannot connect to Vedika API server
    - Network timeout
    - DNS resolution failure

    Solution:
    - Check your internet connection
    - Verify firewall settings allow HTTPS
    - Check if vedika.io is accessible
    - Try again in a few moments

    Example:
        >>> try:
        ...     response = client.ask_question(...)
        ... except NetworkError:
        ...     print("Network error, check your connection")
    """

    def __init__(self, message: str = "Network error"):
        super().__init__(message)


# Exception hierarchy for easy catching:
#
# VedikaAPIError (base)
# ├── AuthenticationError (401)
# ├── InsufficientCreditsError (402)
# ├── TimeoutError (408)
# ├── ValidationError (422)
# ├── RateLimitError (429)
# ├── ServerError (500+)
# └── NetworkError (connection issues)
