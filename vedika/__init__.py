"""
Vedika Python SDK
The only B2B astrology API with AI-powered chatbot queries.
"""

from .client import VedikaClient
from .models import (
    BirthDetails,
    QuestionResponse,
    Citation,
    BirthChart,
    DashaResponse,
    CompatibilityResponse,
    YogaResponse,
    DoshaResponse,
    MuhurthaResponse,
    NumerologyResponse,
    StructuredResponse,
    StructuredResponseSection,
    VoiceResponse,
    VoiceBilling,
    # Project Dominion models
    TarotCard,
    TarotReading,
    SpreadInfo,
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

__version__ = "3.0.0"
__author__ = "Vedika Intelligence"
__email__ = "support@vedika.io"
__url__ = "https://vedika.io"

__all__ = [
    "VedikaClient",
    "BirthDetails",
    "QuestionResponse",
    "Citation",
    "BirthChart",
    "DashaResponse",
    "CompatibilityResponse",
    "YogaResponse",
    "DoshaResponse",
    "MuhurthaResponse",
    "NumerologyResponse",
    "StructuredResponse",
    "StructuredResponseSection",
    "VoiceResponse",
    "VoiceBilling",
    # Project Dominion models
    "TarotCard",
    "TarotReading",
    "SpreadInfo",
    "SpreadList",
    "ChineseZodiac",
    "BaZiChart",
    "KuaResult",
    "Hexagram",
    "Crystal",
    "BodyGraph",
    "HDType",
    "MatchResult",
    "DoshaMatchResult",
    "MantraResult",
    "DeityResult",
    "PastLifeResult",
    "DailyBundle",
    "AllDashaResult",
    "HealthResult",
    "CareerResult",
    # Exceptions
    "VedikaAPIError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientCreditsError",
    "SubscriptionExpiredError",
    "ValidationError",
]
