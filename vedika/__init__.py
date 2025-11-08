"""
Vedika Python SDK
The only B2B astrology API with AI-powered chatbot queries.
"""

from .client import VedikaClient
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

__version__ = "1.0.0"
__author__ = "Vedika Intelligence"
__email__ = "support@vedika.io"
__url__ = "https://vedika.io"

__all__ = [
    "VedikaClient",
    "BirthDetails",
    "QuestionResponse",
    "BirthChart",
    "DashaResponse",
    "CompatibilityResponse",
    "YogaResponse",
    "DoshaResponse",
    "MuhurthaResponse",
    "NumerologyResponse",
    "VedikaAPIError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientCreditsError",
    "ValidationError",
]
