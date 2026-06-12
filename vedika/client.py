"""
Vedika API Client
Main client class for interacting with the Vedika Astrology API.
"""

import os
from typing import Dict, Any, Optional, Iterator  # noqa: F401
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
    NumerologyResponse,
    VoiceResponse,
    TarotCard,
    TarotReading,
    SpreadList,
    ChineseZodiac,
    BaZiChart,
    KuaResult,
    Hexagram,
    Crystal,
    BodyGraph,
    HDType,
    MatchResult,
    DoshaMatchResult,
    MantraResult,
    DeityResult,
    PastLifeResult,
    DailyBundle,
    AllDashaResult,
    HealthResult,
    CareerResult,
)
from .exceptions import (
    VedikaAPIError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    SubscriptionExpiredError,
    ValidationError
)


def _offset_from_datetime(dt):
    """Extract UTC offset ('+05:30' / 'Z') from an ISO datetime, else None."""
    import re
    m = re.search(r'([+-]\d{2}:?\d{2}|Z)$', dt or '')
    return m.group(1) if m else None

def _v2_payload(result):
    """Unwrap a V2 envelope response ({success, data, billing, meta}) to its
    payload. V2 endpoints (Jun 2026 route migration) wrap the body; the legacy
    typed models predate that. Callers attach the full payload to the returned
    model as `.raw` so no field is ever lost to a model-shape mismatch."""
    return result.get("data", result) if isinstance(result, dict) else result


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

        # SDK-5 (Apr 21, 2026): X-API-Key is DEPRECATED at server level
        # (sunset 2026-10-20). Send Authorization: Bearer as primary auth.
        # Keep X-API-Key for backwards-compat with pre-v2.3 server middleware.
        # User-Agent synced to actual package version.
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,  # DEPRECATED — remove after 2026-10-20
            "User-Agent": "vedika-python-sdk/3.0.0"
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
                # SDK-2 (v2.3.1, Apr 21, 2026): Branch on server code to
                # distinguish subscription-expired from wallet-underrun.
                # Server emits SUBSCRIPTION_EXPIRED when billing period ended.
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                msg = body.get("message") or body.get("error") or "Payment required"
                if body.get("code") == "SUBSCRIPTION_EXPIRED":
                    raise SubscriptionExpiredError(msg)
                raise InsufficientCreditsError(msg)
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
        language: Optional[str] = None,
        *,
        system: Optional[str] = None,
        speed: Optional[str] = None,
        conversation_id: Optional[str] = None,
        partner_birth_details: Optional[Dict[str, Any]] = None,
        include_remedies: Optional[bool] = None,
        category: Optional[str] = None,
        response_format: Optional[str] = None
    ) -> QuestionResponse:
        """
        Ask a conversational astrology question (UNIQUE to Vedika!).

        This is the only B2B astrology API that supports natural language queries.

        Args:
            question: Your astrology question in natural language
            birth_details: Birth information (datetime, latitude, longitude, timezone)
            language: Response language (default: client's default language)
            system: Astrology system — "vedic", "western", or "kp"
            speed: Response speed — "fast" or "quality"
            conversation_id: Continue a previous conversation
            partner_birth_details: Partner's birth details for compatibility queries
            include_remedies: Include BPHS remedies in the response
            category: Query category hint (career, marriage, health, etc.)
            response_format: Response format — "text" or "json"

        Returns:
            QuestionResponse with answer, confidence, and metadata

        Example:
            >>> response = client.ask_question(
            ...     question="What are my career prospects this year?",
            ...     birth_details={
            ...         "datetime": "1990-06-15T14:30:00+05:30",
            ...         "latitude": 28.6139,
            ...         "longitude": 77.2090,
            ...         "timezone": "+05:30"
            ...     },
            ...     language="en",
            ...     system="vedic",
            ...     include_remedies=True
            ... )
            >>> print(response.answer)
        """
        data = {
            "question": question,
            "birthDetails": birth_details,
            "language": language or self.language
        }

        if system is not None:
            data["system"] = system
        if speed is not None:
            data["speed"] = speed
        if conversation_id is not None:
            data["conversationId"] = conversation_id
        if partner_birth_details is not None:
            data["partnerBirthDetails"] = partner_birth_details
        if include_remedies is not None:
            data["includeRemedies"] = include_remedies
        if category is not None:
            data["category"] = category
        if response_format is not None:
            data["responseFormat"] = response_format

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

        result = self._request("POST", "/api/v1/chart", data=data)
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
        result = _v2_payload(self._request("POST", "/v2/astrology/dasha-periods", data=birth_details))
        # Bridge the v2 snake_case period keys to the legacy model shape.
        # v2 nests antar_dasha[] inside each maha period; the legacy model
        # exposes flat mahadashas + the antar/pratyantar of the CURRENT maha
        # (full nesting always available via .raw).
        periods = result.get("maha_dasha") or []
        def _map(d):
            return {
                "planet": d.get("planet", ""),
                "startDate": d.get("start_date", ""),
                "endDate": d.get("end_date", ""),
                "durationYears": d.get("duration_years", 0.0),
            }
        cur = result.get("current_dasha") if isinstance(result.get("current_dasha"), dict) else {}
        cur_maha = cur.get("maha_dasha") or {}
        cur_full = next((p for p in periods if p.get("planet") == cur_maha.get("planet")), {})
        antars = cur_full.get("antar_dasha") or []
        cur_antar = cur.get("antar_dasha") or {}
        cur_antar_full = next((a for a in antars if a.get("planet") == cur_antar.get("planet")), {})
        pratyantars = cur_antar_full.get("pratyantar_dasha") or cur_antar_full.get("pratyantar") or []
        bridged = {
            **result,
            "mahadashas": [_map(d) for d in periods],
            "antardashas": [_map(a) for a in antars],
            "pratyantardashas": [_map(p) for p in pratyantars],
            "currentDasha": cur_maha.get("planet")
                if isinstance(result.get("current_dasha"), dict) else result.get("current_dasha"),
        }
        obj = DashaResponse.from_dict(bridged)
        obj.raw = result
        return obj

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

        result = self._request("POST", "/api/v1/compatibility", data=data)
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
        result = _v2_payload(self._request("POST", "/v2/astrology/jaimini/rajayogas", data=birth_details))
        obj = YogaResponse.from_dict(result)
        obj.raw = result
        return obj

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
        result = _v2_payload(self._request("POST", "/v2/astrology/all-doshas", data=birth_details))
        obj = DoshaResponse.from_dict(result)
        obj.raw = result
        return obj

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
            "latitude": location.get("latitude") if isinstance(location, dict) else None,
            "longitude": location.get("longitude") if isinstance(location, dict) else None,
            "eventType": event_type
        }

        result = _v2_payload(self._request("POST", "/v2/astrology/muhurta", data=data))
        obj = MuhurthaResponse.from_dict(result)
        obj.raw = result
        return obj

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

        result = _v2_payload(self._request("POST", "/v2/astrology/numerology/complete", data=data))
        obj = NumerologyResponse.from_dict(result)
        obj.raw = result
        return obj

    # ═══════════════════════════════════════════
    # V2 Vedic Computation Endpoints
    # ═══════════════════════════════════════════

    def get_birth_chart_v2(self, type: str, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get birth chart via V2 endpoint (faster, cheaper).

        Args:
            type: kundli, birth-chart, planet-positions, house-cusps, or ascendant
            birth_details: dict with datetime, latitude, longitude, timezone
        """
        return self._request("POST", f"/v2/astrology/{type}", data=birth_details)

    def get_dasha_v2(self, system: str, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Dasha periods via V2 endpoint.

        Args:
            system: vimshottari-dasha, mahadasha, antardasha, pratyantardasha, or yogini-dasha
            birth_details: dict with datetime, latitude, longitude, timezone
        """
        return self._request("POST", f"/v2/astrology/{system}", data=birth_details)

    def get_doshas_v2(self, type: str, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Dosha analysis via V2 endpoint.

        Args:
            type: mangal-dosha, kaal-sarp-dosha, sade-sati, pitru-dosha, or all-doshas
            birth_details: dict with datetime, latitude, longitude, timezone
        """
        return self._request("POST", f"/v2/astrology/{type}", data=birth_details)

    def get_compatibility_v2(
        self, type: str, male: Dict[str, Any], female: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get compatibility matching via V2 endpoint.

        Args:
            type: guna-milan, kundali-matching, ashtakoot-match, or nakshatra-porutham
            male: dict with datetime, latitude, longitude, timezone
            female: dict with datetime, latitude, longitude, timezone
        """
        return self._request("POST", f"/v2/astrology/{type}", data={"male": male, "female": female})

    def get_panchang(
        self,
        date: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Panchang (Hindu calendar) data.

        Args:
            date: YYYY-MM-DD format (defaults to today)
            latitude: Location latitude (defaults to Delhi)
            longitude: Location longitude (defaults to Delhi)
            timezone: UTC offset (e.g., "+05:30"). NOT IANA names
        """
        params = {}
        if date: params["date"] = date
        if latitude is not None: params["latitude"] = latitude
        if longitude is not None: params["longitude"] = longitude
        if timezone: params["timezone"] = timezone
        return self._request("GET", "/v2/astrology/panchang", params=params)

    def get_muhurta_v2(
        self,
        type: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Muhurta (auspicious timing) via V2 endpoint.

        Args:
            type: choghadiya, hora, rahu-kaal, abhijit-muhurta, brahma-muhurta, etc.
            latitude: Location latitude
            longitude: Location longitude
            timezone: IANA timezone
        """
        params = {}
        if latitude is not None: params["latitude"] = latitude
        if longitude is not None: params["longitude"] = longitude
        if timezone: params["timezone"] = timezone
        return self._request("GET", f"/v2/astrology/{type}", params=params)

    def get_divisional_chart(self, chart: str, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get divisional chart (D2-D60).

        Args:
            chart: navamsa, dashamsa, saptamsa, dwadashamsa, etc.
            birth_details: dict with datetime, latitude, longitude, timezone
        """
        # D2 'hora' is /v2/astrology/hora-chart; /hora is muhurta planetary-hours.
        _path = "hora-chart" if chart in ("hora", "D2") else chart
        return self._request("POST", f"/v2/astrology/{_path}", data=birth_details)

    def get_prediction(
        self,
        period: str,
        rashi: Optional[str] = None,
        birth_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get predictions (daily/weekly/monthly/quarterly/yearly).

        Args:
            period: daily, weekly, monthly, quarterly, or yearly
            rashi: Zodiac sign (e.g., aries, taurus)
            birth_details: Alternative to rashi — derives moon sign automatically
        """
        data = {}
        if rashi: data["rashi"] = rashi
        if birth_details: data["birthDetails"] = birth_details
        return self._request("POST", f"/v2/astrology/prediction/{period}", data=data)

    def get_ashtakavarga(self, type: str, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Ashtakavarga analysis.

        Args:
            type: ashtakavarga or sarvashtakavarga
            birth_details: dict with datetime, latitude, longitude, timezone
        """
        return self._request("POST", f"/v2/astrology/{type}", data=birth_details)

    def get_varshaphal(self, birth_details: Dict[str, Any], year: Optional[int] = None) -> Dict[str, Any]:
        """Get Varshaphal (annual horoscope / solar return).

        Args:
            birth_details: dict with datetime, latitude, longitude, timezone
            year: Year for the annual chart (defaults to current year)
        """
        data = {**birth_details}
        if year: data["year"] = year
        return self._request("POST", "/v2/astrology/varshaphal", data=data)

    def get_strength(self, type: str, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get planetary strength analysis.

        Args:
            type: shadbala, chandra-bala, or tara-bala
            birth_details: dict with datetime, latitude, longitude, timezone
        """
        return self._request("POST", f"/v2/astrology/{type}", data=birth_details)

    def get_numerology_v2(
        self,
        type: str,
        name: Optional[str] = None,
        birth_date: Optional[str] = None,
        system: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get numerology via V2 endpoint.

        Args:
            type: complete, life-path, destiny, personality, soul-urge, personal-year, or compatibility
            name: Full name (required for destiny/personality/soul-urge/complete)
            birth_date: YYYY-MM-DD (required for life-path/personal-year/complete)
            system: pythagorean or chaldean (default pythagorean)
            year: For personal-year calculation
        """
        data = {}
        if name: data["name"] = name
        if birth_date: data["birthDate"] = birth_date
        if system: data["system"] = system
        if year: data["year"] = year
        return self._request("POST", f"/v2/astrology/numerology/{type}", data=data)

    # ═══════════════════════════════════════════
    # Horoscope
    # ═══════════════════════════════════════════

    def get_horoscope(
        self,
        sign: str,
        period: str = "daily",
        system: str = "vedic"
    ) -> Dict[str, Any]:
        """Get horoscope for a zodiac sign.

        Args:
            sign: aries, taurus, gemini, etc.
            period: daily, weekly, or monthly
            system: vedic or western
        """
        base = "/v2/western" if system == "western" else "/v2/astrology"
        # Western only exposes base /horoscope/{sign}; Vedic supports /{period}.
        path = f"{base}/horoscope/{sign}" if (period == "daily" or system == "western") else f"{base}/horoscope/{sign}/{period}"
        return self._request("GET", path)

    # ═══════════════════════════════════════════
    # Western Astrology
    # ═══════════════════════════════════════════

    def get_western_transits(
        self,
        birth_details: Dict[str, Any],
        transit_date_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Western transit chart and aspects.

        Args:
            birth_details: dict with datetime, latitude, longitude, timezone
            transit_date_time: ISO 8601 datetime for transits (defaults to now)
        """
        data = {**birth_details}
        if transit_date_time: data["transitDateTime"] = transit_date_time
        return self._request("POST", "/v2/western/transit-chart", data=data)

    def get_western_progressions(
        self,
        birth_details: Dict[str, Any],
        progression_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Western secondary progressions.

        Args:
            birth_details: dict with datetime, latitude, longitude, timezone
            progression_date: ISO 8601 date for progressions (defaults to now)
        """
        data = {**birth_details}
        if progression_date: data["progressionDate"] = progression_date
        return self._request("POST", "/v2/western/progressions", data=data)

    def get_western_solar_return(
        self,
        birth_details: Dict[str, Any],
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get Western solar return chart.

        Args:
            birth_details: dict with datetime, latitude, longitude, timezone
            year: Year for solar return (defaults to current year)
        """
        data = {**birth_details}
        if year: data["year"] = year
        return self._request("POST", "/v2/western/solar-return", data=data)

    def get_western_relationship(
        self,
        type: str,
        person1: Dict[str, Any],
        person2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get Western relationship analysis.

        Args:
            type: synastry, synastry-aspects, composite, or composite-aspects
            person1: dict with datetime, latitude, longitude, timezone
            person2: dict with datetime, latitude, longitude, timezone
        """
        return self._request("POST", f"/v2/western/{type}", data={"person1": person1, "person2": person2})

    # ═══════════════════════════════════════════
    # Convenience Methods (Common Use Cases)
    # ═══════════════════════════════════════════

    def get_panchang_today(self) -> Dict[str, Any]:
        """Get today's panchang (no parameters needed)."""
        return self._request("GET", "/v2/astrology/panchang/today")

    def get_sade_sati(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Sade Sati status for a birth chart."""
        return self.get_doshas_v2("sade-sati", birth_details)

    def get_chandrashtama(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Chandrashtama (Moon transit) periods."""
        return self._request("POST", "/v2/astrology/chandrashtama", data=birth_details)

    def get_kundli(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Kundli (complete birth chart with all details)."""
        return self.get_birth_chart_v2("kundli", birth_details)

    def get_navamsa(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Navamsa (D9) chart."""
        return self.get_divisional_chart("navamsa", birth_details)

    def get_guna_milan(self, male: Dict[str, Any], female: Dict[str, Any]) -> Dict[str, Any]:
        """Get Guna Milan (36-point matching)."""
        return self.get_compatibility_v2("guna-milan", male, female)

    def get_vimshottari_dasha(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Vimshottari Dasha timeline."""
        return self.get_dasha_v2("vimshottari-dasha", birth_details)

    def get_daily_prediction(self, rashi: str) -> Dict[str, Any]:
        """Get daily prediction for a zodiac sign."""
        return self.get_prediction("daily", rashi=rashi)

    def get_shadbala(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get Shadbala (6-fold planetary strength)."""
        return self.get_strength("shadbala", birth_details)

    # ═══════════════════════════════════════════
    # Utility
    # ═══════════════════════════════════════════

    def get_conversations(self) -> Dict[str, Any]:
        """List all conversations."""
        return self._request("GET", "/api/v1/conversations")

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation.

        Args:
            conversation_id: The conversation ID to delete
        """
        self._request("DELETE", f"/api/v1/conversations/{conversation_id}")

    def get_usage(self) -> Dict[str, Any]:
        """Get wallet usage and balance."""
        return self._request("GET", "/api/v1/usage/wallet")

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

    # ═══════════════════════════════════════════
    # Voice (audio-in → audio-out)
    # SDK-3 (v2.3.1, Apr 21, 2026): typed voice envelope
    # ═══════════════════════════════════════════

    def ask_voice(
        self,
        audio: Any,
        tier: str = "vedika-standard",
        birth_details: Optional[Dict[str, Any]] = None,
        partner_birth_details: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        include_daily_context: Optional[bool] = None,
        allow_general: Optional[bool] = None,
        conversation_id: Optional[str] = None,
        audio_mime: str = "audio/wav",
    ) -> VoiceResponse:
        """
        Send a voice query (multipart audio upload).

        Branches on response Content-Type:
        - ``audio/mpeg``: binary TTS audio, metadata parsed from
          ``X-Vedika-Voice-Meta`` base64 header. Returns a VoiceResponse
          with ``audio=<bytes>`` and ``is_fallback=False``.
        - ``application/json``: TTS failed, text-only fallback. Returns a
          VoiceResponse with ``audio=None``, ``is_fallback=True``, and
          ``response_text=<narrated answer>``.

        Args:
            audio: File-like object, raw bytes, or file path string
            tier: vedika-standard | vedika-jarvis | vedika-native
            birth_details: Required for chart-bound questions unless
                allow_general=True
            partner_birth_details: For synastry / compatibility voice
            language: ISO 639-1 hint (auto-detected when omitted)
            include_daily_context: Inject today's panchang
            allow_general: Bypass chart-bound gate for theory Qs
            conversation_id: Continue an existing voice conversation
            audio_mime: MIME type of the audio blob (default audio/wav)

        Returns:
            VoiceResponse
        """
        import base64
        import json as _json

        # Normalize audio input to (name, fileobj-or-bytes, mime) tuple.
        if hasattr(audio, "read"):
            audio_tuple = ("audio", audio, audio_mime)
        elif isinstance(audio, (bytes, bytearray)):
            audio_tuple = ("audio", bytes(audio), audio_mime)
        elif isinstance(audio, str):
            # File path
            audio_tuple = ("audio", open(audio, "rb"), audio_mime)
        else:
            raise ValueError(
                "audio must be a file-like object, bytes, or a file path string"
            )

        files = {"audio": audio_tuple}
        data: Dict[str, Any] = {"tier": tier}
        if birth_details is not None:
            data["birthDetails"] = _json.dumps(birth_details)
        if partner_birth_details is not None:
            data["partnerBirthDetails"] = _json.dumps(partner_birth_details)
        if language is not None:
            data["language"] = language
        if include_daily_context is not None:
            data["includeDailyContext"] = str(bool(include_daily_context)).lower()
        if allow_general is not None:
            data["allow_general"] = str(bool(allow_general)).lower()
        if conversation_id is not None:
            data["conversationId"] = conversation_id

        # Drop the JSON Content-Type so requests picks multipart boundary.
        headers = {
            k: v for k, v in self.session.headers.items() if k.lower() != "content-type"
        }

        url = f"{self.base_url}/api/v1/voice"
        response = requests.post(
            url,
            files=files,
            data=data,
            headers=headers,
            timeout=self.timeout,
        )

        # Shared error handling (matches _request branches).
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 402:
            try:
                body = response.json()
            except ValueError:
                body = {}
            msg = body.get("message") or body.get("error") or "Payment required"
            if body.get("code") == "SUBSCRIPTION_EXPIRED":
                raise SubscriptionExpiredError(msg)
            raise InsufficientCreditsError(msg)
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded.")
        elif response.status_code == 422:
            body = response.json() if response.content else {}
            raise ValidationError(f"Voice validation error: {body.get('code') or body.get('error')}")
        elif response.status_code >= 400:
            try:
                body = response.json()
                raise VedikaAPIError(
                    f"HTTP {response.status_code}: {body.get('error') or body.get('message')}"
                )
            except ValueError:
                raise VedikaAPIError(f"HTTP {response.status_code}: voice request failed")

        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            # TTS fallback path
            return VoiceResponse.from_json(response.json())

        # Binary audio/mpeg path
        meta_header = response.headers.get("X-Vedika-Voice-Meta")
        meta: Dict[str, Any] = {}
        if meta_header:
            try:
                meta = _json.loads(base64.b64decode(meta_header).decode("utf-8"))
            except Exception:
                meta = {}
        return VoiceResponse.from_binary(response.content, meta)

    def get_voice_pricing(self) -> Dict[str, Any]:
        """
        Get voice pricing tiers, rate limits, and language support.

        Gated to Business + Enterprise plans. Returns 403 VOICE_PLAN_REQUIRED
        for lower tiers.
        """
        return self._request("GET", "/api/v1/voice/pricing")

    # ═══════════════════════════════════════════
    # Project Dominion — New Domain Sub-Clients
    # ═══════════════════════════════════════════

    @property
    def tarot(self) -> '_TarotDomain':
        """Tarot domain methods."""
        return self._TarotDomain(self)

    @property
    def chinese(self) -> '_ChineseDomain':
        """Chinese astrology domain methods."""
        return self._ChineseDomain(self)

    @property
    def iching(self) -> '_IChingDomain':
        """I Ching domain methods."""
        return self._IChingDomain(self)

    @property
    def crystals(self) -> '_CrystalsDomain':
        """Crystal recommendations domain."""
        return self._CrystalsDomain(self)

    @property
    def human_design(self) -> '_HumanDesignDomain':
        """Human Design domain methods."""
        return self._HumanDesignDomain(self)

    @property
    def matrimony(self) -> '_MatrimonyDomain':
        """Matrimony / advanced matching domain."""
        return self._MatrimonyDomain(self)

    @property
    def spiritual(self) -> '_SpiritualDomain':
        """Spiritual guidance domain."""
        return self._SpiritualDomain(self)

    @property
    def daily(self) -> '_DailyDomain':
        """Daily insights domain."""
        return self._DailyDomain(self)

    @property
    def dasha(self) -> '_DashaDomain':
        """Extended dasha systems domain."""
        return self._DashaDomain(self)

    @property
    def health(self) -> '_HealthDomain':
        """Health astrology domain."""
        return self._HealthDomain(self)

    @property
    def career(self) -> '_CareerDomain':
        """Career astrology domain."""
        return self._CareerDomain(self)

    # ── Domain inner classes ──

    class _TarotDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def card_of_the_day(self) -> TarotCard:
            """Get a single card of the day."""
            _r = _v2_payload(self._c._request("GET", "/v2/tarot/card-of-the-day"))
            _o = TarotCard.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

        def draw(self, spread: str, question: Optional[str] = None) -> TarotReading:
            """Draw a tarot spread.

            Args:
                spread: Spread type (e.g. "celtic-cross", "three-card", "single")
                question: Optional question for the reading
            """
            data: Dict[str, Any] = {}
            if question:
                data["question"] = question
            _r = _v2_payload(self._c._request("POST", f"/v2/tarot/draw/{spread}", data=data))
            _obj = TarotReading.from_dict(_r)
            _obj.raw = _r
            return _obj

        def spreads(self) -> SpreadList:
            """List available tarot spreads."""
            _r = _v2_payload(self._c._request("GET", "/v2/tarot/spreads"))
            _o = SpreadList.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

    class _ChineseDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def zodiac_animal(self, year: int) -> ChineseZodiac:
            """Get Chinese zodiac animal for a year.

            Args:
                year: Year to look up (e.g. 1995)
            """
            _r = _v2_payload(self._c._request("POST", "/v2/chinese/zodiac-animal", data={"year": year}))
            _o = ChineseZodiac.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

        def bazi(self, birth_details: Dict[str, Any]) -> BaZiChart:
            """Get BaZi (Four Pillars of Destiny) chart.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/chinese/bazi/chart", data=birth_details))
            _obj = BaZiChart.from_dict(_r)
            _obj.raw = _r
            return _obj

        @property
        def feng_shui(self) -> 'VedikaClient._FengShuiDomain':
            return VedikaClient._FengShuiDomain(self._c)

    class _FengShuiDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def kua_number(self, birth_year: int, gender: str) -> KuaResult:
            """Calculate personal Kua number.

            Args:
                birth_year: Year of birth
                gender: "male" or "female"
            """
            _r = _v2_payload(self._c._request("POST", "/v2/chinese/feng-shui/kua-number",
                                              data={"birthYear": birth_year, "gender": gender}))
            _obj = KuaResult.from_dict(_r)
            _obj.raw = _r
            return _obj

    class _IChingDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def cast(self, question: Optional[str] = None) -> Hexagram:
            """Cast an I Ching hexagram.

            Args:
                question: Optional question to ask the oracle
            """
            data: Dict[str, Any] = {}
            if question:
                data["question"] = question
            _r = _v2_payload(self._c._request("POST", "/v2/iching/cast", data=data))
            _o = Hexagram.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

        def daily(self) -> Hexagram:
            """Get daily I Ching hexagram."""
            _r = _v2_payload(self._c._request("GET", "/v2/iching/daily"))
            _o = Hexagram.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

    class _CrystalsDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def by_zodiac(self, sign: str) -> list:
            """Get crystals recommended for a zodiac sign.

            Args:
                sign: Zodiac sign (e.g. "aries", "taurus")
            """
            result = self._c._request("GET", f"/v2/crystals/by-zodiac/{sign}")
            if isinstance(result, list):
                return [Crystal.from_dict(c) for c in result]
            return [Crystal.from_dict(c) for c in result.get("crystals", result.get("data", []))]

        def catalog(self) -> list:
            """Get full crystal catalog."""
            result = self._c._request("GET", "/v2/crystals/catalog")
            if isinstance(result, list):
                return [Crystal.from_dict(c) for c in result]
            return [Crystal.from_dict(c) for c in result.get("crystals", result.get("data", []))]

    class _HumanDesignDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def chart(self, birth_details: Dict[str, Any]) -> BodyGraph:
            """Get full Human Design body graph chart.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/human-design/chart", data=birth_details))
            _o = BodyGraph.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

        def type(self, birth_details: Dict[str, Any]) -> HDType:
            """Get Human Design type summary.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/human-design/type", data=birth_details))
            _o = HDType.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

    class _MatrimonyDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def unified_match(self, person1: Dict[str, Any], person2: Dict[str, Any]) -> MatchResult:
            """Unified match analysis (Vedic + KP combined).

            Args:
                person1: dict with datetime, latitude, longitude, timezone
                person2: dict with datetime, latitude, longitude, timezone
            """
            return MatchResult.from_dict(
                self._c._request("POST", "/v2/matrimony/unified-match",
                                 data={"person1": person1, "person2": person2})
            )

        def dosha_cancellation(self, person1: Dict[str, Any], person2: Dict[str, Any]) -> DoshaMatchResult:
            """Check dosha cancellation between two charts.

            Args:
                person1: dict with datetime, latitude, longitude, timezone
                person2: dict with datetime, latitude, longitude, timezone
            """
            return DoshaMatchResult.from_dict(
                self._c._request("POST", "/v2/matrimony/dosha-cancellation",
                                 data={"person1": person1, "person2": person2})
            )

    class _SpiritualDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def mantra(self, birth_details: Dict[str, Any]) -> MantraResult:
            """Get personalized mantra recommendation.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/spiritual/mantra", data=birth_details))
            _o = MantraResult.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

        def deity(self, birth_details: Dict[str, Any]) -> DeityResult:
            """Get recommended deity for worship.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/spiritual/deity", data=birth_details))
            _o = DeityResult.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

        def past_life(self, birth_details: Dict[str, Any]) -> PastLifeResult:
            """Get past life karmic indicators.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/spiritual/past-life", data=birth_details))
            _o = PastLifeResult.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

    class _DailyDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def bundle(self) -> DailyBundle:
            """Get comprehensive daily bundle (horoscope + panchang + tarot + mantra)."""
            _r = _v2_payload(self._c._request("GET", "/v2/daily/bundle"))
            _o = DailyBundle.from_dict(_r)
            try: _o.raw = _r
            except Exception: pass
            return _o

        def horoscope(self, sign: str) -> Dict[str, Any]:
            """Get daily horoscope for a zodiac sign.

            Args:
                sign: Zodiac sign (e.g. "aries", "taurus")
            """
            return self._c._request("GET", f"/v2/astrology/horoscope/{sign}")

    class _DashaDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def ashtottari(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
            """Get Ashtottari Dasha periods (108-year cycle).

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            return self._c._request("POST", "/v2/astrology/ashtottari-dasha", data=birth_details)

        def chara(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
            """Get Chara (Jaimini) Dasha periods.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            return self._c._request("POST", "/v2/astrology/chara-dasha", data=birth_details)

        def current_all(self, birth_details: Dict[str, Any]) -> AllDashaResult:
            """Get current periods from ALL dasha systems at once.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            return AllDashaResult.from_dict(
                self._c._request("POST", "/v2/astrology/dasha/current-all", data=birth_details)
            )

    class _HealthDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def analysis(self, birth_details: Dict[str, Any]) -> HealthResult:
            """Get health analysis from birth chart.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/health/vulnerabilities", data={
                "dateOfBirth": str(birth_details.get("datetime", ""))[:10],
                "timeOfBirth": str(birth_details.get("datetime", ""))[11:16],
                "latitude": birth_details.get("latitude"),
                "longitude": birth_details.get("longitude"),
                "timezone": birth_details.get("timezone") or _offset_from_datetime(str(birth_details.get("datetime", ""))),
            }))
            _obj = HealthResult.from_dict(_r)
            _obj.raw = _r
            return _obj

    class _CareerDomain:
        def __init__(self, client: 'VedikaClient'):
            self._c = client

        def analysis(self, birth_details: Dict[str, Any]) -> CareerResult:
            """Get career analysis from birth chart.

            Args:
                birth_details: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/career/suitable", data={
                "dateOfBirth": str(birth_details.get("datetime", ""))[:10],
                "timeOfBirth": str(birth_details.get("datetime", ""))[11:16],
                "latitude": birth_details.get("latitude"),
                "longitude": birth_details.get("longitude"),
                "timezone": birth_details.get("timezone") or _offset_from_datetime(str(birth_details.get("datetime", ""))),
            }))
            _obj = CareerResult.from_dict(_r)
            _obj.raw = _r
            return _obj

    def __repr__(self) -> str:
        return f"VedikaClient(api_key={'***' + self.api_key[-4:] if self.api_key else 'None'})"
