"""
Vedika API Client
Main client class for interacting with the Vedika Astrology API.
"""

import os
from typing import Dict, Any, Optional, Iterator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    BirthDetails,
    QuestionResponse,
    BirthChart,
    DashaResponse,
    CompatibilityResponse,
    YogaResponse,
    DoshaResponse,
    MuhurthaResponse,
    NumerologyResponse
)
from .exceptions import (
    VedikaAPIError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError
)


class VedikaClient:
    """
    Main client for the Vedika Astrology API.

    The ONLY B2B astrology API with AI-powered chatbot queries.

    Args:
        api_key: Your Vedika API key (get one at https://vedika.io/dashboard.html)
        base_url: API base URL (default: production URL)
        timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum number of retries for failed requests (default: 3)
        cache_enabled: Enable prompt caching for cost savings (default: True)
        language: Default language for responses (default: "en")

    Example:
        >>> from vedika import VedikaClient
        >>> client = VedikaClient(api_key="vk_test_...")
        >>> response = client.ask_question(
        ...     question="What are my career prospects?",
        ...     birth_details={"datetime": "1990-06-15T14:30:00+05:30", ...}
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.vedika.io",
        timeout: int = 60,
        max_retries: int = 3,
        cache_enabled: bool = True,
        language: str = "en"
    ):
        self.api_key = api_key or os.getenv("VEDIKA_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Get one at https://vedika.io/dashboard.html"
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self.language = language

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": f"vedika-python-sdk/1.0.0"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )

            # Handle specific HTTP errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 402:
                raise InsufficientCreditsError("Insufficient credits. Add more at https://vedika.io/dashboard.html")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please wait a moment.")
            elif response.status_code == 422:
                raise ValidationError(f"Validation error: {response.json().get('message', 'Invalid input')}")
            elif response.status_code >= 400:
                error_msg = response.json().get("message", "API request failed")
                raise VedikaAPIError(f"HTTP {response.status_code}: {error_msg}")

            return response.json()

        except requests.exceptions.Timeout:
            raise VedikaAPIError("Request timed out. For complex queries, try increasing timeout.")
        except requests.exceptions.RequestException as e:
            raise VedikaAPIError(f"Request failed: {str(e)}")

    def ask_question(
        self,
        question: str,
        birth_details: Dict[str, Any],
        language: Optional[str] = None
    ) -> QuestionResponse:
        """
        Ask a conversational astrology question (UNIQUE to Vedika!).

        This is the only B2B astrology API that supports natural language queries.

        Args:
            question: Your astrology question in natural language
            birth_details: Birth information (datetime, latitude, longitude, timezone)
            language: Response language (default: client's default language)

        Returns:
            QuestionResponse with answer, confidence, and metadata

        Example:
            >>> response = client.ask_question(
            ...     question="What are my career prospects this year?",
            ...     birth_details={
            ...         "datetime": "1990-06-15T14:30:00+05:30",
            ...         "latitude": 28.6139,
            ...         "longitude": 77.2090,
            ...         "timezone": "Asia/Kolkata"
            ...     },
            ...     language="en"
            ... )
            >>> print(response.answer)
        """
        data = {
            "question": question,
            "birthDetails": birth_details,
            "language": language or self.language
        }

        result = self._request("POST", "/api/v1/astrology/query", data=data)
        return QuestionResponse.from_dict(result)

    def ask_question_stream(
        self,
        question: str,
        birth_details: Dict[str, Any],
        language: Optional[str] = None
    ) -> Iterator[str]:
        """
        Stream conversational astrology question response in real-time.

        Args:
            question: Your astrology question
            birth_details: Birth information
            language: Response language

        Yields:
            Response chunks as they're generated

        Example:
            >>> for chunk in client.ask_question_stream(
            ...     question="What are my career prospects?",
            ...     birth_details=birth_info
            ... ):
            ...     print(chunk, end="", flush=True)
        """
        url = f"{self.base_url}/api/v1/astrology/query/stream"
        data = {
            "question": question,
            "birthDetails": birth_details,
            "language": language or self.language
        }

        with requests.post(url, json=data, headers=self.session.headers, stream=True, timeout=self.timeout) as response:
            if response.status_code != 200:
                raise VedikaAPIError(f"Stream request failed: HTTP {response.status_code}")

            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        yield decoded[6:]  # Remove 'data: ' prefix

    def get_birth_chart(
        self,
        datetime: str,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        ayanamsa: str = "lahiri"
    ) -> BirthChart:
        """
        Generate a complete birth chart.

        Args:
            datetime: Birth datetime in ISO 8601 format
            latitude: Birth location latitude
            longitude: Birth location longitude
            timezone: Timezone (default: "UTC")
            ayanamsa: Ayanamsa system (default: "lahiri")

        Returns:
            BirthChart with planets, houses, and ascendant
        """
        data = {
            "birthDetails": {
                "datetime": datetime,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone
            },
            "ayanamsa": ayanamsa
        }

        result = self._request("POST", "/api/v1/charts/birth", data=data)
        return BirthChart.from_dict(result)

    def get_dashas(
        self,
        birth_details: Dict[str, Any]
    ) -> DashaResponse:
        """
        Get Vimshottari Dasha periods.

        Args:
            birth_details: Birth information

        Returns:
            DashaResponse with mahadashas, antardashas, and pratyantardashas
        """
        result = self._request("POST", "/api/vedika/dasha-periods", data={"birthDetails": birth_details})
        return DashaResponse.from_dict(result)

    def check_compatibility(
        self,
        person1_details: Dict[str, Any],
        person2_details: Dict[str, Any]
    ) -> CompatibilityResponse:
        """
        Check marriage compatibility using Ashtakoota matching.

        Args:
            person1_details: First person's birth details
            person2_details: Second person's birth details

        Returns:
            CompatibilityResponse with score and analysis
        """
        data = {
            "person1": person1_details,
            "person2": person2_details
        }

        result = self._request("POST", "/api/v1/compatibility/match", data=data)
        return CompatibilityResponse.from_dict(result)

    def detect_yogas(
        self,
        birth_details: Dict[str, Any]
    ) -> YogaResponse:
        """
        Detect 300+ astrological yogas.

        Args:
            birth_details: Birth information

        Returns:
            YogaResponse with detected yogas and descriptions
        """
        result = self._request("POST", "/api/vedika/yoga-detection", data={"birthDetails": birth_details})
        return YogaResponse.from_dict(result)

    def analyze_doshas(
        self,
        birth_details: Dict[str, Any]
    ) -> DoshaResponse:
        """
        Analyze doshas (Kaal Sarp, Mangal, Sade Sati, etc.).

        Args:
            birth_details: Birth information

        Returns:
            DoshaResponse with dosha analysis and remedies
        """
        result = self._request("POST", "/api/vedika/dosha-analysis", data={"birthDetails": birth_details})
        return DoshaResponse.from_dict(result)

    def get_muhurtha(
        self,
        date: str,
        location: Dict[str, float],
        event_type: str
    ) -> MuhurthaResponse:
        """
        Find auspicious times (Muhurtha) for important events.

        Args:
            date: Date in YYYY-MM-DD format
            location: Location coordinates (latitude, longitude)
            event_type: Type of event (wedding, business, etc.)

        Returns:
            MuhurthaResponse with auspicious and inauspicious times
        """
        data = {
            "date": date,
            "location": location,
            "eventType": event_type
        }

        result = self._request("POST", "/api/vedika/muhurtha", data=data)
        return MuhurthaResponse.from_dict(result)

    def get_numerology(
        self,
        name: str,
        birth_date: str
    ) -> NumerologyResponse:
        """
        Get numerology analysis (37 calculations).

        Args:
            name: Full name
            birth_date: Birth date in YYYY-MM-DD format

        Returns:
            NumerologyResponse with life path, expression, and soul urge numbers
        """
        data = {
            "name": name,
            "birthDate": birth_date
        }

        result = self._request("POST", "/api/vedika/numerology", data=data)
        return NumerologyResponse.from_dict(result)

    def batch_process(
        self,
        queries: list[Dict[str, Any]]
    ) -> list[QuestionResponse]:
        """
        Process multiple queries in batch for efficiency.

        Args:
            queries: List of query dictionaries with 'question' and 'birth_details'

        Returns:
            List of QuestionResponse objects
        """
        results = []
        for query in queries:
            response = self.ask_question(
                question=query["question"],
                birth_details=query["birth_details"],
                language=query.get("language")
            )
            results.append(response)

        return results

    def __repr__(self) -> str:
        return f"VedikaClient(api_key={'***' + self.api_key[-4:] if self.api_key else 'None'})"
