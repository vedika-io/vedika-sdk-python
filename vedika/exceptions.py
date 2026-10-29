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

    def __init__(self, message: str, status_code: int = None, code: str = None):
        self.message = message
        self.status_code = status_code
        # The API's machine-readable ``code`` (for example ``INSUFFICIENT_BALANCE``
        # or ``DAILY_LIMIT_EXCEEDED``) when the response carried one.
        self.code = code
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
    - Check that your key starts with vk_live_ (or vk_ent_ for enterprise keys)
    - Ensure you haven't accidentally exposed your key

    Example:
        >>> try:
        ...     client = VedikaClient(api_key="invalid_key")
        ... except AuthenticationError:
        ...     print("Please provide a valid API key")
    """

    def __init__(self, message: str = "Invalid API key", code: str = None):
        super().__init__(message, status_code=401, code=code)


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

    Limits depend on your plan. The API tells the two cases apart with the
    body ``code``: ``RATE_LIMIT_EXCEEDED`` is the per-minute limit and clears
    after ``retry_after`` seconds (the SDK waits for it and retries within
    ``max_retries``); ``DAILY_LIMIT_EXCEEDED`` raises :class:`DailyLimitError`
    and is never retried.

    Example:
        >>> try:
        ...     response = client.ask_question(...)
        ... except DailyLimitError:
        ...     print("Daily allowance used up; upgrade or wait for the reset")
        ... except RateLimitError as e:
        ...     print(f"Still rate limited after retries; wait {e.retry_after}s")
    """

    def __init__(self, message: str = "Rate limit exceeded", code: str = None, retry_after: float = None):
        super().__init__(message, status_code=429, code=code)
        # Seconds the API asked the caller to wait, when it said.
        self.retry_after = retry_after


class DailyLimitError(RateLimitError):
    """
    A call allowance is used up and will not clear within seconds: the plan's
    daily allowance (``DAILY_LIMIT_EXCEEDED``), the plan limit
    (``PLAN_LIMIT_EXCEEDED``) or the account's monthly spend limit
    (``MONTHLY_SPEND_LIMIT_REACHED``).

    Waiting a few seconds does not help: the allowance resets later in the day
    (the response's ``retryAfter`` is only an estimate), and the monthly spend
    limit clears only when the UTC month rolls over or the account owner raises
    or removes it under Billing. The SDK never retries this error. Read ``code``
    to tell the cases apart. Catch :class:`RateLimitError` to handle both kinds
    of 429, or this subclass to tell them apart.
    """


class InsufficientCreditsError(VedikaAPIError):
    """
    Insufficient credits in account.

    Raised when:
    - Account has run out of credits
    - Query would exceed available credits

    Solution:
    - Upgrade your plan at https://vedika.io/pricing
    - Check your wallet balance before making requests

    A 402 is never retried: the API refused the call before charging, and a
    retry cannot succeed until the wallet is topped up. The wallet figures from
    the response are on the exception (USD): ``required``, ``available`` and
    ``deficit``, plus ``purchase_url``.

    Example:
        >>> try:
        ...     response = client.ask_question(...)
        ... except InsufficientCreditsError as e:
        ...     print(f"Need ${e.required}, have ${e.available}; top up ${e.deficit}")
    """

    def __init__(
        self,
        message: str = "Insufficient credits",
        code: str = None,
        required: float = None,
        available: float = None,
        deficit: float = None,
        purchase_url: str = None,
    ):
        super().__init__(message, status_code=402, code=code)
        # Wallet figures in USD from the 402 body (``wallet.required``,
        # ``wallet.available``, ``wallet.deficit``); ``None`` when not sent.
        self.required = required
        self.available = available
        self.deficit = deficit
        self.purchase_url = purchase_url


class SubscriptionExpiredError(VedikaAPIError):
    """
    Subscription expired — the billing period has ended.

    Both ``SUBSCRIPTION_EXPIRED`` and plain ``INSUFFICIENT_BALANCE`` return
    HTTP 402 on the Vedika API. The SDK branches on the
    server's ``code`` field so callers can distinguish:

    - ``SubscriptionExpiredError``: direct user to renew the subscription
    - ``InsufficientCreditsError``: direct user to top up their wallet

    Raised when server returns ``code == 'SUBSCRIPTION_EXPIRED'`` on a 402.

    Example:
        >>> try:
        ...     response = client.ask_question(...)
        ... except SubscriptionExpiredError:
        ...     print("Please renew at https://vedika.io/dashboard")
        ... except InsufficientCreditsError:
        ...     print("Please add credits at https://vedika.io/dashboard")
    """

    def __init__(self, message: str = "Subscription expired", code: str = None):
        super().__init__(message, status_code=402, code=code)


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

    def __init__(self, message: str = "Validation error", code: str = None):
        super().__init__(message, status_code=422, code=code)


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

    Response time depends on the route, request complexity, answer length and
    selected tier. Configure timeouts for your application; tier names do not
    guarantee a fixed duration.

    Example:
        >>> # Increase timeout for complex queries
        >>> client = VedikaClient(
        ...     api_key="vk_live_...",
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

    Raised for HTTP 503 ``PRO_ULTRA_UNAVAILABLE`` (as
    :class:`ProUltraUnavailableError`). Any other 5xx response raises
    :class:`VedikaAPIError` with ``status_code`` set.

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

    def __init__(self, message: str = "Internal server error", status_code: int = 500, code: str = None):
        super().__init__(message, status_code=status_code, code=code)


class ProUltraUnavailableError(ServerError):
    """
    The Pro Ultra tier cannot serve right now (HTTP 503, ``code``
    ``PRO_ULTRA_UNAVAILABLE``).

    The API refuses the request before it bills anything, so you are never
    charged, and no other tier answers in its place. It is a :class:`ServerError`,
    so existing ``except ServerError`` handling still catches it.

    The SDK retries it like any other 503: only a call that carries an
    idempotency key (every ``ask_question`` call does) is sent again, up to
    ``max_retries``, waiting the API's ``Retry-After``. ``ask_question_stream``
    is never retried. If Pro Ultra is still unavailable after that, wait
    ``retry_after`` seconds, or send the question on another tier yourself
    with ``speed``.

    Example:
        >>> try:
        ...     client.ask_question("Career?", birth_details, speed="pro-ultra")
        ... except ProUltraUnavailableError as e:
        ...     print(f"Pro Ultra is unavailable; try again in {e.retry_after or 5}s")
    """

    def __init__(
        self,
        message: str = "Vedika Pro Ultra is temporarily unavailable",
        code: str = "PRO_ULTRA_UNAVAILABLE",
        retry_after: float = None,
    ):
        super().__init__(message, status_code=503, code=code)
        # Seconds the API asked the caller to wait, when it said.
        self.retry_after = retry_after


class OutputBudgetExhaustedError(VedikaAPIError):
    """
    A Pro Ultra question used its whole output budget before any answer text was
    written (HTTP 400, ``code`` ``OUTPUT_BUDGET_EXHAUSTED``). You are not charged.

    It is only raised when the request had no birth chart to answer from. With a
    chart, the same event is a normal response whose ``finish_reason`` is
    ``"length"``, with ``truncated`` and ``degraded`` set and ``degraded_reason``
    ``"budget_truncated"``; that is not charged either.

    The SDK never retries it and never raises ``max_tokens`` for you: the same
    request would end the same way. Retry with a higher ``max_tokens``, or set
    ``detail="brief"``.

    Example:
        >>> try:
        ...     client.ask_question("Career?", birth_details, speed="pro-ultra", max_tokens=200)
        ... except OutputBudgetExhaustedError as e:
        ...     print(e.message)
    """

    def __init__(
        self,
        message: str = "The output budget for this request was used up before an answer was written",
        code: str = "OUTPUT_BUDGET_EXHAUSTED",
    ):
        super().__init__(message, status_code=400, code=code)


class QuestionErrorCode:
    """
    The ``code`` values the AI question routes return for the delivery tier and
    answer-length controls. Compare them with ``error.code``:

        >>> if e.code == QuestionErrorCode.CONTROL_UNSUPPORTED_FOR_TIER: ...

    - ``CONTROL_UNSUPPORTED_FOR_TIER`` (400): a control the selected tier cannot
      honour, such as ``seed`` on ``"pro-ultra"``. Refused before billing.
    - ``INVALID_DETAIL`` (400): ``detail`` is not "brief", "standard" or "detailed".
    - ``INVALID_STOP`` (400): ``stop`` is not 1 to 4 strings of 1 to 64 characters.
    - ``STOP_MATCHED_BEFORE_ANSWER`` (400): a ``stop`` sequence matched before any
      answer text was written. Not charged; change or remove ``stop``. On a stream
      it arrives as an ``error`` event.
    - ``DETAIL_BUDGET_CONFLICT`` (400): ``detail="detailed"`` with ``max_tokens``
      below 384 (not on ``"eco"``).
    - ``OUTPUT_BUDGET_EXHAUSTED`` (400): see :class:`OutputBudgetExhaustedError`.
    - ``PRO_ULTRA_UNAVAILABLE`` (503): see :class:`ProUltraUnavailableError`.
    - ``ECO_UNAVAILABLE`` (503): the "eco" tier cannot serve right now.
    - ``VERSION_UNAVAILABLE`` (503): the "2.5" standard version cannot serve right now.

    None of these is charged. A ``version`` sent with a speed other than
    standard, or a ``version`` other than "2" or "2.5", is a 400 with code
    ``VALIDATION_ERROR``.
    """

    CONTROL_UNSUPPORTED_FOR_TIER = "CONTROL_UNSUPPORTED_FOR_TIER"
    INVALID_DETAIL = "INVALID_DETAIL"
    INVALID_STOP = "INVALID_STOP"
    STOP_MATCHED_BEFORE_ANSWER = "STOP_MATCHED_BEFORE_ANSWER"
    DETAIL_BUDGET_CONFLICT = "DETAIL_BUDGET_CONFLICT"
    OUTPUT_BUDGET_EXHAUSTED = "OUTPUT_BUDGET_EXHAUSTED"
    PRO_ULTRA_UNAVAILABLE = "PRO_ULTRA_UNAVAILABLE"
    ECO_UNAVAILABLE = "ECO_UNAVAILABLE"
    VERSION_UNAVAILABLE = "VERSION_UNAVAILABLE"


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
# ├── InsufficientCreditsError (402) — wallet underrun
# ├── SubscriptionExpiredError (402) — billing period ended
# ├── TimeoutError (408)
# ├── ValidationError (422)
# ├── RateLimitError (429)
# │   └── DailyLimitError (429, never retried)
# ├── ServerError (raised for 503 PRO_ULTRA_UNAVAILABLE; other 5xx raise VedikaAPIError with status_code)
# │   └── ProUltraUnavailableError (503 PRO_ULTRA_UNAVAILABLE)
# ├── OutputBudgetExhaustedError (400 OUTPUT_BUDGET_EXHAUSTED)
# └── NetworkError (connection issues)
