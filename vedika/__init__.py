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
    # Additional calculation models
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
    normalize_western_relationship,
)
from .exceptions import (
    VedikaAPIError,
    AuthenticationError,
    RateLimitError,
    DailyLimitError,
    InsufficientCreditsError,
    SubscriptionExpiredError,
    ValidationError
)

from ._version import __version__
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
    # Additional calculation models
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
    "normalize_western_relationship",
    # Exceptions
    "VedikaAPIError",
    "AuthenticationError",
    "RateLimitError",
    "DailyLimitError",
    "InsufficientCreditsError",
    "SubscriptionExpiredError",
    "ValidationError",
]

from .client import (
    VastuWorkflowData, VastuRemediationTaskData,
    VastuRemediationTasksUpsertRequest, VastuRemediationTasksUpsertResponse,
    VastuRemediationTasksListRequest, VastuRemediationTasksListResponse,
    VastuRemediationTasksDeleteRequest, VastuRemediationTasksDeleteResponse,
    VastuRemediationReassessRequest, VastuRemediationReassessResponse,
    VastuMerchantCatalogUploadRequest, VastuMerchantCatalogUploadResponse,
    VastuMerchantCatalogGetRequest, VastuMerchantCatalogGetResponse,
    VastuMerchantCatalogDeleteRequest, VastuMerchantCatalogDeleteResponse,
    VastuMerchantRemediesRequest, VastuMerchantRemediesResponse,
)
from .client import VastuDrawingSheetRequest, VastuDrawingSheetResponse, VastuDrawingSheetData, VastuWorkspaceRequest, VastuWorkspaceResponse, VastuWorkspaceData
