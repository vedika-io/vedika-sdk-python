"""
Vedika Python SDK
Astrology APIs with structured calculations and conversational readings.
"""

from .client import VedikaClient
from .vastu_room_capture import upload_room_capture, merge_room_captures
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
    ValidationError,
    ServerError,
    ProUltraUnavailableError,
    OutputBudgetExhaustedError,
    QuestionErrorCode,
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
    # Room scan
    "upload_room_capture",
    "merge_room_captures",
    # Exceptions
    "VedikaAPIError",
    "AuthenticationError",
    "RateLimitError",
    "DailyLimitError",
    "InsufficientCreditsError",
    "SubscriptionExpiredError",
    "ValidationError",
    "ServerError",
    "ProUltraUnavailableError",
    "OutputBudgetExhaustedError",
    "QuestionErrorCode",
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
