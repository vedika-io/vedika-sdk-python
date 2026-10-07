"""
Vedika API Client
Main client class for interacting with the Vedika Astrology API.
"""

from __future__ import annotations

import os
import re
import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional, Iterator, List, Mapping, TypedDict, Literal, Union, overload, cast  # noqa: F401
import requests
from requests.adapters import HTTPAdapter

from .models import (
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
from ._idempotency import certified_header
from ._version import __version__


class VastuOperation(str, Enum):
    REMEDIATION_TASKS_UPSERT = "remediation/tasks/upsert"
    REMEDIATION_TASKS_LIST = "remediation/tasks/list"
    REMEDIATION_TASKS_DELETE = "remediation/tasks/delete"
    REMEDIATION_REASSESS = "remediation/reassess"
    MERCHANT_CATALOG_UPLOAD = "merchant/catalog/upload"
    MERCHANT_CATALOG_GET = "merchant/catalog/get"
    MERCHANT_CATALOG_DELETE = "merchant/catalog/delete"
    MERCHANT_REMEDIES = "merchant/remedies"

    PLAN_COMPARE_VERSIONS = "plan/compare-versions"
    RECEIPT_VERIFY = "receipt/verify"
    RULES_VERSIONS = "rules/versions"
    PORTFOLIO_SEARCH = "portfolio/search"
    PORTFOLIO_COMPARE = "portfolio/compare"
    PORTFOLIO_ANALYTICS = "portfolio/analytics"
    PORTFOLIO_USAGE = "portfolio/usage"
    PORTFOLIO_USAGE_EXPORT = "portfolio/usage/export"
    PORTFOLIO_BUDGETS_SET = "portfolio/budgets/set"
    PORTFOLIO_BUDGETS_GET = "portfolio/budgets/get"
    DRAWING_SHEET = "report/drawing-sheet"
    PROPERTIES_CREATE = "properties/create"
    PROPERTIES_UPDATE = "properties/update"
    PROPERTIES_COLLABORATION_GET = "properties/collaboration/get"
    PROPERTIES_COLLABORATION_INVITE = "properties/collaboration/invite"
    PROPERTIES_COLLABORATION_REVOKE = "properties/collaboration/revoke"
    PROPERTIES_COLLABORATION_MEMBERS = "properties/collaboration/members"
    PROPERTIES_COLLABORATION_COMMENT = "properties/collaboration/comment"
    PROPERTIES_COLLABORATION_REVIEW = "properties/collaboration/review"
    PROPERTIES_COLLABORATION_UPDATE = "properties/collaboration/update"
    PROPERTIES_ACTIVITY_LIST = "properties/activity/list"
    PROPERTIES_ACTIVITY_EXPORT = "properties/activity/export"
    PROPERTIES_GET = "properties/get"
    PROPERTIES_LIST = "properties/list"
    PROPERTIES_DELETE = "properties/delete"
    PROPERTIES_LINK_SCAN = "properties/link-scan"
    ARCHIVE_TIER = "archive/tier"
    ARCHIVE_EXPORT = "archive/export"
    ARCHIVE_DELETE = "archive/delete"
    ARCHIVE_SUMMARY = "archive/summary"
    FEED_LISTINGS = "feed/listings"
    QUOTE_CALCULATE = "quote/calculate"

    """One member per mounted logical Vastu route; URL aliases are not duplicated."""
    SCANS_TIMELAPSE = "scans/timelapse"
    SCANS_DELETE = "scans/delete"
    SCANS_LIST = "scans/list"
    SCANS_RETRIEVE = "scans/retrieve"
    SCANS_SAVE = "scans/save"
    AR_DEITY_ICONS = "ar/deity-icons"
    AR_CAPTURE_MERGE = "ar/capture-merge"
    PLOT_FROM_SURVEY = "plot/from-survey"
    AR_ROOM_CAPTURE = "ar/room-capture"
    AR_ATTESTATION_CHALLENGE = "ar/attestation/challenge"
    AR_YANTRA_MESHES = "ar/yantra-meshes"
    AR_ZONE_TEXTURES = "ar/zone-textures"
    AR_ANCHOR_RECOMMENDATIONS = "ar/anchor-recommendations"
    AR_HEATMAP_RASTER = "ar/heatmap-raster"
    AR_SCAN_QUALITY = "ar/scan-quality"
    AR_TRUE_NORTH_CALIBRATE = "ar/true-north-calibrate"
    ASSESSMENTS = "assessments"
    ASSESSMENTS_BATCH = "assessments/batch"
    AUDIT_FLOOR_PLAN = "audit/floor-plan"
    AUDIT_FLOOR_PLAN_DETAILED = "audit/floor-plan-detailed"
    AUDIT_SINGLE_ROOM = "audit/single-room"
    COMPARE_BEFORE_AFTER_REMEDY = "compare/before-after-remedy"
    COMPOUND_WALL_ANALYSIS = "compound/wall-analysis"
    DIRECTION_AUSPICIOUS_FACING = "direction/auspicious-facing"
    DIRECTION_CORRECT = "direction/correct"
    DIRECTION_DECLINATION = "direction/declination"
    DIRECTION_SUN_PATH = "direction/sun-path"
    DIRECTION_ZONE_FROM_BEARING = "direction/zone-from-bearing"
    ELEMENTS_BALANCE_SUGGEST = "elements/balance-suggest"
    ELEMENTS_DISTRIBUTION = "elements/distribution"
    ENTRANCE_OBSTRUCTION_CHECK = "entrance/obstruction-check"
    ENTRANCE_PADA = "entrance/pada"
    ENTRANCE_RECOMMEND = "entrance/recommend"
    FLOOR_LEVEL_ANALYSIS = "floor/level-analysis"
    FUSION_CHART = "fusion/chart"
    MANDALA_PROJECT_81_PADA = "mandala/project/81-pada"
    MANDALA_PROJECT_9_ZONE = "mandala/project/9-zone"
    MANDALA_PROJECT_BRAHMASTHAN = "mandala/project/brahmasthan"
    MULTI_STOREY_FLOOR_RULES = "multi-storey/floor-rules"
    PLACEMENT_BALCONY = "placement/balcony"
    PLACEMENT_BOREWELL = "placement/borewell"
    PLACEMENT_GARDEN = "placement/garden"
    PLACEMENT_GENERATOR_ELECTRICAL = "placement/generator-electrical"
    PLACEMENT_MAIN_GATE = "placement/main-gate"
    PLACEMENT_OVERHEAD_TANK = "placement/overhead-tank"
    PLACEMENT_SEPTIC_TANK = "placement/septic-tank"
    PLACEMENT_TREE = "placement/tree"
    PLACEMENT_WELL = "placement/well"
    PLACEMENT_WINDOW = "placement/window"
    PLAN_ANALYZE = "plan/analyze"
    PLAN_FROM_REQUIREMENTS = "plan/from-requirements"
    PLAN_GENERATE = "plan/generate"
    PLAN_OPTIMIZE = "plan/optimize"
    PLAN_REPORT = "plan/report"
    PLAN_IMPORT_DXF = "plan/import-dxf"
    PLAN_EXPORT_DXF = "plan/export-dxf"
    PLAN_EXPORT_IFC = "plan/export-ifc"
    PLAN_CONVERT_UNITS = "plan/convert-units"
    PLAN_IMPORT_IFC = "plan/import-ifc"
    PLAN_IMPORT_IMAGE = "plan/import-image"
    PLAN_IMPORT_PDF = "plan/import-pdf"
    PLAN_UPLOAD = "plan/upload"
    PLOT_EXTENSIONS_CUTS = "plot/extensions-cuts"
    PLOT_ORIENTATION = "plot/orientation"
    PLOT_RATIO = "plot/ratio"
    PLOT_ROAD_ORIENTATION = "plot/road-orientation"
    PLOT_SHAPE = "plot/shape"
    PLOT_SLOPE = "plot/slope"
    REFERENCE_COLORS_BY_ZONE = "reference/colors-by-zone"
    REFERENCE_DEFECTS_CATALOG = "reference/defects/catalog"
    REFERENCE_DIRECTIONS_16 = "reference/directions/16"
    REFERENCE_DIRECTIONS_32 = "reference/directions/32"
    REFERENCE_DIRECTIONS_8 = "reference/directions/8"
    REFERENCE_GATE_OBSTRUCTIONS = "reference/gate-obstructions"
    REFERENCE_MANDALA_45_DEVATAS = "reference/mandala/45-devatas"
    REFERENCE_MANDALA_64_PADA = "reference/mandala/64-pada"
    REFERENCE_MANDALA_9_ZONE = "reference/mandala/9-zone"
    REFERENCE_MATERIALS_BY_ZONE = "reference/materials-by-zone"
    REFERENCE_REMEDIES_CATALOG = "reference/remedies/catalog"
    ROOM_BEDROOM = "room/bedroom"
    ROOM_DINING = "room/dining"
    ROOM_KITCHEN = "room/kitchen"
    ROOM_LIVING = "room/living"
    ROOM_POOJA = "room/pooja"
    ROOM_STAIRCASE = "room/staircase"
    ROOM_STORE_OPERATION = "room/store"
    ROOM_STUDY = "room/study"
    ROOM_TOILET = "room/toilet"
    ROOM_WATER_STORAGE = "room/water-storage"
    SCORE_COMPLIANCE_INDEX = "score/compliance-index"
    SCORE_OVERALL = "score/overall"
    SCORE_ZONE_WISE = "score/zone-wise"
    SPECIALIZED_COMMERCIAL = "specialized/commercial"
    SPECIALIZED_EDUCATIONAL = "specialized/educational"
    SPECIALIZED_FACTORY = "specialized/factory"
    SPECIALIZED_HOSPITAL = "specialized/hospital"
    SPECIALIZED_RESIDENTIAL = "specialized/residential"
    SPECIALIZED_RESTAURANT = "specialized/restaurant"
    SPECIALIZED_TEMPLE = "specialized/temple"
    TIMING_BHUMI_PUJAN = "timing/bhumi-pujan"
    TIMING_CONSTRUCTION_START = "timing/construction-start"
    TIMING_GRIHAPRAVESH = "timing/grihapravesh"
    TIMING_VASTU_SHANTI = "timing/vastu-shanti"
    JOBS = "jobs"
    JOBS_ID = "jobs/{id}"
    JOBS_ID_RESULTS = "jobs/{id}/results"
    JOBS_ID_CANCEL = "jobs/{id}/cancel"

_VASTU_OPERATION_CONTRACTS = {
    "remediation/tasks/upsert": {"method": "POST", "requestSchema": "VastuRemediationTasksUpsertRequest", "responseSchema": "VastuRemediationTasksUpsertResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "remediation/tasks/list": {"method": "POST", "requestSchema": "VastuRemediationTasksListRequest", "responseSchema": "VastuRemediationTasksListResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "remediation/tasks/delete": {"method": "POST", "requestSchema": "VastuRemediationTasksDeleteRequest", "responseSchema": "VastuRemediationTasksDeleteResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "remediation/reassess": {"method": "POST", "requestSchema": "VastuRemediationReassessRequest", "responseSchema": "VastuRemediationReassessResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "merchant/catalog/upload": {"method": "POST", "requestSchema": "VastuMerchantCatalogUploadRequest", "responseSchema": "VastuMerchantCatalogUploadResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "merchant/catalog/get": {"method": "POST", "requestSchema": "VastuMerchantCatalogGetRequest", "responseSchema": "VastuMerchantCatalogGetResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "merchant/catalog/delete": {"method": "POST", "requestSchema": "VastuMerchantCatalogDeleteRequest", "responseSchema": "VastuMerchantCatalogDeleteResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "merchant/remedies": {"method": "POST", "requestSchema": "VastuMerchantRemediesRequest", "responseSchema": "VastuMerchantRemediesResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "portfolio/search": {"method": "POST", "requestSchema": "VastuPortfolioSearchRequest", "responseSchema": "VastuPortfolioSearchResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "portfolio/compare": {"method": "POST", "requestSchema": "VastuPortfolioCompareRequest", "responseSchema": "VastuPortfolioCompareResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "portfolio/analytics": {"method": "POST", "requestSchema": "VastuPortfolioAnalyticsRequest", "responseSchema": "VastuPortfolioAnalyticsResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "portfolio/usage": {"method": "POST", "requestSchema": "VastuPortfolioUsageRequest", "responseSchema": "VastuPortfolioUsageResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "portfolio/usage/export": {"method": "POST", "requestSchema": "VastuPortfolioUsageExportRequest", "responseSchema": "VastuPortfolioUsageExportResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "portfolio/budgets/set": {"method": "POST", "requestSchema": "VastuPortfolioBudgetsSetRequest", "responseSchema": "VastuPortfolioBudgetsSetResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "portfolio/budgets/get": {"method": "POST", "requestSchema": "VastuPortfolioBudgetsGetRequest", "responseSchema": "VastuPortfolioBudgetsGetResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},

    "report/drawing-sheet": {"method": "POST", "requestSchema": "VastuDrawingSheetRequest", "responseSchema": "VastuDrawingSheetResponse", "auth": "apiKey", "errors": (400, 401, 402, 403, 404, 405, 409, 410, 413, 415, 503)},
    "properties/create": {"method": "POST", "requestSchema": "VastuPropertiesCreateRequest", "responseSchema": "VastuPropertiesCreateResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "properties/update": {"method": "POST", "requestSchema": "VastuPropertiesUpdateRequest", "responseSchema": "VastuPropertiesUpdateResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "properties/collaboration/get": {"method": "POST", "requestSchema": "VastuPropertiesCollaborationGetRequest", "responseSchema": "VastuPropertiesCollaborationGetResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/collaboration/invite": {"method": "POST", "requestSchema": "VastuPropertiesCollaborationInviteRequest", "responseSchema": "VastuPropertiesCollaborationInviteResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 429, 503)},
    "properties/collaboration/revoke": {"method": "POST", "requestSchema": "VastuPropertiesCollaborationRevokeRequest", "responseSchema": "VastuPropertiesCollaborationRevokeResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/collaboration/members": {"method": "POST", "requestSchema": "VastuPropertiesCollaborationMembersRequest", "responseSchema": "VastuPropertiesCollaborationMembersResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/collaboration/comment": {"method": "POST", "requestSchema": "VastuPropertiesCollaborationCommentRequest", "responseSchema": "VastuPropertiesCollaborationCommentResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/collaboration/review": {"method": "POST", "requestSchema": "VastuPropertiesCollaborationReviewRequest", "responseSchema": "VastuPropertiesCollaborationReviewResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/collaboration/update": {"method": "POST", "requestSchema": "VastuPropertiesCollaborationUpdateRequest", "responseSchema": "VastuPropertiesCollaborationUpdateResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/activity/list": {"method": "POST", "requestSchema": "VastuPropertiesActivityListRequest", "responseSchema": "VastuPropertiesActivityListResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/activity/export": {"method": "POST", "requestSchema": "VastuPropertiesActivityExportRequest", "responseSchema": "VastuPropertiesActivityExportResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/get": {"method": "POST", "requestSchema": "VastuPropertiesGetRequest", "responseSchema": "VastuPropertiesGetResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/list": {"method": "POST", "requestSchema": "VastuPropertiesListRequest", "responseSchema": "VastuPropertiesListResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/delete": {"method": "POST", "requestSchema": "VastuPropertiesDeleteRequest", "responseSchema": "VastuPropertiesDeleteResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "properties/link-scan": {"method": "POST", "requestSchema": "VastuPropertiesLinkScanRequest", "responseSchema": "VastuPropertiesLinkScanResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "archive/tier": {"method": "POST", "requestSchema": "VastuArchiveTierRequest", "responseSchema": "VastuArchiveTierResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "archive/export": {"method": "POST", "requestSchema": "VastuArchiveExportRequest", "responseSchema": "VastuArchiveExportResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "archive/delete": {"method": "POST", "requestSchema": "VastuArchiveDeleteRequest", "responseSchema": "VastuArchiveDeleteResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "archive/summary": {"method": "POST", "requestSchema": "VastuArchiveSummaryRequest", "responseSchema": "VastuArchiveSummaryResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "feed/listings": {"method": "POST", "requestSchema": "VastuFeedListingsRequest", "responseSchema": "VastuFeedListingsResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 503)},
    "quote/calculate": {"method": "POST", "requestSchema": "VastuQuoteCalculateRequest", "responseSchema": "VastuQuoteCalculateResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},

    "scans/timelapse": {"method": "POST", "requestSchema": "VastuScansTimelapseRequest", "responseSchema": "VastuScansTimelapseResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "scans/delete": {"method": "POST", "requestSchema": "VastuScansDeleteRequest", "responseSchema": "VastuScansDeleteResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "scans/list": {"method": "POST", "requestSchema": "VastuScansListRequest", "responseSchema": "VastuScansListResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "scans/retrieve": {"method": "POST", "requestSchema": "VastuScansRetrieveRequest", "responseSchema": "VastuScansRetrieveResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "scans/save": {"method": "POST", "requestSchema": "VastuScansSaveRequest", "responseSchema": "VastuScansSaveResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "ar/deity-icons": {"method": "POST", "requestSchema": "VastuArDeityIconsRequest", "responseSchema": "VastuArDeityIconsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/capture-merge": {"method": "POST", "requestSchema": "VastuArCaptureMergeRequest", "responseSchema": "VastuArCaptureMergeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "plot/from-survey": {"method": "POST", "requestSchema": "VastuPlotFromSurveyRequest", "responseSchema": "VastuPlotFromSurveyResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "ar/room-capture": {"method": "POST", "requestSchema": "VastuArRoomCaptureRequest", "responseSchema": "VastuArRoomCaptureResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "ar/attestation/challenge": {"method": "POST", "requestSchema": "VastuArAttestationChallengeRequest", "responseSchema": "VastuArAttestationChallengeResponse", "auth": "apiKey", "errors": (400, 401, 405, 415, 503)},
    "ar/yantra-meshes": {"method": "POST", "requestSchema": "VastuArYantraMeshesRequest", "responseSchema": "VastuArYantraMeshesResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/zone-textures": {"method": "POST", "requestSchema": "VastuArZoneTexturesRequest", "responseSchema": "VastuArZoneTexturesResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/anchor-recommendations": {"method": "POST", "requestSchema": "VastuArAnchorRecommendationsRequest", "responseSchema": "VastuArAnchorRecommendationsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/heatmap-raster": {"method": "POST", "requestSchema": "VastuArHeatmapRasterRequest", "responseSchema": "VastuArHeatmapRasterResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/scan-quality": {"method": "POST", "requestSchema": "VastuArScanQualityRequest", "responseSchema": "VastuArScanQualityResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "ar/true-north-calibrate": {"method": "POST", "requestSchema": "VastuArTrueNorthCalibrateRequest", "responseSchema": "VastuArTrueNorthCalibrateResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/compare-versions": {"method": "POST", "requestSchema": "VastuCompareVersionsRequest", "responseSchema": "VastuCompareVersionsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 503)},
    "receipt/verify": {"method": "POST", "requestSchema": "VastuReceiptVerifyRequest", "responseSchema": "VastuReceiptVerifyResponse", "auth": "apiKey", "errors": (400, 401, 405, 415, 503)},
    "rules/versions": {"method": "GET", "requestSchema": None, "responseSchema": "VastuRuleVersionsResponse", "auth": "apiKey", "errors": (400, 401, 405, 503)},
    "assessments": {"method": "POST", "requestSchema": "VastuAssessmentsRequest", "responseSchema": "VastuAssessmentsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "assessments/batch": {"method": "POST", "requestSchema": "VastuAssessmentsBatchRequest", "responseSchema": "VastuAssessmentsBatchResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "jobs": {"method": "POST", "requestSchema": "VastuJobsRequest", "responseSchema": "VastuJobsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 409, 415, 429, 503)},
    "jobs/{id}": {"method": "GET", "requestSchema": None, "responseSchema": "VastuJobsIdResponse", "auth": "apiKey", "errors": (401, 404, 405, 503)},
    "jobs/{id}/results": {"method": "GET", "requestSchema": None, "responseSchema": "VastuJobsIdResultsResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 410, 503)},
    "jobs/{id}/cancel": {"method": "POST", "requestSchema": None, "responseSchema": "VastuJobsIdCancelResponse", "auth": "apiKey", "errors": (401, 404, 405, 415, 503)},
    "audit/floor-plan": {"method": "POST", "requestSchema": "VastuAuditFloorPlanRequest", "responseSchema": "VastuAuditFloorPlanResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 429, 500)},
    "audit/floor-plan-detailed": {"method": "POST", "requestSchema": "VastuAuditFloorPlanDetailedRequest", "responseSchema": "VastuAuditFloorPlanDetailedResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "audit/single-room": {"method": "POST", "requestSchema": "VastuAuditSingleRoomRequest", "responseSchema": "VastuAuditSingleRoomResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "compare/before-after-remedy": {"method": "POST", "requestSchema": "VastuCompareBeforeAfterRemedyRequest", "responseSchema": "VastuCompareBeforeAfterRemedyResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "compound/wall-analysis": {"method": "POST", "requestSchema": "VastuCompoundWallAnalysisRequest", "responseSchema": "VastuCompoundWallAnalysisResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "direction/auspicious-facing": {"method": "POST", "requestSchema": "VastuDirectionAuspiciousFacingRequest", "responseSchema": "VastuDirectionAuspiciousFacingResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "direction/correct": {"method": "POST", "requestSchema": "VastuDirectionCorrectRequest", "responseSchema": "VastuDirectionCorrectResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "direction/declination": {"method": "GET_OR_POST", "requestSchema": "VastuDirectionDeclinationRequest", "responseSchema": "VastuDirectionDeclinationResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "direction/sun-path": {"method": "POST", "requestSchema": "VastuDirectionSunPathRequest", "responseSchema": "VastuDirectionSunPathResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "direction/zone-from-bearing": {"method": "POST", "requestSchema": "VastuDirectionZoneFromBearingRequest", "responseSchema": "VastuDirectionZoneFromBearingResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "elements/balance-suggest": {"method": "POST", "requestSchema": "VastuElementsBalanceSuggestRequest", "responseSchema": "VastuElementsBalanceSuggestResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "elements/distribution": {"method": "POST", "requestSchema": "VastuElementsDistributionRequest", "responseSchema": "VastuElementsDistributionResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "entrance/obstruction-check": {"method": "POST", "requestSchema": "VastuEntranceObstructionCheckRequest", "responseSchema": "VastuEntranceObstructionCheckResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "entrance/pada": {"method": "POST", "requestSchema": "VastuEntrancePadaRequest", "responseSchema": "VastuEntrancePadaResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "entrance/recommend": {"method": "POST", "requestSchema": "VastuEntranceRecommendRequest", "responseSchema": "VastuEntranceRecommendResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "floor/level-analysis": {"method": "POST", "requestSchema": "VastuFloorLevelAnalysisRequest", "responseSchema": "VastuFloorLevelAnalysisResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "fusion/chart": {"method": "POST", "requestSchema": "VastuFusionChartRequest", "responseSchema": "VastuFusionChartResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "mandala/project/81-pada": {"method": "POST", "requestSchema": "VastuMandalaProject81PadaRequest", "responseSchema": "VastuMandalaProject81PadaResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "mandala/project/9-zone": {"method": "POST", "requestSchema": "VastuMandalaProject9ZoneRequest", "responseSchema": "VastuMandalaProject9ZoneResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "mandala/project/brahmasthan": {"method": "POST", "requestSchema": "VastuMandalaProjectBrahmasthanRequest", "responseSchema": "VastuMandalaProjectBrahmasthanResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "multi-storey/floor-rules": {"method": "POST", "requestSchema": "VastuMultiStoreyFloorRulesRequest", "responseSchema": "VastuMultiStoreyFloorRulesResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/balcony": {"method": "POST", "requestSchema": "VastuPlacementBalconyRequest", "responseSchema": "VastuPlacementBalconyResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/borewell": {"method": "POST", "requestSchema": "VastuPlacementBorewellRequest", "responseSchema": "VastuPlacementBorewellResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/garden": {"method": "POST", "requestSchema": "VastuPlacementGardenRequest", "responseSchema": "VastuPlacementGardenResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/generator-electrical": {"method": "POST", "requestSchema": "VastuPlacementGeneratorElectricalRequest", "responseSchema": "VastuPlacementGeneratorElectricalResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/main-gate": {"method": "POST", "requestSchema": "VastuPlacementMainGateRequest", "responseSchema": "VastuPlacementMainGateResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/overhead-tank": {"method": "POST", "requestSchema": "VastuPlacementOverheadTankRequest", "responseSchema": "VastuPlacementOverheadTankResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/septic-tank": {"method": "POST", "requestSchema": "VastuPlacementSepticTankRequest", "responseSchema": "VastuPlacementSepticTankResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/tree": {"method": "POST", "requestSchema": "VastuPlacementTreeRequest", "responseSchema": "VastuPlacementTreeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/well": {"method": "POST", "requestSchema": "VastuPlacementWellRequest", "responseSchema": "VastuPlacementWellResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "placement/window": {"method": "POST", "requestSchema": "VastuPlacementWindowRequest", "responseSchema": "VastuPlacementWindowResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/analyze": {"method": "POST", "requestSchema": "VastuPlanAnalyzeRequest", "responseSchema": "VastuPlanAnalyzeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "plan/from-requirements": {"method": "POST", "requestSchema": "VastuPlanFromRequirementsRequest", "responseSchema": "VastuPlanFromRequirementsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/generate": {"method": "POST", "requestSchema": "VastuPlanGenerateRequest", "responseSchema": "VastuPlanGenerateResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/optimize": {"method": "POST", "requestSchema": "VastuPlanOptimizeRequest", "responseSchema": "VastuPlanOptimizeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/report": {"method": "POST", "requestSchema": "VastuPlanReportRequest", "responseSchema": "VastuPlanReportResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/import-dxf": {"method": "POST", "requestSchema": "VastuPlanImportDxfRequest", "responseSchema": "VastuPlanImportDxfResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "plan/export-dxf": {"method": "POST", "requestSchema": "VastuPlanExportDxfRequest", "responseSchema": "VastuPlanExportDxfResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "plan/export-ifc": {"method": "POST", "requestSchema": "VastuPlanExportIfcRequest", "responseSchema": "VastuPlanExportIfcResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "plan/convert-units": {"method": "POST", "requestSchema": "VastuPlanConvertUnitsRequest", "responseSchema": "VastuPlanConvertUnitsResponse", "auth": "apiKey", "errors": (400, 401, 405, 415, 500, 503)},
    "plan/import-ifc": {"method": "POST", "requestSchema": "VastuPlanImportIfcRequest", "responseSchema": "VastuPlanImportIfcResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "plan/import-image": {"method": "POST", "requestSchema": "VastuPlanImportImageRequest", "responseSchema": "VastuPlanImportImageResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 413, 415, 422, 500, 503)},
    "plan/import-pdf": {"method": "POST", "requestSchema": "VastuPlanImportPdfRequest", "responseSchema": "VastuPlanImportPdfResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 413, 415, 422, 500, 503)},
    "plan/upload": {"method": "POST", "requestSchema": "VastuPlanUploadRequest", "responseSchema": "VastuPlanUploadResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plot/extensions-cuts": {"method": "POST", "requestSchema": "VastuPlotExtensionsCutsRequest", "responseSchema": "VastuPlotExtensionsCutsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plot/orientation": {"method": "POST", "requestSchema": "VastuPlotOrientationRequest", "responseSchema": "VastuPlotOrientationResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plot/ratio": {"method": "POST", "requestSchema": "VastuPlotRatioRequest", "responseSchema": "VastuPlotRatioResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plot/road-orientation": {"method": "POST", "requestSchema": "VastuPlotRoadOrientationRequest", "responseSchema": "VastuPlotRoadOrientationResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plot/shape": {"method": "POST", "requestSchema": "VastuPlotShapeRequest", "responseSchema": "VastuPlotShapeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plot/slope": {"method": "POST", "requestSchema": "VastuPlotSlopeRequest", "responseSchema": "VastuPlotSlopeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "reference/colors-by-zone": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceColorsByZoneResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/defects/catalog": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceDefectsCatalogResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/directions/16": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceDirections16Response", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/directions/32": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceDirections32Response", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/directions/8": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceDirections8Response", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/gate-obstructions": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceGateObstructionsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/mandala/45-devatas": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceMandala45DevatasResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/mandala/64-pada": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceMandala64PadaResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/mandala/9-zone": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceMandala9ZoneResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/materials-by-zone": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceMaterialsByZoneResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "reference/remedies/catalog": {"method": "GET", "requestSchema": None, "responseSchema": "VastuReferenceRemediesCatalogResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 500)},
    "room/bedroom": {"method": "POST", "requestSchema": "VastuRoomBedroomRequest", "responseSchema": "VastuRoomBedroomResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/dining": {"method": "POST", "requestSchema": "VastuRoomDiningRequest", "responseSchema": "VastuRoomDiningResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/kitchen": {"method": "POST", "requestSchema": "VastuRoomKitchenRequest", "responseSchema": "VastuRoomKitchenResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/living": {"method": "POST", "requestSchema": "VastuRoomLivingRequest", "responseSchema": "VastuRoomLivingResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/pooja": {"method": "POST", "requestSchema": "VastuRoomPoojaRequest", "responseSchema": "VastuRoomPoojaResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/staircase": {"method": "POST", "requestSchema": "VastuRoomStaircaseRequest", "responseSchema": "VastuRoomStaircaseResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/store": {"method": "POST", "requestSchema": "VastuRoomStoreRequest", "responseSchema": "VastuRoomStoreResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/study": {"method": "POST", "requestSchema": "VastuRoomStudyRequest", "responseSchema": "VastuRoomStudyResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/toilet": {"method": "POST", "requestSchema": "VastuRoomToiletRequest", "responseSchema": "VastuRoomToiletResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "room/water-storage": {"method": "POST", "requestSchema": "VastuRoomWaterStorageRequest", "responseSchema": "VastuRoomWaterStorageResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "score/compliance-index": {"method": "POST", "requestSchema": "VastuScoreComplianceIndexRequest", "responseSchema": "VastuScoreComplianceIndexResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "score/overall": {"method": "POST", "requestSchema": "VastuScoreOverallRequest", "responseSchema": "VastuScoreOverallResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "score/zone-wise": {"method": "POST", "requestSchema": "VastuScoreZoneWiseRequest", "responseSchema": "VastuScoreZoneWiseResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500, 503)},
    "specialized/commercial": {"method": "POST", "requestSchema": "VastuSpecializedCommercialRequest", "responseSchema": "VastuSpecializedCommercialResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "specialized/educational": {"method": "POST", "requestSchema": "VastuSpecializedEducationalRequest", "responseSchema": "VastuSpecializedEducationalResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "specialized/factory": {"method": "POST", "requestSchema": "VastuSpecializedFactoryRequest", "responseSchema": "VastuSpecializedFactoryResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "specialized/hospital": {"method": "POST", "requestSchema": "VastuSpecializedHospitalRequest", "responseSchema": "VastuSpecializedHospitalResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "specialized/residential": {"method": "POST", "requestSchema": "VastuSpecializedResidentialRequest", "responseSchema": "VastuSpecializedResidentialResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "specialized/restaurant": {"method": "POST", "requestSchema": "VastuSpecializedRestaurantRequest", "responseSchema": "VastuSpecializedRestaurantResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "specialized/temple": {"method": "POST", "requestSchema": "VastuSpecializedTempleRequest", "responseSchema": "VastuSpecializedTempleResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "timing/bhumi-pujan": {"method": "POST", "requestSchema": "VastuTimingBhumiPujanRequest", "responseSchema": "VastuTimingBhumiPujanResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "timing/construction-start": {"method": "POST", "requestSchema": "VastuTimingConstructionStartRequest", "responseSchema": "VastuTimingConstructionStartResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "timing/grihapravesh": {"method": "POST", "requestSchema": "VastuTimingGrihapraveshRequest", "responseSchema": "VastuTimingGrihapraveshResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "timing/vastu-shanti": {"method": "POST", "requestSchema": "VastuTimingVastuShantiRequest", "responseSchema": "VastuTimingVastuShantiResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
}

VastuJsonValue = Union[str, int, float, bool, None, List["VastuJsonValue"], Dict[str, "VastuJsonValue"]]

class _VastuArHeatmapRasterRequestRoomsItemBoundsOptional(TypedDict, total=False):
    headingErrorDeg: float
    positionErrorM: float

class VastuArHeatmapRasterRequestRoomsItem(_VastuArHeatmapRasterRequestRoomsItemBoundsOptional):
    roomType: str
    zone: str

class _VastuArHeatmapRasterRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    plotPolygon: List[List[float]]
    bearingDeg: float

class VastuArHeatmapRasterRequest(_VastuArHeatmapRasterRequestOptional):
    rooms: List[VastuArHeatmapRasterRequestRoomsItem]

class VastuArPlanToWorld(TypedDict):
    units: Literal["metres", "m", "ft", "mm", "in"]
    origin: List[float]
    xAxis: List[float]
    yAxis: List[float]

class _VastuArAnchorRecommendationsRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuArAnchorRecommendationsRequest(_VastuArAnchorRecommendationsRequestAttribution):
    plotPolygon: List[List[float]]
    bearingDeg: float
    planToWorld: VastuArPlanToWorld

class _VastuArZoneTexturesRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]

class VastuArZoneTexturesRequest(_VastuArZoneTexturesRequestOptional):
    pass

class _VastuArYantraMeshesRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    format: Literal["gltf", "usdz"]

class VastuArYantraMeshesRequest(_VastuArYantraMeshesRequestOptional):
    model: Literal["nine-zone-mandala"]

class _VastuArDeityIconsRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]

class VastuArDeityIconsRequest(_VastuArDeityIconsRequestOptional):
    pass

class VastuRoomCaptureDevice(TypedDict):
    platform: Literal["ios", "android", "web"]
    method: Literal["roomplan", "arkit-raycast", "arcore-hit", "webxr-hit", "manual-trace"]
    depth: Literal["lidar", "arcore-depth", "none"]

class _VastuRoomCaptureFrameNorthOptional(TypedDict, total=False):
    declinationDeg: Optional[float]
    yawSpreadDeg: Optional[float]

class VastuRoomCaptureFrameNorth(_VastuRoomCaptureFrameNorthOptional):
    referenceFrame: Literal["true", "manual", "magnetic"]
    headingSource: str
    declinationProvenance: Literal["live", "manual", "native", "fixture", "unset"]
    yawSamples: int
    compassConfidence: float

class _VastuRoomCaptureFrameOptional(TypedDict, total=False):
    units: str
    planToWorld: Optional[VastuArPlanToWorld]

class VastuRoomCaptureFrame(_VastuRoomCaptureFrameOptional):
    units: Literal["metres", "m", "ft", "mm", "in"]
    axes: Literal["+X east,+Y true north"]
    north: VastuRoomCaptureFrameNorth

class _VastuRoomCaptureOutlineOptional(TypedDict, total=False):
    polygon: List[List[float]]
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]

class VastuRoomCaptureOutline(_VastuRoomCaptureOutlineOptional):
    source: Literal["traced"]

class _VastuRoomCaptureRoomsItemOpeningsItemOptional(TypedDict, total=False):
    heightM: Optional[float]

class VastuRoomCaptureRoomsItemOpeningsItem(_VastuRoomCaptureRoomsItemOpeningsItemOptional):
    kind: Literal["door", "window", "opening"]
    centerXY: List[float]
    widthM: float
    confidence: Literal["low", "medium", "high"]

class _VastuRoomCaptureRoomsItemOptional(TypedDict, total=False):
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    id: str
    headingErrorDeg: float
    positionErrorM: float
    heightM: Optional[float]
    openings: List[VastuRoomCaptureRoomsItemOpeningsItem]

class VastuRoomCaptureRoomsItem(_VastuRoomCaptureRoomsItemOptional):
    id: str
    label: Optional[str]
    labelSource: Literal["user", "roomplan-section", "none"]
    polygon: List[List[float]]
    areaM2: float
    floorIndex: int

class _VastuRoomCaptureQualityOptional(TypedDict, total=False):
    closureGapM: Optional[float]
    pointCloudDensity: Optional[float]
    coveragePercent: Optional[float]
    scanDurationSec: Optional[float]
    scannedAreaM2: Optional[float]
    expectedRoomCount: Optional[int]
    gpsConfidence: Optional[float]

class VastuRoomCaptureQuality(_VastuRoomCaptureQualityOptional):
    polygonClosure: bool
    pointCloudDensityBasis: Literal["feature-points", "lidar-depth", "none"]
    roomCount: int
    roomsTagged: int

class VastuRoomCapture(TypedDict):
    schema: Literal["vedika.roomCapture/1"]
    captureId: str
    capturedAtEpoch: int
    device: VastuRoomCaptureDevice
    frame: VastuRoomCaptureFrame
    outline: VastuRoomCaptureOutline
    rooms: List[VastuRoomCaptureRoomsItem]
    quality: VastuRoomCaptureQuality
    attestation: Literal["caller-reported"]

class _VastuDeviceAttestationOptional(TypedDict, total=False):
    keyId: str
    attestationObject: str
    assertion: str
    integrityToken: str

class VastuDeviceAttestation(_VastuDeviceAttestationOptional):
    """Optional native-app device attestation proof; see ``ar/attestation/challenge``."""
    platform: Literal["ios", "android"]
    challenge: str

class _VastuArAttestationChallengeRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuArAttestationChallengeRequest(_VastuArAttestationChallengeRequestAttribution):
    platform: Literal["ios", "android"]

class VastuArCaptureMergeRequestLinksItemControlPointsItem(TypedDict):
    fromXY: List[float]
    toXY: List[float]


class VastuArCaptureMergeRequestLinksItemSharedDoorsItem(TypedDict):
    fromXY: List[float]
    toXY: List[float]


class VastuArCaptureMergeRequestFloorsItem(TypedDict):
    floorIndex: int
    elevationM: float
    originXY: List[float]
    bearingDeg: float


class VastuArCaptureMergeRequestCapturesItem(TypedDict):
    id: str
    floorIndex: int
    payload: VastuRoomCapture


class _VastuArCaptureMergeRequestLinksItemOptional(TypedDict, total=False):
    controlPoints: List[VastuArCaptureMergeRequestLinksItemControlPointsItem]
    sharedDoors: List[VastuArCaptureMergeRequestLinksItemSharedDoorsItem]

class VastuArCaptureMergeRequestLinksItem(_VastuArCaptureMergeRequestLinksItemOptional):
    fromCaptureId: str
    toCaptureId: str


class VastuPlotFromSurveyRequestControlPointsItem(TypedDict):
    id: str
    xy: List[float]


class _VastuArCaptureMergeRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    maxChargeUsd: str

class VastuArCaptureMergeRequest(_VastuArCaptureMergeRequestOptional):
    captures: List[VastuArCaptureMergeRequestCapturesItem]
    links: List[VastuArCaptureMergeRequestLinksItem]
    floors: List[VastuArCaptureMergeRequestFloorsItem]
    toleranceM: float


class _VastuPlotFromSurveyRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    maxChargeUsd: str
    units: str
    controlPoints: List[VastuPlotFromSurveyRequestControlPointsItem]
    origin: List[float]

class VastuPlotFromSurveyRequest(_VastuPlotFromSurveyRequestOptional):
    crs: str
    units: str
    boundary: List[List[float]]


class _VastuOptimizationConstraintsWetShaftsItemOptional(TypedDict, total=False):
    roomIds: List[str]
    maxDistanceM: float

class VastuOptimizationConstraintsWetShaftsItem(_VastuOptimizationConstraintsWetShaftsItemOptional):
    id: str
    polygon: List[List[float]]


class _VastuOptimizationConstraintsPlumbingStacksItemOptional(TypedDict, total=False):
    roomIds: List[str]
    maxDistanceM: float

class VastuOptimizationConstraintsPlumbingStacksItem(_VastuOptimizationConstraintsPlumbingStacksItemOptional):
    id: str
    polygon: List[List[float]]


class _VastuOptimizationConstraintsColumnsItemOptional(TypedDict, total=False):
    id: str

class VastuOptimizationConstraintsColumnsItem(_VastuOptimizationConstraintsColumnsItemOptional):
    polygon: List[List[float]]


class _VastuOptimizationConstraintsLoadBearingWallsItemOptional(TypedDict, total=False):
    id: str

class VastuOptimizationConstraintsLoadBearingWallsItem(_VastuOptimizationConstraintsLoadBearingWallsItemOptional):
    polygon: List[List[float]]


class _VastuOptimizationConstraintsOptional(TypedDict, total=False):
    lockedRooms: List[str]
    wetShafts: List[VastuOptimizationConstraintsWetShaftsItem]
    plumbingStacks: List[VastuOptimizationConstraintsPlumbingStacksItem]
    loadBearingWalls: List[VastuOptimizationConstraintsLoadBearingWallsItem]
    columns: List[VastuOptimizationConstraintsColumnsItem]
    minSizes: Dict[str, VastuJsonValue]

class VastuOptimizationConstraints(_VastuOptimizationConstraintsOptional):
    pass


class _VastuArRoomCaptureRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    zoneResolution: Literal[8, 16, 32]
    deviceAttestation: VastuDeviceAttestation

class VastuArRoomCaptureRequest(_VastuArRoomCaptureRequestOptional):
    capture: VastuRoomCapture

class VastuScanSnapshotRoomsItem(TypedDict):
    roomType: str
    zone: str

class _VastuScanTelemetryOptional(TypedDict, total=False):
    roomCount: int
    expectedRoomCount: int

class VastuScanTelemetry(_VastuScanTelemetryOptional):
    pointCloudDensity: float
    polygonClosure: bool
    compassConfidence: float
    gpsConfidence: float
    roomsTagged: int
    scanDurationSec: float
    scannedAreaM2: float

class _VastuScanSnapshotOptional(TypedDict, total=False):
    rooms: List[VastuScanSnapshotRoomsItem]
    plotPolygon: List[List[float]]
    bearingDeg: float
    telemetry: VastuScanTelemetry
    capture: VastuRoomCapture

class VastuScanSnapshot(_VastuScanSnapshotOptional):
    inputSource: Literal["self-reported", "plan-derived", "device-reported"]

class _VastuScansSaveRequestOptional(TypedDict, total=False):
    tenantRef: str
    deviceAttestation: VastuDeviceAttestation

class VastuScansSaveRequest(_VastuScansSaveRequestOptional):
    scanId: str
    propertyId: str
    title: str
    retentionDays: int
    snapshot: VastuScanSnapshot

class _VastuScansRetrieveRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuScansRetrieveRequest(_VastuScansRetrieveRequestAttribution):
    requestId: str
    scanId: str

class _VastuScansListRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    cursor: Optional[str]

class VastuScansListRequest(_VastuScansListRequestOptional):
    requestId: str
    limit: int

class _VastuScansDeleteRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuScansDeleteRequest(_VastuScansDeleteRequestAttribution):
    scanId: str

class _VastuScansTimelapseRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuScansTimelapseRequest(_VastuScansTimelapseRequestAttribution):
    requestId: str
    scanIds: List[str]


class VastuArScanDimension(TypedDict):
    score: Optional[int]
    reason: str
    status: Literal["reported", "unknown"]
class VastuArScanCoverageDimension(VastuArScanDimension):
    basis: Literal["reported-percent", "duration-area-proxy", "unknown"]
class VastuArScanPointCloudDensityDimension(VastuArScanDimension):
    basis: Literal["feature-points", "lidar-depth", "none", "unreported"]
class VastuArScanDimensions(TypedDict):
    pointCloudDensity: VastuArScanPointCloudDensityDimension
    polygonClosure: VastuArScanDimension
    compassConfidence: VastuArScanDimension
    gpsConfidence: VastuArScanDimension
    roomsTagged: VastuArScanDimension
    coverage: VastuArScanCoverageDimension
class VastuArTrueNorthResultInput(TypedDict):
    lat: float
    lon: float
    datetime: str
    deviceHeadingAtSunDeg: float
class _VastuArScanQualityRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointCloudDensity: float
    polygonClosure: bool
    roomsTagged: Union[int, bool]
    compassConfidence: float
    gpsConfidence: float
    scanDurationSec: float
    scannedAreaM2: float
    roomCount: int
    expectedRoomCount: int
    pointCloudDensityPerM2: float
    polygonClosed: bool
    coveragePercent: float
    pointCloudDensityBasis: Optional[Literal["feature-points", "lidar-depth", "none"]]
    deviceAttestation: VastuDeviceAttestation

class VastuArScanQualityRequest(_VastuArScanQualityRequestOptional):
    pass

class _VastuArTrueNorthCalibrateRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    deviceHeadingAccuracyDeg: float
    headingSampleAgeMs: float

class VastuArTrueNorthCalibrateRequest(_VastuArTrueNorthCalibrateRequestOptional):
    lat: float
    lon: float
    datetime: str
    deviceHeadingAtSunDeg: float

class _VastuAssessmentRoomOptional(TypedDict, total=False):
    direction: str
    polygon: List[List[float]]
    area: float

class VastuAssessmentRoom(_VastuAssessmentRoomOptional):
    roomType: str
    zone: str

class _VastuAssessmentsRequestOptional(TypedDict, total=False):
    rulesVersion: str
    receipt: bool
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    rooms: List[VastuAssessmentRoom]
    plotPolygon: List[List[float]]
    doorXY: List[float]
    bearingDeg: float
    confidence: float
    pointCloudDensity: float
    polygonClosure: bool
    roomsTagged: bool
    compassConfidence: float
    gpsConfidence: float
    scanDurationSec: float
    scannedAreaM2: float

class VastuAssessmentsRequest(_VastuAssessmentsRequestOptional):
    inputSource: str

class VastuAssessmentsBatchRequestItemsItem(TypedDict):
    id: str
    assessment: VastuAssessmentsRequest

class _VastuAssessmentsBatchRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuAssessmentsBatchRequest(_VastuAssessmentsBatchRequestAttribution):
    """One to twenty items with unique IDs; retain the caller key for retries."""
    items: List[VastuAssessmentsBatchRequestItemsItem]


class _VastuAuditFloorPlanDetailedRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    plotPolygon: List[List[float]]
    bearingDeg: float

class VastuAuditFloorPlanDetailedRequest(_VastuAuditFloorPlanDetailedRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuAuditFloorPlanRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    rooms: List[Dict[str, VastuJsonValue]]
    text: str

class VastuAuditFloorPlanRequest(_VastuAuditFloorPlanRequestOptional):
    pass

class _VastuAuditSingleRoomRequestGeomOptional(TypedDict, total=False):
    merchantCatalogId: str
    headingErrorDeg: float
    positionErrorM: float

class _VastuAuditSingleRoomRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuAuditSingleRoomRequest(_VastuAuditSingleRoomRequestGeomOptional):
    roomType: str
    zone: str

class _VastuCompareBeforeAfterRemedyRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    rooms: List[Dict[str, VastuJsonValue]]
    text: str

class VastuCompareBeforeAfterRemedyRequest(_VastuCompareBeforeAfterRemedyRequestOptional):
    remedies: List[Dict[str, VastuJsonValue]]

class _VastuCompoundWallAnalysisRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    walls: Union[List[Dict[str, VastuJsonValue]], Dict[str, VastuJsonValue]]

class VastuCompoundWallAnalysisRequest(_VastuCompoundWallAnalysisRequestOptional):
    pass

class _VastuDirectionAuspiciousFacingRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    occupant: str

class VastuDirectionAuspiciousFacingRequest(_VastuDirectionAuspiciousFacingRequestOptional):
    purpose: str

class _VastuDirectionCorrectRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    date: str

class VastuDirectionCorrectRequest(_VastuDirectionCorrectRequestOptional):
    direction: str
    lat: float
    lon: float

class _VastuDirectionDeclinationRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    date: str

class VastuDirectionDeclinationRequest(_VastuDirectionDeclinationRequestOptional):
    lat: float
    lon: float

class _VastuDirectionSunPathRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    date: str

class VastuDirectionSunPathRequest(_VastuDirectionSunPathRequestOptional):
    lat: float
    lon: float

class _VastuDirectionZoneFromBearingRequestGeomOptional(TypedDict, total=False):
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float

class _VastuDirectionZoneFromBearingRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuDirectionZoneFromBearingRequest(_VastuDirectionZoneFromBearingRequestGeomOptional):
    bearingDeg: float

class _VastuElementsBalanceSuggestRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    distribution: Dict[str, VastuJsonValue]
    deficient: List[str]
    excess: List[str]

class VastuElementsBalanceSuggestRequest(_VastuElementsBalanceSuggestRequestOptional):
    pass

class _VastuElementsDistributionRequestGeomOptional(TypedDict, total=False):
    headingErrorDeg: float
    positionErrorM: float

class _VastuElementsDistributionRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuElementsDistributionRequest(_VastuElementsDistributionRequestGeomOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuEntranceObstructionCheckRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    houseHeightMeters: float
    distanceMeters: float

class VastuEntranceObstructionCheckRequest(_VastuEntranceObstructionCheckRequestOptional):
    feature: str

class _VastuEntrancePadaRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    plotPolygon: List[List[float]]
    headingErrorDeg: float
    positionErrorM: float
    bearingDeg: float

class VastuEntrancePadaRequest(_VastuEntrancePadaRequestOptional):
    plotPolygon: List[List[float]]
    doorXY: List[float]

class _VastuEntranceRecommendRequestGeomOptional(TypedDict, total=False):
    headingErrorDeg: float
    positionErrorM: float

class _VastuEntranceRecommendRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuEntranceRecommendRequest(_VastuEntranceRecommendRequestGeomOptional):
    facing: str

class _VastuFloorLevelAnalysisRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    levels: Union[List[Dict[str, VastuJsonValue]], Dict[str, VastuJsonValue]]

class VastuFloorLevelAnalysisRequest(_VastuFloorLevelAnalysisRequestOptional):
    pass

class _VastuFusionChartRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    timezone: str
    facing: str

class VastuFusionChartRequest(_VastuFusionChartRequestOptional):
    datetime: str
    latitude: float
    longitude: float

class _VastuMandalaProject81PadaRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    plotPolygon: List[List[float]]
    headingErrorDeg: float
    positionErrorM: float
    bearingDeg: float
    doorXY: List[float]

class VastuMandalaProject81PadaRequest(_VastuMandalaProject81PadaRequestOptional):
    plotPolygon: List[List[float]]

class _VastuMandalaProject9ZoneRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    plotPolygon: List[List[float]]
    headingErrorDeg: float
    positionErrorM: float
    bearingDeg: float
    doorXY: List[float]

class VastuMandalaProject9ZoneRequest(_VastuMandalaProject9ZoneRequestOptional):
    plotPolygon: List[List[float]]

class _VastuMandalaProjectBrahmasthanRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    plotPolygon: List[List[float]]
    headingErrorDeg: float
    positionErrorM: float
    bearingDeg: float
    doorXY: List[float]

class VastuMandalaProjectBrahmasthanRequest(_VastuMandalaProjectBrahmasthanRequestOptional):
    plotPolygon: List[List[float]]

class _VastuMultiStoreyFloorRulesRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuMultiStoreyFloorRulesRequest(_VastuMultiStoreyFloorRulesRequestAttribution):
    floors: int

class _VastuPlacementBalconyRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementBalconyRequest(_VastuPlacementBalconyRequestOptional):
    pass

class _VastuPlacementBorewellRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementBorewellRequest(_VastuPlacementBorewellRequestOptional):
    pass

class _VastuPlacementGardenRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementGardenRequest(_VastuPlacementGardenRequestOptional):
    pass

class _VastuPlacementGeneratorElectricalRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementGeneratorElectricalRequest(_VastuPlacementGeneratorElectricalRequestOptional):
    pass

class _VastuPlacementMainGateRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    direction: str
    zone: str
    pada: int

class VastuPlacementMainGateRequest(_VastuPlacementMainGateRequestOptional):
    facing: str

class _VastuPlacementOverheadTankRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementOverheadTankRequest(_VastuPlacementOverheadTankRequestOptional):
    pass

class _VastuPlacementSepticTankRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementSepticTankRequest(_VastuPlacementSepticTankRequestOptional):
    pass

class _VastuPlacementTreeRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementTreeRequest(_VastuPlacementTreeRequestOptional):
    pass

class _VastuPlacementWellRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementWellRequest(_VastuPlacementWellRequestOptional):
    pass

class _VastuPlacementWindowRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementWindowRequest(_VastuPlacementWindowRequestOptional):
    pass

class _VastuCompareVersionsRequestOptional(TypedDict, total=False):
    operation: str

class VastuCompareVersionsRequest(_VastuCompareVersionsRequestOptional):
    fromVersion: str
    toVersion: str
    input: Dict[str, VastuJsonValue]

class _VastuReceiptVerifyRequestOptional(TypedDict, total=False):
    input: Dict[str, VastuJsonValue]

class VastuReceiptVerifyRequest(_VastuReceiptVerifyRequestOptional):
    token: str

class _VastuPlanAnalyzeRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    rulesVersion: str
    receipt: bool
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    headingErrorDeg: float
    positionErrorM: float
    plot: Dict[str, VastuJsonValue]
    zoneResolution: Literal[8, 16, 32]

class VastuPlanAnalyzeRequest(_VastuPlanAnalyzeRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuPlanFromRequirementsRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    plotPolygon: List[VastuJsonValue]
    headingErrorDeg: float
    positionErrorM: float
    entrance: Dict[str, VastuJsonValue]
    rooms: List[Dict[str, VastuJsonValue]]
    requirements: Dict[str, VastuJsonValue]
    parking: Dict[str, VastuJsonValue]
    staircase: Dict[str, VastuJsonValue]
    lift: Dict[str, VastuJsonValue]
    variants: int
    variantSvg: bool
    includeSvg: bool

class VastuPlanFromRequirementsRequest(_VastuPlanFromRequirementsRequestOptional):
    plot: Dict[str, VastuJsonValue]

class _VastuPlanGenerateRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    plotPolygon: List[VastuJsonValue]
    headingErrorDeg: float
    positionErrorM: float
    entrance: Dict[str, VastuJsonValue]
    rooms: List[Dict[str, VastuJsonValue]]
    requirements: Dict[str, VastuJsonValue]
    parking: Dict[str, VastuJsonValue]
    staircase: Dict[str, VastuJsonValue]
    lift: Dict[str, VastuJsonValue]
    variants: int
    variantSvg: bool
    includeSvg: bool

class VastuPlanGenerateRequest(_VastuPlanGenerateRequestOptional):
    plot: Dict[str, VastuJsonValue]

class _VastuPlanOptimizeRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    plotPolygon: List[VastuJsonValue]
    lockedRooms: List[str]
    wetShafts: List[Dict[str, VastuJsonValue]]
    plumbingStacks: List[Dict[str, VastuJsonValue]]
    loadBearingWalls: List[Dict[str, VastuJsonValue]]
    columns: List[Dict[str, VastuJsonValue]]
    minSizes: Dict[str, VastuJsonValue]
    constraints: VastuOptimizationConstraints
    headingErrorDeg: float
    positionErrorM: float
    plot: Dict[str, VastuJsonValue]
    includeSvg: bool

class VastuPlanOptimizeRequest(_VastuPlanOptimizeRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class VastuPlanReportRequestBrand(TypedDict, total=False):
    reportTitle: str
    generatedFor: str

class _VastuPlanReportRequestCompositionCtaBlocksItemOptional(TypedDict, total=False):
    phone: Optional[str]

class VastuPlanReportRequestCompositionCtaBlocksItem(_VastuPlanReportRequestCompositionCtaBlocksItemOptional):
    label: str
    link: str

class _VastuPlanReportRequestCompositionOptional(TypedDict, total=False):
    sections: List[Literal["summary", "facing", "plot-shape", "compliance", "rooms", "zones", "defects", "remedies", "elements", "sources"]]
    intro: Optional[str]
    outro: Optional[str]
    ctaBlocks: List[VastuPlanReportRequestCompositionCtaBlocksItem]

class VastuPlanReportRequestComposition(_VastuPlanReportRequestCompositionOptional):
    pass

class _VastuPlanReportRequestOptional(TypedDict, total=False):
    composition: VastuPlanReportRequestComposition
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    headingErrorDeg: float
    positionErrorM: float
    plot: Dict[str, VastuJsonValue]
    format: Literal["json", "html", "pdf"]
    brand: VastuPlanReportRequestBrand
    reportTitle: str
    generatedFor: str
    tenantName: str

class VastuPlanReportRequest(_VastuPlanReportRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuPlanUploadRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    headingErrorDeg: float
    positionErrorM: float
    rooms: List[Dict[str, VastuJsonValue]]
    layout: Dict[str, VastuJsonValue]
    asciiGrid: str
    plot: Dict[str, VastuJsonValue]

class _VastuPlanImportOptions(TypedDict, total=False):
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    scaleInputUnitsPerUnit: float
    northBearingDeg: float
    scaleMetersPerUnit: float

class _VastuPlanImportImageRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuPlanImportImageRequest(_VastuPlanImportOptions):
    fileBase64: str

class _VastuPlanImportPdfRequestAttribution(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuPlanImportPdfRequest(VastuPlanImportImageRequest):
    page: int

class VastuPlanUploadRequest(_VastuPlanUploadRequestOptional):
    pass

class _VastuPlotExtensionsCutsRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    plotPolygon: List[List[float]]
    length: float
    width: float

class VastuPlotExtensionsCutsRequest(_VastuPlotExtensionsCutsRequestOptional):
    pass

class _VastuPlotOrientationRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facingBearingDeg: float
    bearingDeg: float

class VastuPlotOrientationRequest(_VastuPlotOrientationRequestOptional):
    pass

class _VastuPlotRatioRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    plotPolygon: List[List[float]]
    headingErrorDeg: float
    positionErrorM: float
    bearingDeg: float
    doorXY: List[float]

class VastuPlotRatioRequest(_VastuPlotRatioRequestOptional):
    plotPolygon: List[List[float]]

class _VastuPlotRoadOrientationRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    roads: List[str]
    roadSides: List[str]
    veedhiShoola: str
    tPointFrom: str
    roadThrustFrom: str

class VastuPlotRoadOrientationRequest(_VastuPlotRoadOrientationRequestOptional):
    pass

class _VastuPlotShapeRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    plotPolygon: List[List[float]]
    headingErrorDeg: float
    positionErrorM: float
    bearingDeg: float
    doorXY: List[float]

class VastuPlotShapeRequest(_VastuPlotShapeRequestOptional):
    plotPolygon: List[List[float]]

class _VastuPlotSlopeRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    slopeDirection: str
    lowSide: str
    lowCorner: str
    slopeBearingDeg: float

class VastuPlotSlopeRequest(_VastuPlotSlopeRequestOptional):
    pass

class _VastuRoomBedroomRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomBedroomRequest(_VastuRoomBedroomRequestOptional):
    pass

class _VastuRoomDiningRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomDiningRequest(_VastuRoomDiningRequestOptional):
    pass

class _VastuRoomKitchenRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomKitchenRequest(_VastuRoomKitchenRequestOptional):
    pass

class _VastuRoomLivingRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomLivingRequest(_VastuRoomLivingRequestOptional):
    pass

class _VastuRoomPoojaRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomPoojaRequest(_VastuRoomPoojaRequestOptional):
    pass

class _VastuRoomStaircaseRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomStaircaseRequest(_VastuRoomStaircaseRequestOptional):
    pass

class _VastuRoomStoreRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomStoreRequest(_VastuRoomStoreRequestOptional):
    pass

class _VastuRoomStudyRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomStudyRequest(_VastuRoomStudyRequestOptional):
    pass

class _VastuRoomToiletRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomToiletRequest(_VastuRoomToiletRequestOptional):
    pass

class _VastuRoomWaterStorageRequestOptional(TypedDict, total=False):
    merchantCatalogId: str
    propertyId: str
    tenantRef: str
    pointXY: List[float]
    plotPolygon: List[List[float]]
    bearingDeg: float
    headingErrorDeg: float
    positionErrorM: float
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuRoomWaterStorageRequest(_VastuRoomWaterStorageRequestOptional):
    pass

class _VastuScoreComplianceIndexRequestOptional(TypedDict, total=False):
    rulesVersion: str
    receipt: bool
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    plot: Dict[str, VastuJsonValue]

class VastuScoreComplianceIndexRequest(_VastuScoreComplianceIndexRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuScoreOverallRequestOptional(TypedDict, total=False):
    rulesVersion: str
    receipt: bool
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    plot: Dict[str, VastuJsonValue]

class VastuScoreOverallRequest(_VastuScoreOverallRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuScoreZoneWiseRequestOptional(TypedDict, total=False):
    rulesVersion: str
    receipt: bool
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    plot: Dict[str, VastuJsonValue]

class VastuScoreZoneWiseRequest(_VastuScoreZoneWiseRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedCommercialRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedCommercialRequest(_VastuSpecializedCommercialRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedEducationalRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedEducationalRequest(_VastuSpecializedEducationalRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedFactoryRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedFactoryRequest(_VastuSpecializedFactoryRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedHospitalRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedHospitalRequest(_VastuSpecializedHospitalRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedResidentialRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedResidentialRequest(_VastuSpecializedResidentialRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedRestaurantRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedRestaurantRequest(_VastuSpecializedRestaurantRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedTempleRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    headingErrorDeg: float
    positionErrorM: float
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedTempleRequest(_VastuSpecializedTempleRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuTimingBhumiPujanRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingBhumiPujanRequest(_VastuTimingBhumiPujanRequestOptional):
    latitude: float
    longitude: float

class _VastuTimingConstructionStartRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingConstructionStartRequest(_VastuTimingConstructionStartRequestOptional):
    latitude: float
    longitude: float

class _VastuTimingGrihapraveshRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingGrihapraveshRequest(_VastuTimingGrihapraveshRequestOptional):
    latitude: float
    longitude: float

class _VastuTimingVastuShantiRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingVastuShantiRequest(_VastuTimingVastuShantiRequestOptional):
    latitude: float
    longitude: float

class VastuWorkflowBilling(TypedDict):
    charged: str
    currency: Literal["USD"]

class _VastuRemediationTasksUpsertRequestTaskEvidenceItemOptional(TypedDict, total=False):
    photoRef: Optional[str]
    note: Optional[str]

class VastuRemediationTasksUpsertRequestTaskEvidenceItem(_VastuRemediationTasksUpsertRequestTaskEvidenceItemOptional):
    reference: str

class _VastuRemediationTasksUpsertRequestTaskOptional(TypedDict, total=False):
    assignee: Optional[str]
    dueDate: Optional[str]
    evidence: List[VastuRemediationTasksUpsertRequestTaskEvidenceItem]

class VastuRemediationTasksUpsertRequestTask(_VastuRemediationTasksUpsertRequestTaskOptional):
    taskId: str
    reportRef: str
    findingRef: str
    remedyKey: str
    title: str
    status: Literal["pending", "in_progress", "completed", "cancelled"]

class VastuRemediationTasksUpsertRequest(TypedDict):
    expectedRevision: int
    mutationId: str
    propertyId: str
    task: VastuRemediationTasksUpsertRequestTask

class VastuRemediationTasksListRequest(TypedDict):
    propertyId: str

class VastuRemediationTasksDeleteRequest(TypedDict):
    id: str
    confirmId: str

class _VastuRemediationReassessRequestPlanRoomsItemOptional(TypedDict, total=False):
    name: str
    room: str
    roomType: str
    label: str
    zone: str
    direction: str
    x: float
    y: float
    w: float
    h: float
    width: float
    height: float
    polygon: List[VastuJsonValue]
    outline: List[VastuJsonValue]
    area: float
    headingErrorDeg: float
    positionErrorM: float

class VastuRemediationReassessRequestPlanRoomsItem(_VastuRemediationReassessRequestPlanRoomsItemOptional):
    pass

class VastuRemediationReassessRequestPlanImportReview(TypedDict):
    northKnown: bool
    scaleKnown: bool
    analysisReady: bool
    coordinateFrame: Literal["north-up", "drawing-up"]
    units: Literal["m", "drawing-units"]

class _VastuRemediationReassessRequestPlanOptional(TypedDict, total=False):
    plot: Dict[str, VastuJsonValue]
    zoneResolution: Literal[8, 16, 32]
    headingErrorDeg: float
    positionErrorM: float
    importReview: VastuRemediationReassessRequestPlanImportReview
    merchantCatalogId: str

class VastuRemediationReassessRequestPlan(_VastuRemediationReassessRequestPlanOptional):
    rooms: List[VastuRemediationReassessRequestPlanRoomsItem]

class VastuRemediationReassessRequest(TypedDict):
    expectedRevision: int
    mutationId: str
    propertyId: str
    taskId: str
    plan: VastuRemediationReassessRequestPlan

class VastuMerchantCatalogUploadRequest(TypedDict):
    expectedRevision: int
    mutationId: str
    catalogId: str
    format: Literal["csv", "json"]
    content: VastuJsonValue

class VastuMerchantCatalogGetRequest(TypedDict):
    catalogId: str

class VastuMerchantCatalogDeleteRequest(TypedDict):
    id: str
    confirmId: str

class VastuMerchantRemediesRequest(TypedDict):
    catalogId: str
    remedyKeys: List[str]

class VastuRemediationTasksUpsertResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

class VastuRemediationTasksListResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

class VastuRemediationTasksDeleteResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

class VastuRemediationReassessResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

class VastuMerchantCatalogUploadResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

class VastuMerchantCatalogGetResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

class VastuMerchantCatalogDeleteResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

class VastuMerchantRemediesResponse(TypedDict):
    success: Literal[True]
    data: VastuWorkflowData
    billing: VastuWorkflowBilling
    replayed: bool

# BEGIN GENERATED VASTU RESPONSE DATA
class _VastuArAnchorRecommendationsDataAnchorsItemOptional(TypedDict, total=False):
    deityClassification: Literal["classical", "convention"]
    deitySource: str

class VastuArAnchorRecommendationsDataAnchorsItem(_VastuArAnchorRecommendationsDataAnchorsItemOptional):
    id: str
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]
    deity: str
    planPosition: List[float]
    worldPosition: List[float]
    normal: List[float]
    insidePlot: Literal[True]

class VastuArAttestationChallengeDataDeviceAttestation(TypedDict):
    status: Literal["challenge_issued", "not_configured"]
    platform: Literal["ios", "android"]

class _VastuArCaptureMergeDataPairResidualsItemOptional(TypedDict, total=False):
    controlCount: int

class VastuArCaptureMergeDataPairResidualsItem(_VastuArCaptureMergeDataPairResidualsItemOptional):
    rmsResidualM: float
    maxResidualM: float
    fromCaptureId: str
    toCaptureId: str

class VastuArCaptureMergeDataPricing(TypedDict):
    attributableCostUsd: str
    markupMultiplier: Literal[4]
    computedPriceUsd: str
    settledChargeUsd: str
    settlement: str

class _VastuArDeityIconsDataIconsItemOptional(TypedDict, total=False):
    deityClassification: Literal["classical", "convention"]
    deitySource: str

class VastuArDeityIconsDataIconsItem(_VastuArDeityIconsDataIconsItemOptional):
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]
    deity: str
    kind: Literal["typographic-nameplate"]
    png: VastuJsonValue
    svg: VastuJsonValue
    width: int
    height: int

class _VastuArHeatmapRasterDataZonesItemOptional(TypedDict, total=False):
    deityClassification: Literal["classical", "convention"]
    deitySource: str

class VastuArHeatmapRasterDataZonesItem(_VastuArHeatmapRasterDataZonesItemOptional):
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]
    deity: str
    disturbed: bool
    observed: bool
    roomCount: int

class VastuArHeatmapRasterDataCompleteness(TypedDict):
    status: Literal["partial", "computed_from_supplied_input"]
    computedComponents: List[str]
    missingInputs: List[str]
    projectedCellCount: int
    physicalCoverageVerified: Literal[False]
    note: str

class VastuArHeatmapRasterDataLegendDisturbed(TypedDict):
    color: str
    meaning: str

class VastuArHeatmapRasterDataLegendNeutral(TypedDict):
    color: str
    meaning: str

class VastuArHeatmapRasterDataLegend(TypedDict):
    disturbed: VastuArHeatmapRasterDataLegendDisturbed
    neutral: VastuArHeatmapRasterDataLegendNeutral
    observed: str

class _VastuArRoomCaptureDataCaptureOutlineGeometryOptional(TypedDict, total=False):
    polygon: VastuJsonValue
    holes: List[VastuJsonValue]
    multipolygons: List[VastuJsonValue]

class VastuArRoomCaptureDataCaptureOutlineGeometry(_VastuArRoomCaptureDataCaptureOutlineGeometryOptional):
    pass

class _VastuArRoomCaptureDataCaptureOutlineOptional(TypedDict, total=False):
    geometry: VastuArRoomCaptureDataCaptureOutlineGeometry

class VastuArRoomCaptureDataCaptureOutline(_VastuArRoomCaptureDataCaptureOutlineOptional):
    polygon: List[List[float]]
    source: Literal["traced"]
    width: float
    length: float
    areaM2: float

class _VastuArRoomCaptureDataCaptureOptional(TypedDict, total=False):
    units: Literal["m"]
    inputUnits: Literal["m", "ft", "mm", "in", "metres"]

class VastuArRoomCaptureDataCapture(_VastuArRoomCaptureDataCaptureOptional):
    captureId: str
    capturedAtEpoch: int
    device: Dict[str, VastuJsonValue]
    north: Dict[str, VastuJsonValue]
    floorIndex: int
    outline: VastuArRoomCaptureDataCaptureOutline
    originShiftM: List[float]
    roomCount: int
    openingCount: int

class _VastuArRoomCaptureDataRoomsItemGeometryOptional(TypedDict, total=False):
    polygon: VastuJsonValue
    holes: List[VastuJsonValue]
    multipolygons: List[VastuJsonValue]

class VastuArRoomCaptureDataRoomsItemGeometry(_VastuArRoomCaptureDataRoomsItemGeometryOptional):
    pass

class _VastuArRoomCaptureDataRoomsItemOptional(TypedDict, total=False):
    geometry: VastuArRoomCaptureDataRoomsItemGeometry

class VastuArRoomCaptureDataRoomsItem(_VastuArRoomCaptureDataRoomsItemOptional):
    id: str
    label: Optional[str]
    roomType: Optional[str]
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]
    zoneBasis: str
    areaM2: float
    centroid: List[float]
    heightM: Optional[float]
    openingCount: int
    polygon: List[List[float]]

class VastuArRoomCaptureDataDerivedRequests(TypedDict):
    planAnalyze: VastuJsonValue
    auditFloorPlanDetailed: VastuJsonValue
    scanQuality: VastuJsonValue
    anchorRecommendations: Optional[VastuJsonValue]

class VastuArRoomCaptureDataCompleteness(TypedDict):
    acceptForAudit: bool
    labelledRooms: int
    unlabelledRooms: List[str]
    missing: List[str]
    warnings: List[str]

class VastuArScanQualityDataRoomCoverage(TypedDict):
    expectedRoomCount: Optional[int]
    percent: Optional[float]
    status: Literal["complete", "partial", "invalid", "unknown"]
    scope: Literal["caller-declared-room-set"]

class VastuArScanQualityDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class VastuArTrueNorthDataHeadingQuality(TypedDict):
    accuracyDeg: Optional[float]
    sampleAgeMs: Optional[float]
    maxAccuracyDeg: float
    maxSampleAgeMs: Literal[4000]
    reliable: bool
    basis: str

class VastuArYantraMeshesDataGeometry(TypedDict):
    vertices: int
    triangles: int
    upAxis: str
    northAxis: str
    eastAxis: str
    units: Literal["metres"]

class VastuArZoneTexturesDataCellsItem(TypedDict):
    contentInsetPixels: int
    devata: str
    gltfUvBoundsTopLeft: List[float]
    maskBit: int
    pixelBoundsExclusive: List[int]
    usdUvBoundsBottomLeft: List[float]
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]

class _VastuArchiveDeleteDataErasureReceiptRemovedItemOptional(TypedDict, total=False):
    recordId: str
    artifactId: str
    artifactHash: str
    versionHash: str
    deleteMarker: bool
    versionCount: int
    deleteMarkerCount: int
    versionsSha256: str

class VastuArchiveDeleteDataErasureReceiptRemovedItem(_VastuArchiveDeleteDataErasureReceiptRemovedItemOptional):
    kind: str

class VastuArchiveDeleteDataErasureReceiptRetainedItem(TypedDict):
    kind: str
    purpose: str

class _VastuArchiveDeleteDataErasureReceiptOptional(TypedDict, total=False):
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    revisionId: str

class VastuArchiveDeleteDataErasureReceipt(_VastuArchiveDeleteDataErasureReceiptOptional):
    schemaVersion: Literal[1]
    propertyId: str
    status: Literal["completed"]
    scope: Literal["active-property-storage"]
    completedAt: str
    removed: List[VastuArchiveDeleteDataErasureReceiptRemovedItem]
    retained: List[VastuArchiveDeleteDataErasureReceiptRetainedItem]
    backupRetentionDays: int
    backupPolicy: str
    hashAlgorithm: Literal["SHA-256"]
    receiptHash: str
    deletedByAccountHash: str
    deletedAtEpoch: int

class VastuArchiveSummaryDataArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class VastuArchiveTierDataIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuArchiveTierDataArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class _VastuAssessmentBatchDataResultsItemResponseDataBadgeEligibilityOptional(TypedDict, total=False):
    confidence: float
    fullBadgeThreshold: float
    minimumConfidence: float

class VastuAssessmentBatchDataResultsItemResponseDataBadgeEligibility(_VastuAssessmentBatchDataResultsItemResponseDataBadgeEligibilityOptional):
    inputSource: Literal["seller-supplied", "plan-derived", "measured"]
    badge: Optional[Literal["plan-derived", "measured"]]
    eligible: bool
    variant: Optional[Literal["standard", "low_confidence"]]
    reason: str

class _VastuAssessmentBatchDataResultsItemResponseDataSourcesItemOptional(TypedDict, total=False):
    tradition: str

class VastuAssessmentBatchDataResultsItemResponseDataSourcesItem(_VastuAssessmentBatchDataResultsItemResponseDataSourcesItemOptional):
    source: str
    scope: str
    verified: bool
    classification: Literal["classical", "convention", "computed"]

class _VastuAssessmentBatchDataResultsItemResponseDataOptional(TypedDict, total=False):
    score: float
    findings: List[Dict[str, VastuJsonValue]]
    maxScore: float
    grade: Optional[str]
    gradeLabel: Optional[str]
    scoreBreakdown: Optional[Dict[str, VastuJsonValue]]
    entrance: Optional[Dict[str, VastuJsonValue]]
    scanQuality: Optional[Dict[str, VastuJsonValue]]
    zoneReference: Optional[Dict[str, VastuJsonValue]]
    sources: List[VastuAssessmentBatchDataResultsItemResponseDataSourcesItem]
    verified: bool
    tradition: str
    reason: str
    requiredConfidence: float
    missingData: List[str]
    reScanSuggestions: List[str]
    charged: bool
    listingId: VastuJsonValue

class VastuAssessmentBatchDataResultsItemResponseData(_VastuAssessmentBatchDataResultsItemResponseDataOptional):
    system: Literal["vastu"]
    method: Literal["listing-assessment"]
    status: Literal["assessed", "insufficient_data"]
    confidence: float
    badgeEligibility: VastuAssessmentBatchDataResultsItemResponseDataBadgeEligibility
    confidenceBasis: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]

class VastuAssessmentBatchDataResultsItemResponseBilling(TypedDict):
    charged: float
    currency: str
    balanceBefore: float
    balanceAfter: float
    endpoint: str
    category: str

class _VastuAssessmentBatchDataResultsItemResponseMetaOptional(TypedDict, total=False):
    source: str
    dataSource: Literal["vedika-ephemeris"]

class VastuAssessmentBatchDataResultsItemResponseMeta(_VastuAssessmentBatchDataResultsItemResponseMetaOptional):
    engine: Literal["vedika-intelligence"]
    version: str

class _VastuAssessmentBatchDataResultsItemResponseOptional(TypedDict, total=False):
    data: VastuAssessmentBatchDataResultsItemResponseData
    error: str
    code: str
    billing: VastuAssessmentBatchDataResultsItemResponseBilling
    meta: VastuAssessmentBatchDataResultsItemResponseMeta

class VastuAssessmentBatchDataResultsItemResponse(_VastuAssessmentBatchDataResultsItemResponseOptional):
    success: bool

class VastuAssessmentBatchDataResultsItem(TypedDict):
    id: str
    status: int
    response: VastuAssessmentBatchDataResultsItemResponse

class VastuAssessmentBatchDataSummary(TypedDict):
    total: int
    succeeded: int
    failed: int

class _VastuAssessmentBadgeEligibilityOptional(TypedDict, total=False):
    confidence: float
    fullBadgeThreshold: float
    minimumConfidence: float

class VastuAssessmentBadgeEligibility(_VastuAssessmentBadgeEligibilityOptional):
    inputSource: Literal["seller-supplied", "plan-derived", "measured"]
    badge: Optional[Literal["plan-derived", "measured"]]
    eligible: bool
    variant: Optional[Literal["standard", "low_confidence"]]
    reason: str

class _VastuAssessmentDataFindingsItemOptional(TypedDict, total=False):
    code: str
    room: Optional[str]
    zone: Optional[str]
    severity: Optional[str]
    detail: Optional[str]
    recommendedZone: Optional[str]
    remedy: Optional[str]
    remedyType: Optional[str]
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    zoneReference: Optional[Dict[str, VastuJsonValue]]
    pada: Optional[Dict[str, VastuJsonValue]]
    missingData: List[VastuJsonValue]
    reScanSuggestions: List[VastuJsonValue]
    classification: str
    verified: bool
    computed: bool
    source: str

class VastuAssessmentDataFindingsItem(_VastuAssessmentDataFindingsItemOptional):
    pass

class _VastuAssessmentDataSourcesItemOptional(TypedDict, total=False):
    tradition: str

class VastuAssessmentDataSourcesItem(_VastuAssessmentDataSourcesItemOptional):
    source: str
    scope: str
    verified: bool
    classification: Literal["classical", "convention", "computed"]

class VastuAssessmentDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuAssessmentDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class _VastuBrahmasthanProjectionDataGridFrameOptional(TypedDict, total=False):
    orientation: Literal["north-aligned"]
    fittedTo: Literal["plot-bounding-box"]
    rotationDeg: float
    gridBoxArea: float
    plotAreaShareOfGridBox: Optional[float]
    note: str

class VastuBrahmasthanProjectionDataGridFrame(_VastuBrahmasthanProjectionDataGridFrameOptional):
    pass

class _VastuCatalogReferenceDataDefectsItemOptional(TypedDict, total=False):
    labelKey: str
    labelParams: Dict[str, VastuJsonValue]
    code: str
    label: str
    severity: str
    source: str
    classification: str
    verified: bool

class VastuCatalogReferenceDataDefectsItem(_VastuCatalogReferenceDataDefectsItemOptional):
    pass

class _VastuCatalogReferenceDataRemediesItemOptional(TypedDict, total=False):
    remedyKey: str
    remedyParams: Dict[str, VastuJsonValue]
    defectCode: str
    remedy: str
    classification: str
    source: str

class VastuCatalogReferenceDataRemediesItem(_VastuCatalogReferenceDataRemediesItemOptional):
    pass

class _VastuCatalogReferenceDataZoneRemediesItemOptional(TypedDict, total=False):
    zone: str
    remedy: str
    remedyKey: str
    remedyParams: Dict[str, VastuJsonValue]
    classification: str
    source: str

class VastuCatalogReferenceDataZoneRemediesItem(_VastuCatalogReferenceDataZoneRemediesItemOptional):
    pass

class _VastuChatUploadDataBillingOptional(TypedDict, total=False):
    chargedCents: int
    balanceAfterCents: Optional[int]
    currency: Literal["USD"]

class VastuChatUploadDataBilling(_VastuChatUploadDataBillingOptional):
    pass

class VastuCompareVersionsDataChangesItem(TypedDict):
    ruleId: str
    before: VastuJsonValue
    after: VastuJsonValue
    reason: str
    fromReason: Optional[Dict[str, VastuJsonValue]]
    toReason: Optional[Dict[str, VastuJsonValue]]

class _VastuComplianceIndexDataDrivingDefectsItemOptional(TypedDict, total=False):
    room: str
    zone: str
    severity: str
    weight: int
    pointsLost: float
    issue: str
    recommendedZone: Optional[str]
    remedy: Optional[str]
    remedyType: Optional[str]
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    source: str
    verified: bool
    computed: bool
    classification: str
    ruleProvenance: Dict[str, VastuJsonValue]
    tradition: str

class VastuComplianceIndexDataDrivingDefectsItem(_VastuComplianceIndexDataDrivingDefectsItemOptional):
    pass

class VastuComplianceIndexDataScoring(TypedDict):
    version: str
    unit: str
    formula: str
    basis: str
    comparisonBasis: str
    classification: str
    inputPlacementCount: int
    uniquePlacementCount: int
    duplicatePlacementCount: int
    verified: Literal[False]

class VastuComplianceIndexDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuComplianceIndexDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class VastuDetailedFloorPlanAuditDataDefectsItemIssueParams(TypedDict):
    roomType: str
    zone: str
    severity: str

class _VastuDetailedFloorPlanAuditDataDefectsItemOptional(TypedDict, total=False):
    issueKey: str
    issueParams: VastuDetailedFloorPlanAuditDataDefectsItemIssueParams
    remedyKey: Optional[str]
    remedyParams: Dict[str, VastuJsonValue]
    room: str
    zone: str
    issue: str
    remedy: str
    severity: str
    classification: str
    recommendedZone: Optional[str]
    source: Optional[str]
    code: Optional[str]
    remedyClassification: Optional[str]
    remedySource: Optional[str]

class VastuDetailedFloorPlanAuditDataDefectsItem(_VastuDetailedFloorPlanAuditDataDefectsItemOptional):
    pass

class _VastuDetailedFloorPlanAuditDataDevataHeatmapItemOptional(TypedDict, total=False):
    zone: str
    deity: str
    deityClassification: str
    deitySource: str
    devatas: List[Dict[str, VastuJsonValue]]
    disturbed: bool

class VastuDetailedFloorPlanAuditDataDevataHeatmapItem(_VastuDetailedFloorPlanAuditDataDevataHeatmapItemOptional):
    pass

class _VastuDetailedFloorPlanAuditDataRemediationOrderItemOptional(TypedDict, total=False):
    actionKey: Optional[str]
    actionParams: Dict[str, VastuJsonValue]
    room: str
    zone: str
    action: str
    severity: str
    source: Optional[str]
    code: Optional[str]
    step: int
    classification: str
    remedyClassification: Optional[str]
    remedySource: Optional[str]

class VastuDetailedFloorPlanAuditDataRemediationOrderItem(_VastuDetailedFloorPlanAuditDataRemediationOrderItemOptional):
    pass

class VastuDetailedFloorPlanAuditDataScoring(TypedDict):
    version: str
    unit: str
    formula: str
    basis: str
    comparisonBasis: str
    classification: str
    inputPlacementCount: int
    uniquePlacementCount: int
    duplicatePlacementCount: int
    verified: Literal[False]

class VastuDetailedFloorPlanAuditDataCompleteness(TypedDict):
    status: Literal["partial", "computed_from_supplied_input"]
    computedComponents: List[str]
    missingInputs: List[str]
    projectedCellCount: int
    physicalCoverageVerified: Literal[False]
    note: str

class VastuDetailedFloorPlanAuditDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuDetailedFloorPlanAuditDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class _VastuDirectionsReferenceDataDirectionsItemOptional(TypedDict, total=False):
    code: str
    sanskrit: str
    deity: str
    deityClassification: str
    deitySource: str
    element: str
    bearingStart: float
    bearingEnd: float
    verified: bool
    tradition: str
    source: str

class VastuDirectionsReferenceDataDirectionsItem(_VastuDirectionsReferenceDataDirectionsItemOptional):
    pass

class _VastuEntrancePadaDataPadaOptional(TypedDict, total=False):
    deityRosterName: Optional[str]
    deityNameClassification: Literal["classical", "convention"]
    deityNameSource: str
    deityPlacementClassification: Literal["classical", "convention"]
    deityPlacementSource: str

class VastuEntrancePadaDataPada(_VastuEntrancePadaDataPadaOptional):
    index: int
    deity: str
    quadrant: str
    subIndex: int
    bearingStart: float
    bearingEnd: float
    auspiciousness: str
    source: str

class VastuFloorPlanAuditDataDefectsItemIssueParams(TypedDict):
    roomType: str
    zone: str
    severity: str

class _VastuFloorPlanAuditDataDefectsItemOptional(TypedDict, total=False):
    issueKey: str
    issueParams: VastuFloorPlanAuditDataDefectsItemIssueParams
    remedyKey: Optional[str]
    remedyParams: Dict[str, VastuJsonValue]
    room: str
    zone: str
    issue: str
    remedy: str
    severity: str
    classification: str
    recommendedZone: Optional[str]
    source: Optional[str]
    code: Optional[str]
    remedyClassification: Optional[str]
    remedySource: Optional[str]

class VastuFloorPlanAuditDataDefectsItem(_VastuFloorPlanAuditDataDefectsItemOptional):
    pass

class VastuFloorPlanAuditDataScoring(TypedDict):
    version: str
    unit: str
    formula: str
    basis: str
    comparisonBasis: str
    classification: str
    inputPlacementCount: int
    uniquePlacementCount: int
    duplicatePlacementCount: int
    verified: Literal[False]

class VastuFloorPlanAuditDataTextParse(TypedDict):
    version: str
    transliterations: str
    grammar: str
    coverage: str
    supportedLanguages: List[str]
    roomVocabulary: List[str]
    directionVocabulary: List[str]
    unparsedClauses: List[str]
    parsedClauseCount: int

class VastuFloorPlanAuditDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuFloorPlanAuditDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class _VastuFusionChartDataCautionDirectionsItemOptional(TypedDict, total=False):
    deity: str
    element: str
    ruledBy: str
    strengthPct: float
    avoidUse: List[str]

class VastuFusionChartDataCautionDirectionsItem(_VastuFusionChartDataCautionDirectionsItemOptional):
    direction: str
    rationale: str

class VastuJobStatusDataCounts(TypedDict):
    succeeded: int
    failed: int
    pending: int
    cancelled: int

class VastuJobStatusDataBilling(TypedDict):
    currency: Literal["USD"]
    pricePerItem: float
    maxCharge: float
    charged: float
    basis: str

class _VastuMandalaProjectionDataGridFrameOptional(TypedDict, total=False):
    orientation: Literal["north-aligned"]
    fittedTo: Literal["plot-bounding-box"]
    rotationDeg: float
    gridBoxArea: float
    plotAreaShareOfGridBox: Optional[float]
    note: str

class VastuMandalaProjectionDataGridFrame(_VastuMandalaProjectionDataGridFrameOptional):
    pass

class _VastuMandalaReferenceDataZonesItemOptional(TypedDict, total=False):
    remedyKey: str
    remedyParams: Dict[str, VastuJsonValue]
    zone: str
    deity: str
    element: str
    remedy: str
    source: str
    sourceClassification: str
    remedyClassification: str
    remedySource: str
    prescribed: List[str]
    forbidden: List[str]
    verseBackedRooms: List[str]
    verseBackedRoomsSource: str
    deityClassification: str
    deitySource: str
    elementClassification: str
    elementSource: str

class VastuMandalaReferenceDataZonesItem(_VastuMandalaReferenceDataZonesItemOptional):
    pass

class _VastuMandalaReferenceDataCellsItemOptional(TypedDict, total=False):
    id: str
    padaNumber: int
    row: int
    col: int
    zone: str
    isBrahmasthan: bool
    devata: Optional[str]
    source: str
    devataVerified: bool
    devataNameVerified: bool
    placementClassification: str
    placementSource: str
    polygon: List[List[float]]
    centroid: List[float]
    area: float
    insidePlot: bool

class VastuMandalaReferenceDataCellsItem(_VastuMandalaReferenceDataCellsItemOptional):
    pass

class _VastuMeasurementUncertaintyResultsItemOptional(TypedDict, total=False):
    id: VastuJsonValue
    headingErrorDeg: float
    positionErrorM: float
    method: str

class VastuMeasurementUncertaintyResultsItem(_VastuMeasurementUncertaintyResultsItemOptional):
    pointResult: Dict[str, VastuJsonValue]
    possibleZones: List[str]
    possiblePadas: List[Dict[str, VastuJsonValue]]
    stable: bool
    bearingMarginDeg: Optional[float]

class VastuMeasurementUncertaintyBounds(TypedDict):
    headingErrorDeg: float
    positionErrorM: float

class _VastuOverallScoreDataPlacementsItemOptional(TypedDict, total=False):
    room: str
    zone: str
    severity: str
    weight: int
    merit: float
    demerit: float
    compliant: bool
    recommendedZone: Optional[str]
    issue: str
    remedy: Optional[str]
    remedyType: Optional[str]
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    source: str
    verified: bool
    computed: bool
    classification: str
    ruleProvenance: Dict[str, VastuJsonValue]
    tradition: str

class VastuOverallScoreDataPlacementsItem(_VastuOverallScoreDataPlacementsItemOptional):
    pass

class VastuOverallScoreDataScoring(TypedDict):
    version: str
    unit: str
    formula: str
    basis: str
    comparisonBasis: str
    classification: str
    inputPlacementCount: int
    uniquePlacementCount: int
    duplicatePlacementCount: int
    verified: Literal[False]

class VastuOverallScoreDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuOverallScoreDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class _VastuPlanAuditDataRoomByRoomItemMappedItemsItemOptional(TypedDict, total=False):
    link: Optional[str]
    referralRef: Optional[str]

class VastuPlanAuditDataRoomByRoomItemMappedItemsItem(_VastuPlanAuditDataRoomByRoomItemMappedItemsItemOptional):
    remedyKey: str
    itemId: str
    kind: Literal["sku", "service"]
    label: str
    availability: Literal["in_stock", "out_of_stock", "on_request", "unavailable"]

class _VastuPlanAuditDataRoomByRoomItemOptional(TypedDict, total=False):
    room: str
    zone: str
    zoneSource: str
    ideal: Optional[str]
    verdict: str
    severity: str
    defect: Optional[str]
    remedy: Optional[str]
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    source: str
    verified: bool
    computed: bool
    classification: str
    ruleProvenance: Dict[str, VastuJsonValue]
    tradition: str
    statedZone: str
    zoneConflict: Literal[True]
    mappedItems: List[VastuPlanAuditDataRoomByRoomItemMappedItemsItem]

class VastuPlanAuditDataRoomByRoomItem(_VastuPlanAuditDataRoomByRoomItemOptional):
    pass

class _VastuPlanAuditDataDefectsItemMappedItemsItemOptional(TypedDict, total=False):
    link: Optional[str]
    referralRef: Optional[str]

class VastuPlanAuditDataDefectsItemMappedItemsItem(_VastuPlanAuditDataDefectsItemMappedItemsItemOptional):
    remedyKey: str
    itemId: str
    kind: Literal["sku", "service"]
    label: str
    availability: Literal["in_stock", "out_of_stock", "on_request", "unavailable"]

class _VastuPlanAuditDataDefectsItemOptional(TypedDict, total=False):
    room: str
    zone: str
    severity: str
    issue: str
    remedy: str
    source: str
    verified: bool
    tradition: str
    remedyType: str
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    mappedItems: List[VastuPlanAuditDataDefectsItemMappedItemsItem]

class VastuPlanAuditDataDefectsItem(_VastuPlanAuditDataDefectsItemOptional):
    pass

class _VastuPlanAuditDataRemediesItemMappedItemsItemOptional(TypedDict, total=False):
    link: Optional[str]
    referralRef: Optional[str]

class VastuPlanAuditDataRemediesItemMappedItemsItem(_VastuPlanAuditDataRemediesItemMappedItemsItemOptional):
    remedyKey: str
    itemId: str
    kind: Literal["sku", "service"]
    label: str
    availability: Literal["in_stock", "out_of_stock", "on_request", "unavailable"]

class _VastuPlanAuditDataRemediesItemOptional(TypedDict, total=False):
    priority: int
    room: str
    zone: str
    severity: str
    action: str
    source: str
    verified: bool
    tradition: str
    remedyType: str
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    remedyKey: Optional[str]
    remedyParams: Dict[str, VastuJsonValue]
    mappedItems: List[VastuPlanAuditDataRemediesItemMappedItemsItem]

class VastuPlanAuditDataRemediesItem(_VastuPlanAuditDataRemediesItemOptional):
    pass

class _VastuPlanAuditDataTracedGeometryRegionGeometryOptional(TypedDict, total=False):
    polygon: VastuJsonValue
    holes: List[VastuJsonValue]
    multipolygons: List[VastuJsonValue]

class VastuPlanAuditDataTracedGeometryRegionGeometry(_VastuPlanAuditDataTracedGeometryRegionGeometryOptional):
    pass

class _VastuPlanAuditDataTracedGeometryRegionBrahmasthanOptional(TypedDict, total=False):
    pole: List[float]
    poleInside: bool
    basis: str
    netArea: float

class VastuPlanAuditDataTracedGeometryRegionBrahmasthan(_VastuPlanAuditDataTracedGeometryRegionBrahmasthanOptional):
    pass

class _VastuPlanAuditDataTracedGeometryRegionGridZonesItemOptional(TypedDict, total=False):
    zone: str
    area: float

class VastuPlanAuditDataTracedGeometryRegionGridZonesItem(_VastuPlanAuditDataTracedGeometryRegionGridZonesItemOptional):
    pass

class _VastuPlanAuditDataTracedGeometryRegionSectorsItemOptional(TypedDict, total=False):
    zone: str
    area: float

class VastuPlanAuditDataTracedGeometryRegionSectorsItem(_VastuPlanAuditDataTracedGeometryRegionSectorsItemOptional):
    pass

class _VastuPlanAuditDataTracedGeometryRegionOptional(TypedDict, total=False):
    geometry: VastuPlanAuditDataTracedGeometryRegionGeometry
    area: float
    centroid: List[float]
    centroidInside: bool
    brahmasthan: VastuPlanAuditDataTracedGeometryRegionBrahmasthan
    gridZones: List[VastuPlanAuditDataTracedGeometryRegionGridZonesItem]
    sectors: List[VastuPlanAuditDataTracedGeometryRegionSectorsItem]

class VastuPlanAuditDataTracedGeometryRegion(_VastuPlanAuditDataTracedGeometryRegionOptional):
    pass

class _VastuPlanAuditDataTracedGeometryOptional(TypedDict, total=False):
    region: VastuPlanAuditDataTracedGeometryRegion

class VastuPlanAuditDataTracedGeometry(_VastuPlanAuditDataTracedGeometryOptional):
    pass

class _VastuPlanAuditDataArtifactOptional(TypedDict, total=False):
    encoding: Literal["base64"]

class VastuPlanAuditDataArtifact(_VastuPlanAuditDataArtifactOptional):
    contentType: Literal["text/html; charset=utf-8", "application/pdf"]
    filename: Literal["vastu-report.html", "vastu-report.pdf"]
    content: str

class VastuPlanAuditDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuPlanAuditDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class _VastuPlanGenerateDataPlotRegionGeometryOptional(TypedDict, total=False):
    polygon: VastuJsonValue
    holes: List[VastuJsonValue]
    multipolygons: List[VastuJsonValue]

class VastuPlanGenerateDataPlotRegionGeometry(_VastuPlanGenerateDataPlotRegionGeometryOptional):
    pass

class _VastuPlanGenerateDataPlotRegionBrahmasthanOptional(TypedDict, total=False):
    pole: List[float]
    poleInside: bool
    basis: str
    netArea: float

class VastuPlanGenerateDataPlotRegionBrahmasthan(_VastuPlanGenerateDataPlotRegionBrahmasthanOptional):
    pass

class _VastuPlanGenerateDataPlotRegionGridZonesItemOptional(TypedDict, total=False):
    zone: str
    area: float

class VastuPlanGenerateDataPlotRegionGridZonesItem(_VastuPlanGenerateDataPlotRegionGridZonesItemOptional):
    pass

class _VastuPlanGenerateDataPlotRegionSectorsItemOptional(TypedDict, total=False):
    zone: str
    area: float

class VastuPlanGenerateDataPlotRegionSectorsItem(_VastuPlanGenerateDataPlotRegionSectorsItemOptional):
    pass

class _VastuPlanGenerateDataPlotRegionOptional(TypedDict, total=False):
    geometry: VastuPlanGenerateDataPlotRegionGeometry
    area: float
    centroid: List[float]
    centroidInside: bool
    brahmasthan: VastuPlanGenerateDataPlotRegionBrahmasthan
    gridZones: List[VastuPlanGenerateDataPlotRegionGridZonesItem]
    sectors: List[VastuPlanGenerateDataPlotRegionSectorsItem]

class VastuPlanGenerateDataPlotRegion(_VastuPlanGenerateDataPlotRegionOptional):
    pass

class VastuPlanImportDataPlanPlot(TypedDict):
    polygon: List[List[float]]
    width: Optional[float]
    length: Optional[float]

class VastuPlanImportDataPlanRoomsItem(TypedDict):
    id: str
    name: str
    roomType: str
    label: str
    polygon: List[List[float]]

class VastuPlanImportDataPlanOpeningsItem(TypedDict):
    start: List[float]
    end: List[float]
    kind: Literal["door", "window", "opening"]

class VastuPlanImportDataPlanEntrance(TypedDict):
    start: List[float]
    end: List[float]
    kind: Literal["door", "window", "opening"]

class VastuPlanImportDataPlanImportReview(TypedDict):
    northKnown: bool
    scaleKnown: bool
    analysisReady: bool
    coordinateFrame: Literal["north-up", "drawing-up"]
    units: Literal["m", "drawing-units"]

class _VastuPlanImportDataPlanOptional(TypedDict, total=False):
    units: Literal["m", "drawing-units"]

class VastuPlanImportDataPlan(_VastuPlanImportDataPlanOptional):
    plot: VastuPlanImportDataPlanPlot
    rooms: List[VastuPlanImportDataPlanRoomsItem]
    openings: List[VastuPlanImportDataPlanOpeningsItem]
    entrance: Optional[VastuPlanImportDataPlanEntrance]
    importReview: VastuPlanImportDataPlanImportReview

class VastuPlanImportDataNorth(TypedDict):
    bearingDeg: Optional[float]
    confidence: float
    source: str

class VastuPlanImportDataScale(TypedDict):
    metersPerUnit: Optional[float]
    source: str

class VastuPlanImportDataDimensionsItem(TypedDict):
    text: str
    start: List[float]
    end: List[float]
    confidence: float

class VastuPlanImportDataNeedsReviewItem(TypedDict):
    field: str
    reason: str

class VastuPlanImportDataSourceDocument(TypedDict):
    page: int
    pageCount: int

class VastuPlanImportDataSource(TypedDict):
    method: Literal["vector", "ocr", "vision"]
    document: Optional[VastuPlanImportDataSourceDocument]

class VastuPlanImportDataUsage(TypedDict):
    inputTokens: int
    outputTokens: int
    computeMicros: int
    cpuMicros: int
    deliveryBytes: int

class VastuPlanImportDataPricing(TypedDict):
    currency: Literal["USD"]
    attributableCost: str
    modelCost: str
    computeCost: str
    markup: Literal[4]
    price: str
    unit: Literal["image", "selected-page"]
    walletRounding: str
    computedPrice: str
    deliveryCost: str

class _VastuPlanImportDxfDataPlanPlotOptional(TypedDict, total=False):
    polygon: List[List[float]]
    units: str

class VastuPlanImportDxfDataPlanPlot(_VastuPlanImportDxfDataPlanPlotOptional):
    width: float
    length: float

class _VastuPlanImportDxfDataPlanRoomsItemOptional(TypedDict, total=False):
    x: float
    y: float
    w: float
    h: float
    area: float
    centre: List[float]
    holes: List[List[List[float]]]
    source: Dict[str, VastuJsonValue]
    labelEntityId: str

class VastuPlanImportDxfDataPlanRoomsItem(_VastuPlanImportDxfDataPlanRoomsItemOptional):
    id: str
    name: str
    polygon: List[List[float]]

class _VastuPlanImportDxfDataPlanOpeningsDoorsItemOptional(TypedDict, total=False):
    centre: List[float]
    source: Dict[str, VastuJsonValue]

class VastuPlanImportDxfDataPlanOpeningsDoorsItem(_VastuPlanImportDxfDataPlanOpeningsDoorsItemOptional):
    id: str
    type: str
    line: List[List[float]]
    width: float

class _VastuPlanImportDxfDataPlanOpeningsWindowsItemOptional(TypedDict, total=False):
    centre: List[float]
    source: Dict[str, VastuJsonValue]

class VastuPlanImportDxfDataPlanOpeningsWindowsItem(_VastuPlanImportDxfDataPlanOpeningsWindowsItemOptional):
    id: str
    type: str
    line: List[List[float]]
    width: float

class _VastuPlanImportDxfDataPlanOpeningsOptional(TypedDict, total=False):
    doors: List[VastuPlanImportDxfDataPlanOpeningsDoorsItem]
    windows: List[VastuPlanImportDxfDataPlanOpeningsWindowsItem]
    units: str

class VastuPlanImportDxfDataPlanOpenings(_VastuPlanImportDxfDataPlanOpeningsOptional):
    pass

class _VastuPlanImportDxfDataPlanOptional(TypedDict, total=False):
    openings: VastuPlanImportDxfDataPlanOpenings
    orientationDeg: float
    cadMetadata: Dict[str, VastuJsonValue]

class VastuPlanImportDxfDataPlan(_VastuPlanImportDxfDataPlanOptional):
    plot: VastuPlanImportDxfDataPlanPlot
    rooms: List[VastuPlanImportDxfDataPlanRoomsItem]
    trueNorthDeg: float
    units: str

class _VastuPlanImportDxfDataMappingReportItemOptional(TypedDict, total=False):
    handle: Optional[str]
    stepId: int
    layer: str
    role: str
    planIds: List[str]
    reason: Optional[str]
    parentId: str

class VastuPlanImportDxfDataMappingReportItem(_VastuPlanImportDxfDataMappingReportItemOptional):
    entityId: str
    entityType: str
    status: str

class _VastuPlanImportDxfDataReviewReasonsItemOptional(TypedDict, total=False):
    id: str

class VastuPlanImportDxfDataReviewReasonsItem(_VastuPlanImportDxfDataReviewReasonsItemOptional):
    reason: str

class VastuPlanImportIfcDataBuildingsItem(TypedDict):
    id: str
    name: str

class _VastuPlanImportIfcDataStoreysItemPlanPlotOptional(TypedDict, total=False):
    polygon: List[List[float]]
    units: str

class VastuPlanImportIfcDataStoreysItemPlanPlot(_VastuPlanImportIfcDataStoreysItemPlanPlotOptional):
    width: float
    length: float

class _VastuPlanImportIfcDataStoreysItemPlanRoomsItemOptional(TypedDict, total=False):
    x: float
    y: float
    w: float
    h: float
    area: float
    centre: List[float]
    holes: List[List[List[float]]]
    source: Dict[str, VastuJsonValue]

class VastuPlanImportIfcDataStoreysItemPlanRoomsItem(_VastuPlanImportIfcDataStoreysItemPlanRoomsItemOptional):
    id: str
    name: str
    polygon: List[List[float]]

class _VastuPlanImportIfcDataStoreysItemPlanOpeningsDoorsItemOptional(TypedDict, total=False):
    centre: List[float]
    source: Dict[str, VastuJsonValue]
    name: str
    openingHeight: Optional[float]

class VastuPlanImportIfcDataStoreysItemPlanOpeningsDoorsItem(_VastuPlanImportIfcDataStoreysItemPlanOpeningsDoorsItemOptional):
    id: str
    type: str
    line: List[List[float]]
    width: float

class _VastuPlanImportIfcDataStoreysItemPlanOpeningsWindowsItemOptional(TypedDict, total=False):
    centre: List[float]
    source: Dict[str, VastuJsonValue]
    name: str
    openingHeight: Optional[float]

class VastuPlanImportIfcDataStoreysItemPlanOpeningsWindowsItem(_VastuPlanImportIfcDataStoreysItemPlanOpeningsWindowsItemOptional):
    id: str
    type: str
    line: List[List[float]]
    width: float

class _VastuPlanImportIfcDataStoreysItemPlanOpeningsOptional(TypedDict, total=False):
    doors: List[VastuPlanImportIfcDataStoreysItemPlanOpeningsDoorsItem]
    windows: List[VastuPlanImportIfcDataStoreysItemPlanOpeningsWindowsItem]
    units: str

class VastuPlanImportIfcDataStoreysItemPlanOpenings(_VastuPlanImportIfcDataStoreysItemPlanOpeningsOptional):
    pass

class _VastuPlanImportIfcDataStoreysItemPlanOptional(TypedDict, total=False):
    openings: VastuPlanImportIfcDataStoreysItemPlanOpenings
    orientationDeg: float
    cadMetadata: Dict[str, VastuJsonValue]

class VastuPlanImportIfcDataStoreysItemPlan(_VastuPlanImportIfcDataStoreysItemPlanOptional):
    plot: VastuPlanImportIfcDataStoreysItemPlanPlot
    rooms: List[VastuPlanImportIfcDataStoreysItemPlanRoomsItem]
    trueNorthDeg: float
    units: str

class VastuPlanImportIfcDataStoreysItem(TypedDict):
    id: str
    name: str
    buildingId: Optional[str]
    elevationMetres: Optional[float]
    plan: VastuPlanImportIfcDataStoreysItemPlan

class _VastuPlanImportIfcDataMappingReportItemOptional(TypedDict, total=False):
    handle: Optional[str]
    stepId: int
    layer: str
    role: str
    planIds: List[str]
    reason: Optional[str]
    storeyId: Optional[str]

class VastuPlanImportIfcDataMappingReportItem(_VastuPlanImportIfcDataMappingReportItemOptional):
    entityId: str
    entityType: str
    status: str

class _VastuPlanImportIfcDataReviewReasonsItemOptional(TypedDict, total=False):
    id: str

class VastuPlanImportIfcDataReviewReasonsItem(_VastuPlanImportIfcDataReviewReasonsItemOptional):
    reason: str

class _VastuPlanOptimizeDataPlotRegionGeometryOptional(TypedDict, total=False):
    polygon: VastuJsonValue
    holes: List[VastuJsonValue]
    multipolygons: List[VastuJsonValue]

class VastuPlanOptimizeDataPlotRegionGeometry(_VastuPlanOptimizeDataPlotRegionGeometryOptional):
    pass

class _VastuPlanOptimizeDataPlotRegionBrahmasthanOptional(TypedDict, total=False):
    pole: List[float]
    poleInside: bool
    basis: str
    netArea: float

class VastuPlanOptimizeDataPlotRegionBrahmasthan(_VastuPlanOptimizeDataPlotRegionBrahmasthanOptional):
    pass

class _VastuPlanOptimizeDataPlotRegionGridZonesItemOptional(TypedDict, total=False):
    zone: str
    area: float

class VastuPlanOptimizeDataPlotRegionGridZonesItem(_VastuPlanOptimizeDataPlotRegionGridZonesItemOptional):
    pass

class _VastuPlanOptimizeDataPlotRegionSectorsItemOptional(TypedDict, total=False):
    zone: str
    area: float

class VastuPlanOptimizeDataPlotRegionSectorsItem(_VastuPlanOptimizeDataPlotRegionSectorsItemOptional):
    pass

class _VastuPlanOptimizeDataPlotRegionOptional(TypedDict, total=False):
    geometry: VastuPlanOptimizeDataPlotRegionGeometry
    area: float
    centroid: List[float]
    centroidInside: bool
    brahmasthan: VastuPlanOptimizeDataPlotRegionBrahmasthan
    gridZones: List[VastuPlanOptimizeDataPlotRegionGridZonesItem]
    sectors: List[VastuPlanOptimizeDataPlotRegionSectorsItem]

class VastuPlanOptimizeDataPlotRegion(_VastuPlanOptimizeDataPlotRegionOptional):
    pass

class VastuPlotFromSurveyDataPricing(TypedDict):
    attributableCostUsd: str
    markupMultiplier: Literal[4]
    computedPriceUsd: str
    settledChargeUsd: str
    settlement: str

class VastuPortfolioAnalyticsDataAccountCounts(TypedDict):
    propertiesCreated: int
    propertiesAssessed: int
    reportsDelivered: int
    returningProperties: int

class VastuPortfolioAnalyticsDataAccountDailyItemCounts(TypedDict):
    propertiesCreated: int
    propertiesAssessed: int
    reportsDelivered: int
    returningProperties: int

class VastuPortfolioAnalyticsDataAccountDailyItem(TypedDict):
    date: str
    counts: VastuPortfolioAnalyticsDataAccountDailyItemCounts

class VastuPortfolioAnalyticsDataAccount(TypedDict):
    counts: VastuPortfolioAnalyticsDataAccountCounts
    daily: List[VastuPortfolioAnalyticsDataAccountDailyItem]
    returningDefinition: str
    deliveryDefinition: str
    coverage: str

class _VastuPortfolioBudgetsSetDataScopeOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuPortfolioBudgetsSetDataScope(_VastuPortfolioBudgetsSetDataScopeOptional):
    pass

class _VastuPortfolioCompareDataPropertiesItemAssessmentOptional(TypedDict, total=False):
    score: int
    grade: str
    inputSource: str
    ruleset: str
    zoneDefects: List[str]
    kind: Literal["assessed", "reportDelivered", "computed"]

class VastuPortfolioCompareDataPropertiesItemAssessment(_VastuPortfolioCompareDataPropertiesItemAssessmentOptional):
    pass

class VastuPortfolioCompareDataPropertiesItem(TypedDict):
    propertyId: str
    title: str
    city: str
    tags: List[str]
    createdAtEpoch: int
    assessment: Optional[VastuPortfolioCompareDataPropertiesItemAssessment]
    assessedAtEpoch: Optional[int]

class _VastuPortfolioSearchDataPropertiesItemAssessmentOptional(TypedDict, total=False):
    score: int
    grade: str
    inputSource: str
    ruleset: str
    zoneDefects: List[str]
    kind: Literal["assessed", "reportDelivered", "computed"]

class VastuPortfolioSearchDataPropertiesItemAssessment(_VastuPortfolioSearchDataPropertiesItemAssessmentOptional):
    pass

class VastuPortfolioSearchDataPropertiesItem(TypedDict):
    propertyId: str
    title: str
    city: str
    tags: List[str]
    createdAtEpoch: int
    assessment: Optional[VastuPortfolioSearchDataPropertiesItemAssessment]
    assessedAtEpoch: Optional[int]

class VastuPortfolioUsageDataGroupsItem(TypedDict):
    propertyId: Optional[str]
    tenantRef: Optional[str]
    calls: int
    chargedUsd: str
    pending: int

class VastuPropertiesActivityExportDataEventsItem(TypedDict):
    sequence: int
    actorId: str
    propertyId: str
    revision: str
    contentHash: str
    action: str
    at: int
    previousHash: str
    hash: str
    details: Dict[str, VastuJsonValue]

class VastuPropertiesActivityListDataEventsItem(TypedDict):
    sequence: int
    actorId: str
    propertyId: str
    revision: str
    contentHash: str
    action: str
    at: int
    previousHash: str
    hash: str
    details: Dict[str, VastuJsonValue]

class VastuPropertiesCollaborationCommentDataComment(TypedDict):
    id: str
    actorId: str
    assessmentId: str
    revision: str
    contentHash: str
    at: int
    text: str

class VastuPropertiesCollaborationGetDataPropertyIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuPropertiesCollaborationGetDataPropertyArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class VastuPropertiesCollaborationGetDataProperty(TypedDict):
    propertyId: str
    ownerId: str
    ids: VastuPropertiesCollaborationGetDataPropertyIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuPropertiesCollaborationGetDataPropertyArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str

class VastuPropertiesCollaborationGetDataCommentsItem(TypedDict):
    id: str
    actorId: str
    assessmentId: str
    revision: str
    contentHash: str
    at: int
    text: str

class VastuPropertiesCollaborationGetDataReviewsItem(TypedDict):
    actorId: str
    assessmentId: str
    revision: str
    contentHash: str
    at: int
    decision: Literal["approved", "rejected"]

class VastuPropertiesCollaborationReviewDataReview(TypedDict):
    actorId: str
    assessmentId: str
    revision: str
    contentHash: str
    at: int
    decision: Literal["approved", "rejected"]

class VastuPropertiesCollaborationUpdateDataPropertyIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuPropertiesCollaborationUpdateDataPropertyArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class VastuPropertiesCollaborationUpdateDataProperty(TypedDict):
    propertyId: str
    ownerId: str
    ids: VastuPropertiesCollaborationUpdateDataPropertyIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuPropertiesCollaborationUpdateDataPropertyArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str

class VastuPropertiesCreateDataIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuPropertiesCreateDataArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class _VastuPropertiesDeleteDataErasureReceiptRemovedItemOptional(TypedDict, total=False):
    recordId: str
    artifactId: str
    artifactHash: str
    versionHash: str
    deleteMarker: bool
    versionCount: int
    deleteMarkerCount: int
    versionsSha256: str

class VastuPropertiesDeleteDataErasureReceiptRemovedItem(_VastuPropertiesDeleteDataErasureReceiptRemovedItemOptional):
    kind: str

class VastuPropertiesDeleteDataErasureReceiptRetainedItem(TypedDict):
    kind: str
    purpose: str

class _VastuPropertiesDeleteDataErasureReceiptOptional(TypedDict, total=False):
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    revisionId: str

class VastuPropertiesDeleteDataErasureReceipt(_VastuPropertiesDeleteDataErasureReceiptOptional):
    schemaVersion: Literal[1]
    propertyId: str
    status: Literal["completed"]
    scope: Literal["active-property-storage"]
    completedAt: str
    removed: List[VastuPropertiesDeleteDataErasureReceiptRemovedItem]
    retained: List[VastuPropertiesDeleteDataErasureReceiptRetainedItem]
    backupRetentionDays: int
    backupPolicy: str
    hashAlgorithm: Literal["SHA-256"]
    receiptHash: str
    deletedByAccountHash: str
    deletedAtEpoch: int

class VastuPropertiesGetDataIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuPropertiesGetDataArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class VastuPropertiesLinkScanDataIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuPropertiesLinkScanDataArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class VastuPropertiesListDataPropertiesItemIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuPropertiesListDataPropertiesItemArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class VastuPropertiesListDataPropertiesItem(TypedDict):
    propertyId: str
    ownerId: str
    ids: VastuPropertiesListDataPropertiesItemIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuPropertiesListDataPropertiesItemArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str

class VastuPropertiesUpdateDataIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class VastuPropertiesUpdateDataArchiveTier(TypedDict):
    months: int
    storedBytes: int
    priceCents: int
    setAtEpoch: int
    retainUntilEpoch: int

class _VastuQuoteCalculateDataLineItemsItemOptional(TypedDict, total=False):
    slug: str
    label: str
    quantity: int
    baseCostUsd: str
    totalPriceUsd: str
    category: str

class VastuQuoteCalculateDataLineItemsItem(_VastuQuoteCalculateDataLineItemsItemOptional):
    pass

class VastuReceiptVerifyDataReceipt(TypedDict):
    assessmentId: str
    inputHash: str
    resultHash: str
    rulesVersion: str
    score: int
    grade: Optional[str]
    sourceLabels: List[str]
    timestamp: int

class _VastuRemediationTaskDataEvidenceItemOptional(TypedDict, total=False):
    photoRef: Optional[str]
    note: Optional[str]

class VastuRemediationTaskDataEvidenceItem(_VastuRemediationTaskDataEvidenceItemOptional):
    reference: str

class VastuRemediationTaskDataReassessmentLinkRequest(TypedDict):
    propertyId: str

class VastuRemediationTaskDataReassessmentLink(TypedDict):
    operation: str
    method: Literal["POST"]
    request: VastuRemediationTaskDataReassessmentLinkRequest
    resultPointer: str
    propertyId: str
    taskId: str
    assessmentId: str

class _VastuRemedyComparisonDataBeforeDefectsItemOptional(TypedDict, total=False):
    room: str
    zone: str
    issue: str
    severity: str
    remedy: str
    recommendedZone: Optional[str]
    source: str
    classification: str
    remedyClassification: Optional[str]
    remedySource: Optional[str]

class VastuRemedyComparisonDataBeforeDefectsItem(_VastuRemedyComparisonDataBeforeDefectsItemOptional):
    pass

class _VastuRemedyComparisonDataBeforeOptional(TypedDict, total=False):
    score: Optional[int]
    grade: Optional[str]
    defectCount: int
    prescribedCount: int
    defects: List[VastuRemedyComparisonDataBeforeDefectsItem]

class VastuRemedyComparisonDataBefore(_VastuRemedyComparisonDataBeforeOptional):
    pass

class _VastuRemedyComparisonDataAfterDefectsItemOptional(TypedDict, total=False):
    room: str
    zone: str
    issue: str
    severity: str
    remedy: str
    recommendedZone: Optional[str]
    source: str
    classification: str
    remedyClassification: Optional[str]
    remedySource: Optional[str]

class VastuRemedyComparisonDataAfterDefectsItem(_VastuRemedyComparisonDataAfterDefectsItemOptional):
    pass

class _VastuRemedyComparisonDataAfterOptional(TypedDict, total=False):
    score: Optional[int]
    grade: Optional[str]
    defectCount: int
    prescribedCount: int
    defects: List[VastuRemedyComparisonDataAfterDefectsItem]

class VastuRemedyComparisonDataAfter(_VastuRemedyComparisonDataAfterOptional):
    pass

class VastuRemedyComparisonDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class _VastuSpecializedAuditDataFindingsItemOptional(TypedDict, total=False):
    room: str
    zone: str
    function: str
    status: str
    severity: str
    idealZones: List[str]
    deity: str
    deityClassification: str
    deitySource: str
    element: str
    elementTradition: str
    waterEffect: Optional[Dict[str, VastuJsonValue]]
    note: str
    verified: bool
    computed: bool
    classification: str
    tradition: str
    source: str

class VastuSpecializedAuditDataFindingsItem(_VastuSpecializedAuditDataFindingsItemOptional):
    pass

class VastuSpecializedAuditDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuSpecializedAuditDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class VastuSunPathDataInput(TypedDict):
    lat: float
    lon: float
    date: str

class _VastuWorkflowDataDataItemsItemOptional(TypedDict, total=False):
    link: Optional[str]
    referralRef: Optional[str]

class VastuWorkflowDataDataItemsItem(_VastuWorkflowDataDataItemsItemOptional):
    remedyKey: str
    itemId: str
    kind: Literal["sku", "service"]
    label: str
    availability: Literal["in_stock", "out_of_stock", "on_request", "unavailable"]

class _VastuWorkflowDataDataOptional(TypedDict, total=False):
    propertyId: str
    catalogId: str
    tasks: Dict[str, "VastuRemediationTaskData"]
    items: List[VastuWorkflowDataDataItemsItem]

class VastuWorkflowDataData(_VastuWorkflowDataDataOptional):
    pass

class _VastuWorkflowDataRemediesItemMappedItemsItemOptional(TypedDict, total=False):
    link: Optional[str]
    referralRef: Optional[str]

class VastuWorkflowDataRemediesItemMappedItemsItem(_VastuWorkflowDataRemediesItemMappedItemsItemOptional):
    remedyKey: str
    itemId: str
    kind: Literal["sku", "service"]
    label: str
    availability: Literal["in_stock", "out_of_stock", "on_request", "unavailable"]

class _VastuWorkflowDataRemediesItemOptional(TypedDict, total=False):
    remedyKey: str
    remedy: str
    classification: str
    source: str
    mappedItems: List[VastuWorkflowDataRemediesItemMappedItemsItem]

class VastuWorkflowDataRemediesItem(_VastuWorkflowDataRemediesItemOptional):
    pass

class _VastuZoneWiseScoreDataZonesItemRoomsItemOptional(TypedDict, total=False):
    room: str
    severity: str
    compliant: bool
    issue: str
    remedy: Optional[str]
    remedyType: Optional[str]
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    recommendedZone: Optional[str]

class VastuZoneWiseScoreDataZonesItemRoomsItem(_VastuZoneWiseScoreDataZonesItemRoomsItemOptional):
    pass

class _VastuZoneWiseScoreDataZonesItemOptional(TypedDict, total=False):
    zone: str
    zoneWeight: int
    zoneImportance: str
    score: int
    grade: str
    worstSeverity: str
    rooms: List[VastuZoneWiseScoreDataZonesItemRoomsItem]
    source: str
    verified: bool
    tradition: str

class VastuZoneWiseScoreDataZonesItem(_VastuZoneWiseScoreDataZonesItemOptional):
    pass

class VastuZoneWiseScoreDataScoring(TypedDict):
    version: str
    unit: str
    formula: str
    basis: str
    comparisonBasis: str
    classification: str
    inputPlacementCount: int
    uniquePlacementCount: int
    duplicatePlacementCount: int
    verified: Literal[False]

class VastuZoneWiseScoreDataNotAssessedItem(TypedDict):
    room: str
    zone: str
    reason: Literal["no placement rule for this space type"]
    graded: Literal[False]

class VastuZoneWiseScoreDataReceipt(TypedDict):
    format: Literal["JWS"]
    token: str
    verifyUrl: str
    keyUrl: str

class _VastuArAnchorRecommendationsDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArAnchorRecommendationsData(_VastuArAnchorRecommendationsDataOptional):
    anchors: List[VastuArAnchorRecommendationsDataAnchorsItem]
    omittedZones: List[Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]]
    planToWorld: VastuJsonValue
    bearingDeg: float
    bearingAssumedNorth: Literal[False]
    physicalRegistrationVerified: Literal[False]
    physicalNorthVerified: Literal[False]
    sources: List[str]
    verified: Literal[False]
    provenance: VastuJsonValue
    computed: Literal[True]
    physicalCoverageVerified: Literal[False]
    coordinateNote: str
    omissionNote: str

class _VastuArAttestationChallengeDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArAttestationChallengeData(_VastuArAttestationChallengeDataOptional):
    challenge: Optional[str]
    expiresAtEpoch: Optional[int]
    ttlSeconds: Optional[Literal[300]]
    singleUse: Literal[True]
    deviceAttestation: VastuArAttestationChallengeDataDeviceAttestation

class _VastuArCaptureMergeDataOptional(TypedDict, total=False):
    pricing: VastuArCaptureMergeDataPricing
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArCaptureMergeData(_VastuArCaptureMergeDataOptional):
    method: Literal["capture-merge"]
    frame: Dict[str, VastuJsonValue]
    rooms: List[Dict[str, VastuJsonValue]]
    outlines: List[Dict[str, VastuJsonValue]]
    registrations: List[Dict[str, VastuJsonValue]]
    pairResiduals: List[VastuArCaptureMergeDataPairResidualsItem]
    unresolvedAlignmentErrors: List[str]
    floorStack: List[Dict[str, VastuJsonValue]]
    toleranceM: float
    alignmentMethod: str

class _VastuArDeityIconsDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArDeityIconsData(_VastuArDeityIconsDataOptional):
    icons: List[VastuArDeityIconsDataIconsItem]
    verified: Literal[False]
    provenance: VastuJsonValue

class _VastuArHeatmapRasterDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArHeatmapRasterData(_VastuArHeatmapRasterDataOptional):
    mask: int
    texture: VastuJsonValue
    maskBitOrder: List[Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]]
    zones: List[VastuArHeatmapRasterDataZonesItem]
    observedZones: List[Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]]
    unobservedZones: List[Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]]
    mandalaProjection: Optional[Dict[str, VastuJsonValue]]
    bearingAssumedNorth: bool
    completeness: VastuArHeatmapRasterDataCompleteness
    sources: List[str]
    physicalCoverageVerified: Literal[False]
    verified: Literal[False]
    provenance: VastuJsonValue
    legend: VastuArHeatmapRasterDataLegend
    computed: Literal[True]

class _VastuArRoomCaptureDataOptional(TypedDict, total=False):
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArRoomCaptureData(_VastuArRoomCaptureDataOptional):
    method: Literal["room-capture"]
    schema: Literal["vedika.roomCapture/1"]
    capture: VastuArRoomCaptureDataCapture
    rooms: List[VastuArRoomCaptureDataRoomsItem]
    derivedRequests: VastuArRoomCaptureDataDerivedRequests
    planAnalysis: VastuJsonValue
    audit: VastuJsonValue
    scanQuality: VastuJsonValue
    anchorRecommendations: Optional[VastuJsonValue]
    completeness: VastuArRoomCaptureDataCompleteness
    sources: List[str]
    verified: Literal[False]
    captureVerification: Literal["unverified-caller-input"]
    attestation: Literal["caller-reported"]
    note: str
    deviceAttestation: VastuJsonValue

class _VastuArScanQualityDataOptional(TypedDict, total=False):
    deviceAttestation: VastuJsonValue
    deviceAttested: Literal[True]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuArScanQualityDataReceipt

class VastuArScanQualityData(_VastuArScanQualityDataOptional):
    grade: Optional[Literal["A", "B", "C", "D", "F"]]
    score: Optional[int]
    missingData: List[str]
    warnings: List[str]
    reScanSuggestions: List[str]
    dimensions: VastuArScanDimensions
    acceptForAudit: bool
    sources: List[str]
    verified: bool
    roomsTaggedCount: Optional[float]
    unreportedDimensions: List[str]
    roomCount: Optional[int]
    roomCoverage: VastuArScanQualityDataRoomCoverage
    scoreScope: Literal["reported-scan-telemetry"]
    evidenceSource: Literal["caller-reported"]
    sensorAttestation: Literal[False]
    limitations: str

class _VastuArTrueNorthDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArTrueNorthData(_VastuArTrueNorthDataOptional):
    input: VastuArTrueNorthResultInput
    sunAzimuthTrueDeg: float
    solarElevationDeg: float
    offsetDeg: float
    headingCorrection: str
    reliable: bool
    reason: str
    sources: List[str]
    verified: bool
    solarGeometryReliable: bool
    headingQuality: VastuArTrueNorthDataHeadingQuality

class _VastuArYantraMeshesDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArYantraMeshesData(_VastuArYantraMeshesDataOptional):
    name: str
    format: Literal["gltf", "usdz"]
    asset: VastuJsonValue
    dimensionsMetres: List[float]
    geometry: VastuArYantraMeshesDataGeometry
    ritualDesign: Literal[False]
    remedyEfficacyClaimed: Literal[False]
    verified: Literal[False]
    provenance: VastuJsonValue
    assetId: Literal["nine-zone-mandala"]

class _VastuArZoneTexturesDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArZoneTexturesData(_VastuArZoneTexturesDataOptional):
    png: VastuJsonValue
    svg: VastuJsonValue
    width: int
    height: int
    cells: List[VastuArZoneTexturesDataCellsItem]
    verified: Literal[False]
    provenance: VastuJsonValue
    pixelBoundsConvention: str
    gltfUvOrigin: str
    usdUvOrigin: str

class _VastuArchiveDeleteDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    erasureStatus: Literal["pending", "completed"]
    erasureReceipt: VastuArchiveDeleteDataErasureReceipt
    retryAfterEpoch: int
    revisionId: str
    replayed: bool

class VastuArchiveDeleteData(_VastuArchiveDeleteDataOptional):
    propertyId: str
    deleted: bool
    exportDeleted: bool
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]

class _VastuArchiveExportDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArchiveExportData(_VastuArchiveExportDataOptional):
    propertyId: str
    downloadUrl: str
    expiresInSeconds: Literal[3600]
    expiresAtEpoch: int
    sizeBytes: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]

class _VastuArchiveSummaryDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArchiveSummaryData(_VastuArchiveSummaryDataOptional):
    propertyId: str
    archiveTier: Optional[VastuArchiveSummaryDataArchiveTier]
    linkedScanCount: int
    linkedAssessmentCount: int
    expiresAtEpoch: int

class _VastuArchiveTierDataOptional(TypedDict, total=False):
    ownerId: str
    ids: VastuArchiveTierDataIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuArchiveTierDataArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str
    months: int
    storedBytes: int
    meterCents: int
    actionCents: int
    totalCents: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuArchiveTierData(_VastuArchiveTierDataOptional):
    propertyId: str

class _VastuAssessmentBatchDataOptional(TypedDict, total=False):
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuAssessmentBatchData(_VastuAssessmentBatchDataOptional):
    results: List[VastuAssessmentBatchDataResultsItem]
    summary: VastuAssessmentBatchDataSummary
    billingBasis: str
    execution: Literal["synchronous"]

class _VastuAssessmentDataOptional(TypedDict, total=False):
    score: float
    findings: List[VastuAssessmentDataFindingsItem]
    maxScore: float
    grade: Optional[str]
    gradeLabel: Optional[str]
    scoreBreakdown: Optional[Dict[str, VastuJsonValue]]
    entrance: Optional[Dict[str, VastuJsonValue]]
    scanQuality: Optional[Dict[str, VastuJsonValue]]
    zoneReference: Optional[Dict[str, VastuJsonValue]]
    sources: List[VastuAssessmentDataSourcesItem]
    verified: bool
    tradition: str
    reason: str
    requiredConfidence: float
    missingData: List[str]
    reScanSuggestions: List[str]
    charged: bool
    listingId: VastuJsonValue
    notAssessed: List[VastuAssessmentDataNotAssessedItem]
    warnings: List[Dict[str, VastuJsonValue]]
    zoneCheck: Dict[str, VastuJsonValue]
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuAssessmentDataReceipt

class VastuAssessmentData(_VastuAssessmentDataOptional):
    system: Literal["vastu"]
    method: Literal["listing-assessment"]
    status: Literal["assessed", "insufficient_data"]
    confidence: float
    badgeEligibility: VastuAssessmentBadgeEligibility
    confidenceBasis: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]

class _VastuAuspiciousFacingDataOptional(TypedDict, total=False):
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    rationale: str
    system: str
    tradition: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuAuspiciousFacingData(_VastuAuspiciousFacingDataOptional):
    purpose: str
    bestFacing: List[Dict[str, VastuJsonValue]]
    bestZone: List[Dict[str, VastuJsonValue]]
    avoidFacing: List[Dict[str, VastuJsonValue]]
    verifiedPlacement: Optional[Dict[str, VastuJsonValue]]
    zoneComplianceCheck: List[Dict[str, VastuJsonValue]]
    verified: bool

class _VastuBearingZoneDataOptional(TypedDict, total=False):
    deityClassification: str
    deitySource: str
    elementClassification: str
    elementSource: str
    verseBackedRooms: List[str]
    roomRulesClassification: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuBearingZoneData(_VastuBearingZoneDataOptional):
    bearingDeg: float
    zone: str
    deity: str
    element: str
    prescribedRooms: List[str]
    forbiddenRooms: List[str]
    sources: List[str]
    verified: bool

class _VastuBrahmasthanProjectionDataOptional(TypedDict, total=False):
    bearingAssumedNorth: bool
    forbiddenActionsClassification: str
    forbiddenActionsSource: str
    classicalSourceScope: str
    centroidBasis: Literal["plot-area-centroid"]
    centerPolygonCentre: List[float]
    centreBasis: Literal["bounding-box-centre"]
    centreOffset: float
    centreNote: str
    gridFrame: VastuBrahmasthanProjectionDataGridFrame
    inPlotArea: float
    inPlotFraction: float
    shareOfPlotArea: Optional[float]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuBrahmasthanProjectionData(_VastuBrahmasthanProjectionDataOptional):
    centerPolygon: List[List[float]]
    bufferPolygon: List[List[float]]
    centroid: List[float]
    area: float
    forbiddenActions: List[str]
    classicalSource: str
    sources: List[str]
    verified: bool
    computed: bool
    classification: str

class _VastuCatalogReferenceDataOptional(TypedDict, total=False):
    defectCount: int
    defects: List[VastuCatalogReferenceDataDefectsItem]
    remedyCount: int
    remedies: List[VastuCatalogReferenceDataRemediesItem]
    featureCount: int
    features: List[Dict[str, VastuJsonValue]]
    rangeClassification: Literal["convention"]
    rangeSource: str
    sources: List[str]
    note: str
    meta: Dict[str, VastuJsonValue]
    zoneRemedies: List[VastuCatalogReferenceDataZoneRemediesItem]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuCatalogReferenceData(_VastuCatalogReferenceDataOptional):
    verified: bool
    referenceVersion: str

class _VastuChatUploadDataOptional(TypedDict, total=False):
    pagesSkipped: int
    textTruncated: bool
    replayed: bool
    billing: VastuChatUploadDataBilling
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuChatUploadData(_VastuChatUploadDataOptional):
    success: Literal[True]
    uploadId: str
    pages: int
    charsExtracted: int
    expiresAt: str
    digestSha256: str
    fileSha256: str

class _VastuCompareVersionsDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuCompareVersionsData(_VastuCompareVersionsDataOptional):
    inputHash: str
    operation: str
    fromVersion: str
    toVersion: str
    fromAssessment: Dict[str, VastuJsonValue]
    toAssessment: Dict[str, VastuJsonValue]
    changed: bool
    changes: List[VastuCompareVersionsDataChangesItem]
    retainedVersions: Literal[2]
    scope: str

class _VastuComplianceIndexDataOptional(TypedDict, total=False):
    basis: str
    defectsSummary: Dict[str, VastuJsonValue]
    indexLabel: Optional[str]
    indexScale: List[Dict[str, VastuJsonValue]]
    indexScaleNote: str
    indexType: str
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    system: str
    tradition: str
    verdict: Optional[str]
    notAssessed: List[VastuComplianceIndexDataNotAssessedItem]
    scoreNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuComplianceIndexDataReceipt

class VastuComplianceIndexData(_VastuComplianceIndexDataOptional):
    score: Optional[float]
    complianceIndex: Optional[str]
    drivingDefects: List[VastuComplianceIndexDataDrivingDefectsItem]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool
    scoring: VastuComplianceIndexDataScoring

class _VastuDetailedFloorPlanAuditDataOptional(TypedDict, total=False):
    bearingAssumedNorth: bool
    gradeScale: Dict[str, VastuJsonValue]
    notAssessed: List[VastuDetailedFloorPlanAuditDataNotAssessedItem]
    scoreNote: str
    merchantCatalogId: str
    merchantCatalogRevision: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuDetailedFloorPlanAuditDataReceipt

class VastuDetailedFloorPlanAuditData(_VastuDetailedFloorPlanAuditDataOptional):
    score: Optional[float]
    grade: Optional[str]
    totalRooms: int
    prescribedCount: int
    defects: List[VastuDetailedFloorPlanAuditDataDefectsItem]
    devataHeatmap: List[VastuDetailedFloorPlanAuditDataDevataHeatmapItem]
    mandalaProjection: Optional[Dict[str, VastuJsonValue]]
    remediationOrder: List[VastuDetailedFloorPlanAuditDataRemediationOrderItem]
    sources: List[str]
    verified: bool
    computed: bool
    classification: str
    scoring: VastuDetailedFloorPlanAuditDataScoring
    completeness: VastuDetailedFloorPlanAuditDataCompleteness

class _VastuDirectionCorrectDataOptional(TypedDict, total=False):
    correctedZoneIsMagnetic: bool
    declinationCoverage: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuDirectionCorrectData(_VastuDirectionCorrectDataOptional):
    input: Dict[str, VastuJsonValue]
    magneticBearingDeg: Optional[float]
    declinationDeg: Optional[float]
    trueBearingDeg: Optional[float]
    correctedZone: str
    sources: List[str]
    verified: bool

class _VastuDirectionDeclinationDataOptional(TypedDict, total=False):
    declinationCoverage: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuDirectionDeclinationData(_VastuDirectionDeclinationDataOptional):
    lat: float
    lon: float
    date: str
    declinationDeg: Optional[float]
    interpretation: str
    gridEpoch: str
    sources: List[str]
    verified: bool
    computed: bool
    classification: str

class _VastuDirections32ReferenceDataOptional(TypedDict, total=False):
    system: str
    method: str
    padaWidthDeg: float
    auspiciousCount: int
    avoidCount: int
    classicalDoorScheme: Dict[str, VastuJsonValue]
    note: str
    tradition: str
    meta: Dict[str, VastuJsonValue]
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuDirections32ReferenceData(_VastuDirections32ReferenceDataOptional):
    padaCount: int
    padas: List[Dict[str, VastuJsonValue]]
    verified: bool
    referenceVersion: str

class _VastuDirectionsReferenceDataOptional(TypedDict, total=False):
    note: str
    sources: List[str]
    system: str
    method: str
    sectorWidthDeg: float
    meta: Dict[str, VastuJsonValue]
    tradition: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuDirectionsReferenceData(_VastuDirectionsReferenceDataOptional):
    directionCount: int
    directions: List[VastuDirectionsReferenceDataDirectionsItem]
    verified: bool
    referenceVersion: str

class _VastuDrawingSheetDataOptional(TypedDict, total=False):
    contentType: str
    pdfBase64: str

class VastuDrawingSheetData(_VastuDrawingSheetDataOptional):
    html: str
    svg: str
    paperSize: Literal["A3", "A2"]
    paperWidthMm: float
    paperHeightMm: float
    scaleDenominator: int
    metresToPaperMm: float
    planWidthMm: float
    planHeightMm: float
    trueNorthDeg: float
    fieldEvidenceCount: int
    inputUnits: Literal["m", "ft", "mm", "in"]
    units: Literal["m"]
    metresPerInputUnit: float

class _VastuElementBalanceDataOptional(TypedDict, total=False):
    meta: Dict[str, VastuJsonValue]
    method: str
    summary: str
    system: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuElementBalanceData(_VastuElementBalanceDataOptional):
    derivedFrom: str
    deficientElements: List[str]
    excessElements: List[str]
    remedies: List[Dict[str, VastuJsonValue]]
    balanced: bool

class _VastuElementDistributionDataOptional(TypedDict, total=False):
    meta: Dict[str, VastuJsonValue]
    method: str
    system: str
    totalRooms: float
    weightingBasis: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuElementDistributionData(_VastuElementDistributionDataOptional):
    elementDistribution: List[Dict[str, VastuJsonValue]]
    idealModel: Dict[str, VastuJsonValue]
    dominantElement: str
    deficientElements: List[str]
    excessElements: List[str]
    zoneBreakdown: List[Dict[str, VastuJsonValue]]

class _VastuEntrancePadaDataOptional(TypedDict, total=False):
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuEntrancePadaData(_VastuEntrancePadaDataOptional):
    doorXY: List[float]
    plotCentroid: List[float]
    rawBearingDeg: float
    trueBearingDeg: float
    pada: VastuEntrancePadaDataPada
    edgeRefined: bool
    sources: List[str]
    verified: bool

class _VastuEntranceRecommendDataOptional(TypedDict, total=False):
    bestEntranceIsUnfavourable: bool
    bestEntranceNote: Optional[str]
    facingCaution: Optional[Dict[str, VastuJsonValue]]
    meta: Dict[str, VastuJsonValue]
    method: str
    poojaPrescribedHere: Optional[Dict[str, VastuJsonValue]]
    prescribedRoomsAtFacing: List[str]
    system: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuEntranceRecommendData(_VastuEntranceRecommendDataOptional):
    facing: Dict[str, VastuJsonValue]
    bestEntrancePada: Dict[str, VastuJsonValue]
    recommendedPadas: List[Dict[str, VastuJsonValue]]
    avoidPadas: List[Dict[str, VastuJsonValue]]

class _VastuFeedListingsDataOptional(TypedDict, total=False):
    dryRun: bool
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuFeedListingsData(_VastuFeedListingsDataOptional):
    accepted: int
    rejected: int
    skipped: int
    results: List[Dict[str, VastuJsonValue]]

class _VastuFloorPlanAuditDataOptional(TypedDict, total=False):
    gradeScale: Dict[str, VastuJsonValue]
    textParse: VastuFloorPlanAuditDataTextParse
    notAssessed: List[VastuFloorPlanAuditDataNotAssessedItem]
    scoreNote: str
    merchantCatalogId: str
    merchantCatalogRevision: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuFloorPlanAuditDataReceipt

class VastuFloorPlanAuditData(_VastuFloorPlanAuditDataOptional):
    score: Optional[float]
    grade: Optional[str]
    totalRooms: int
    prescribedCount: int
    defects: List[VastuFloorPlanAuditDataDefectsItem]
    sources: List[str]
    verified: bool
    computed: bool
    classification: str
    scoring: VastuFloorPlanAuditDataScoring

class _VastuFloorRulesDataOptional(TypedDict, total=False):
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    principle: str
    system: str
    tradition: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuFloorRulesData(_VastuFloorRulesDataOptional):
    masterBedroomFloor: int
    floorRules: List[Dict[str, VastuJsonValue]]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool

class _VastuFusionChartDataOptional(TypedDict, total=False):
    meta: Dict[str, VastuJsonValue]
    method: str
    system: str
    tradition: str
    verified: bool
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuFusionChartData(_VastuFusionChartDataOptional):
    ascendant: Dict[str, VastuJsonValue]
    grahaDirections: List[Dict[str, VastuJsonValue]]
    favourableDirections: List[Dict[str, VastuJsonValue]]
    cautionDirections: List[VastuFusionChartDataCautionDirectionsItem]
    methodology: Dict[str, VastuJsonValue]
    summary: str
    sources: List[str]

class _VastuJobResultsDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuJobResultsData(_VastuJobResultsDataOptional):
    jobId: str
    jobStatus: Literal["queued", "running", "completed", "partial", "failed", "cancelled"]
    results: List[VastuJsonValue]
    nextCursor: Optional[str]

class _VastuJobStatusDataOptional(TypedDict, total=False):
    webhookId: Optional[str]
    finishedAt: Optional[int]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuJobStatusData(_VastuJobStatusDataOptional):
    jobId: str
    status: Literal["queued", "running", "completed", "partial", "failed", "cancelled"]
    operation: Literal["assessments", "plan-analyze", "plan-report"]
    itemCount: int
    counts: VastuJobStatusDataCounts
    billing: VastuJobStatusDataBilling
    cancelRequested: bool
    createdAt: int
    updatedAt: int
    expiresAt: int
    resultsUrl: str

class _VastuJobSubmitDataOptional(TypedDict, total=False):
    preview: List[VastuJsonValue]
    previewNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuJobSubmitData(_VastuJobSubmitDataOptional):
    jobId: str
    status: Literal["queued", "running", "completed", "partial", "failed", "cancelled"]
    itemCount: int
    maxCharge: float
    replayed: bool

class _VastuLevelAnalysisDataOptional(TypedDict, total=False):
    idealOrdering: str
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    principle: str
    system: str
    tradition: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuLevelAnalysisData(_VastuLevelAnalysisDataOptional):
    idealLevels: List[Dict[str, VastuJsonValue]]
    observedAnalysis: Optional[Dict[str, VastuJsonValue]]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool

class _VastuMainGateDataOptional(TypedDict, total=False):
    facingAffectsPrescribedPadas: bool
    facingNote: str
    padaVerdict: Dict[str, VastuJsonValue]
    feature: str
    meta: Dict[str, VastuJsonValue]
    method: str
    remedyType: str
    system: str
    verified: bool
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuMainGateData(_VastuMainGateDataOptional):
    facing: str
    padaScheme: str
    prescribedPadas: List[int]
    rule: str
    remedy: str
    sources: List[Dict[str, VastuJsonValue]]
    computed: bool
    classification: str

class _VastuMandalaProjectionDataOptional(TypedDict, total=False):
    bearingAssumedNorth: bool
    classification: str
    computed: bool
    gridFrame: VastuMandalaProjectionDataGridFrame
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuMandalaProjectionData(_VastuMandalaProjectionDataOptional):
    cells: List[Dict[str, VastuJsonValue]]
    plotCentroid: List[float]
    bearingDeg: float
    sources: List[str]
    verified: bool

class _VastuMandalaReferenceDataOptional(TypedDict, total=False):
    zoneCount: int
    zones: List[VastuMandalaReferenceDataZonesItem]
    devataCount: int
    devatas: List[Dict[str, VastuJsonValue]]
    cells: List[VastuMandalaReferenceDataCellsItem]
    padaCount: int
    grid: Dict[str, VastuJsonValue]
    sources: List[str]
    system: str
    method: str
    note: str
    meta: Dict[str, VastuJsonValue]
    bearingDeg: float
    brahmasthanPadas: List[float]
    classBreakdown: Dict[str, VastuJsonValue]
    devataSource: str
    devataVerified: bool
    mandala: str
    plotCentroid: List[float]
    projected: bool
    tradition: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuMandalaReferenceData(_VastuMandalaReferenceDataOptional):
    verified: bool
    referenceVersion: str

class _VastuMeasurementUncertaintyOptional(TypedDict, total=False):
    coordinateUnits: Literal["m"]

class VastuMeasurementUncertainty(_VastuMeasurementUncertaintyOptional):
    pointResult: Dict[str, VastuJsonValue]
    results: List[VastuMeasurementUncertaintyResultsItem]
    stable: bool
    bounds: VastuMeasurementUncertaintyBounds
    rulesChanged: Literal[False]

class _VastuObstructionDataOptional(TypedDict, total=False):
    rangeClassification: str
    rangeSource: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuObstructionData(_VastuObstructionDataOptional):
    input: Dict[str, VastuJsonValue]
    matchedFeature: str
    effect: str
    rangeChecked: bool
    inRange: Optional[bool]
    houseHeightMultiples: Optional[float]
    verdict: str
    note: str
    source: str
    sources: List[str]
    verified: bool
    computed: bool
    classification: str

class _VastuOverallScoreDataOptional(TypedDict, total=False):
    basis: str
    formula: str
    gradeLabel: Optional[str]
    indexType: str
    input: Dict[str, VastuJsonValue]
    maxScore: float
    meta: Dict[str, VastuJsonValue]
    method: str
    scoreBreakdown: Dict[str, VastuJsonValue]
    system: str
    tradition: str
    verdict: Optional[str]
    notAssessed: List[VastuOverallScoreDataNotAssessedItem]
    scoreNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuOverallScoreDataReceipt

class VastuOverallScoreData(_VastuOverallScoreDataOptional):
    score: Optional[float]
    grade: Optional[str]
    placements: List[VastuOverallScoreDataPlacementsItem]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool
    scoring: VastuOverallScoreDataScoring

class _VastuPlacementDataOptional(TypedDict, total=False):
    deityClassification: Literal["classical", "convention"]
    deitySource: str
    elementSource: str
    tradition: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPlacementData(_VastuPlacementDataOptional):
    system: str
    method: str
    feature: str
    proposedZone: str
    verdict: str
    severity: str
    idealZones: List[str]
    acceptableZones: List[str]
    forbiddenZones: List[str]
    deity: str
    element: str
    elementVerified: bool
    principle: str
    reason: str
    remedy: Optional[str]
    remedyType: Optional[str]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool
    meta: Dict[str, VastuJsonValue]

class _VastuPlanAuditDataOptional(TypedDict, total=False):
    printReady: Dict[str, VastuJsonValue]
    tracedGeometry: VastuPlanAuditDataTracedGeometry
    gradeLabel: Optional[str]
    scoreDisclaimer: str
    artifact: VastuPlanAuditDataArtifact
    notAssessed: List[VastuPlanAuditDataNotAssessedItem]
    scoreNote: str
    warnings: List[Dict[str, VastuJsonValue]]
    uncertainty: VastuMeasurementUncertainty
    merchantCatalogId: str
    merchantCatalogRevision: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuPlanAuditDataReceipt
    units: str
    inputUnits: str
    metresPerInputUnit: float

class VastuPlanAuditData(_VastuPlanAuditDataOptional):
    system: str
    method: str
    input: Dict[str, VastuJsonValue]
    facing: Dict[str, VastuJsonValue]
    plotShape: Optional[Dict[str, VastuJsonValue]]
    overallScore: Optional[float]
    grade: Optional[str]
    summary: str
    zoneCompliance: List[Dict[str, VastuJsonValue]]
    roomByRoom: List[VastuPlanAuditDataRoomByRoomItem]
    defects: List[VastuPlanAuditDataDefectsItem]
    remedies: List[VastuPlanAuditDataRemediesItem]
    elementBalance: Dict[str, VastuJsonValue]
    sources: List[str]
    provenance: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]

class _VastuPlanConvertUnitsDataOptional(TypedDict, total=False):
    pricing: Dict[str, VastuJsonValue]
    units: str
    metresPerInputUnit: float

class VastuPlanConvertUnitsData(_VastuPlanConvertUnitsDataOptional):
    plan: Dict[str, VastuJsonValue]
    inputUnits: Literal["m", "ft", "mm", "in"]
    outputUnits: Literal["m", "ft", "mm", "in"]
    scaleFactor: float
    canonicalUnits: Literal["m"]

class _VastuPlanExportDxfDataOptional(TypedDict, total=False):
    pricing: Dict[str, VastuJsonValue]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    units: str
    inputUnits: str
    metresPerInputUnit: float

class VastuPlanExportDxfData(_VastuPlanExportDxfDataOptional):
    dxf: str
    contentType: str
    fileName: str
    version: str
    unitsCode: int
    trueNorthDeg: float
    zones: int
    roomCount: int
    openingCount: int
    dimensionCount: int
    findingCount: int
    needsReview: bool

class _VastuPlanExportIfcDataOptional(TypedDict, total=False):
    units: Literal["m"]
    pricing: Dict[str, VastuJsonValue]
    inputUnits: str
    metresPerInputUnit: float

class VastuPlanExportIfcData(_VastuPlanExportIfcDataOptional):
    ifc: str
    schema: Literal["IFC4"]
    contentType: str
    fileName: str
    outputUnits: Literal["m", "ft", "mm", "in"]
    roomCount: int
    canonicalUnits: Literal["m"]

class _VastuPlanGenerateDataOptional(TypedDict, total=False):
    svg: str
    architecturalRooms: List[Dict[str, VastuJsonValue]]
    derivedRoomProgramme: List[Dict[str, VastuJsonValue]]
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    requirements: Dict[str, VastuJsonValue]
    roomProgrammeNote: str
    sources: List[Dict[str, VastuJsonValue]]
    system: str
    variantCount: float
    variantNote: str
    verified: bool
    floors: List[Dict[str, VastuJsonValue]]
    core: Dict[str, VastuJsonValue]
    verticalChecks: List[Dict[str, VastuJsonValue]]
    floorNote: str
    uncertainty: VastuMeasurementUncertainty
    merchantCatalogId: str
    merchantCatalogRevision: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    units: str
    inputUnits: str
    metresPerInputUnit: float
    plotRegion: VastuPlanGenerateDataPlotRegion

class VastuPlanGenerateData(_VastuPlanGenerateDataOptional):
    plot: Dict[str, VastuJsonValue]
    entrance: Dict[str, VastuJsonValue]
    rooms: List[Dict[str, VastuJsonValue]]
    mandala: Dict[str, VastuJsonValue]
    compliance: Dict[str, VastuJsonValue]
    openings: Dict[str, VastuJsonValue]
    variants: List[Dict[str, VastuJsonValue]]
    recommendedVariant: str

class _VastuPlanImportDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    units: Literal["m", "drawing-units"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    metresPerInputUnit: float

class VastuPlanImportData(_VastuPlanImportDataOptional):
    plan: VastuPlanImportDataPlan
    north: VastuPlanImportDataNorth
    scale: VastuPlanImportDataScale
    dimensions: List[VastuPlanImportDataDimensionsItem]
    confidence: Dict[str, VastuJsonValue]
    needsReview: List[VastuPlanImportDataNeedsReviewItem]
    analysisReady: bool
    source: VastuPlanImportDataSource
    usage: VastuPlanImportDataUsage
    pricing: VastuPlanImportDataPricing

class _VastuPlanImportDxfDataOptional(TypedDict, total=False):
    pricing: Dict[str, VastuJsonValue]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    units: str
    inputUnits: str
    metresPerInputUnit: float

class VastuPlanImportDxfData(_VastuPlanImportDxfDataOptional):
    plan: VastuPlanImportDxfDataPlan
    mappingReport: List[VastuPlanImportDxfDataMappingReportItem]
    needsReview: bool
    reviewReasons: List[VastuPlanImportDxfDataReviewReasonsItem]

class _VastuPlanImportIfcDataOptional(TypedDict, total=False):
    pricing: Dict[str, VastuJsonValue]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    units: str
    inputUnits: str
    metresPerInputUnit: float

class VastuPlanImportIfcData(_VastuPlanImportIfcDataOptional):
    schema: str
    buildings: List[VastuPlanImportIfcDataBuildingsItem]
    storeys: List[VastuPlanImportIfcDataStoreysItem]
    trueNorthDeg: float
    mappingReport: List[VastuPlanImportIfcDataMappingReportItem]
    needsReview: bool
    reviewReasons: List[VastuPlanImportIfcDataReviewReasonsItem]

class _VastuPlanOptimizeDataOptional(TypedDict, total=False):
    svg: str
    compliance: Dict[str, VastuJsonValue]
    entrance: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    openings: Dict[str, VastuJsonValue]
    plot: Dict[str, VastuJsonValue]
    sources: List[Dict[str, VastuJsonValue]]
    system: str
    verified: bool
    uncertainty: VastuMeasurementUncertainty
    unmetConstraints: List[Dict[str, VastuJsonValue]]
    initialConstraintViolations: List[Dict[str, VastuJsonValue]]
    feasible: bool
    search: Dict[str, VastuJsonValue]
    scoring: Dict[str, VastuJsonValue]
    merchantCatalogId: str
    merchantCatalogRevision: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    units: str
    inputUnits: str
    metresPerInputUnit: float
    plotRegion: VastuPlanOptimizeDataPlotRegion

class VastuPlanOptimizeData(_VastuPlanOptimizeDataOptional):
    before: Dict[str, VastuJsonValue]
    after: Dict[str, VastuJsonValue]
    improvement: Dict[str, VastuJsonValue]
    moves: List[Dict[str, VastuJsonValue]]
    mandala: Dict[str, VastuJsonValue]

class _VastuPlotExtensionsCutsDataOptional(TypedDict, total=False):
    actualPlotArea: float
    areaEfficiency: float
    idealRectangleArea: float
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    provenance: Dict[str, VastuJsonValue]
    summary: str
    system: str
    verdict: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPlotExtensionsCutsData(_VastuPlotExtensionsCutsDataOptional):
    directions: List[Dict[str, VastuJsonValue]]
    extensions: List[str]
    cuts: List[str]
    severeCuts: List[str]
    sources: List[str]
    verified: bool

class _VastuPlotFromSurveyDataOptional(TypedDict, total=False):
    pricing: VastuPlotFromSurveyDataPricing
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPlotFromSurveyData(_VastuPlotFromSurveyDataOptional):
    method: Literal["plot-from-survey"]
    sourceCrs: str
    sourceUnits: str
    coordinateOrder: str
    frame: Dict[str, VastuJsonValue]
    plotPolygon: List[List[float]]
    controlPoints: List[Dict[str, VastuJsonValue]]
    areaM2: float
    gridConvergenceDeg: float
    boundaryGridConvergenceDeg: List[float]
    trueNorthGridBearingDeg: float
    maxDistanceFromOriginM: float

class _VastuPlotOrientationDataOptional(TypedDict, total=False):
    auspicious: bool
    deity: str
    facingSanskrit: str
    gradeProvenance: Dict[str, VastuJsonValue]
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    note: str
    provenance: Dict[str, VastuJsonValue]
    system: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPlotOrientationData(_VastuPlotOrientationDataOptional):
    facing: str
    grade: str
    doorPadaScheme: Dict[str, VastuJsonValue]
    sources: List[str]
    verified: bool

class _VastuPlotRatioDataOptional(TypedDict, total=False):
    rectangular: Literal[False]
    fillRatio: float
    ratioScope: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPlotRatioData(_VastuPlotRatioDataOptional):
    length: float
    width: float
    units: str
    unitsNote: str
    lengthM: Optional[float]
    widthM: Optional[float]
    ratio: float
    category: str
    acceptable: bool
    remedy: Optional[str]
    classicalSource: str
    sources: List[str]
    verified: bool
    boundingFrame: Literal["longest-edge-aligned"]

class _VastuPlotShapeDataOptional(TypedDict, total=False):
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPlotShapeData(_VastuPlotShapeDataOptional):
    shape: str
    vertices: int
    area: float
    bboxArea: float
    fillRatio: float
    vastuGrade: str
    notes: str
    classicalSource: str
    sources: List[str]
    verified: bool
    boundingFrame: Literal["longest-edge-aligned"]

class _VastuPlotSlopeDataOptional(TypedDict, total=False):
    verdict: str
    remedy: Optional[str]
    auspicious: bool
    effect: str
    effectProvenance: Dict[str, VastuJsonValue]
    idealRule: str
    idealRuleProvenance: Dict[str, VastuJsonValue]
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    provenance: Dict[str, VastuJsonValue]
    remedyType: Optional[str]
    system: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPlotSlopeData(_VastuPlotSlopeDataOptional):
    downSlopeDirection: str
    classicalReference: Dict[str, VastuJsonValue]
    sources: List[str]
    verified: bool

class VastuPortfolioAnalyticsData(TypedDict):
    fromEpoch: int
    toEpoch: int
    account: VastuPortfolioAnalyticsDataAccount
    byTag: Dict[str, VastuJsonValue]

class VastuPortfolioBudgetsGetData(TypedDict):
    dimensions: Dict[str, VastuJsonValue]
    period: Literal["lifetime"]

class VastuPortfolioBudgetsSetData(TypedDict):
    scope: VastuPortfolioBudgetsSetDataScope
    capUsd: Optional[str]
    period: Literal["lifetime"]

class VastuPortfolioCompareData(TypedDict):
    properties: List[VastuPortfolioCompareDataPropertiesItem]
    comparableGroups: Dict[str, VastuJsonValue]
    crossRulesetRanking: Literal[False]

class VastuPortfolioSearchData(TypedDict):
    properties: List[VastuPortfolioSearchDataPropertiesItem]
    total: int
    nextCursor: Optional[str]

class VastuPortfolioUsageData(TypedDict):
    fromEpoch: int
    toEpoch: int
    retentionDays: int
    groups: List[VastuPortfolioUsageDataGroupsItem]

class VastuPortfolioUsageExportData(TypedDict):
    csv: str
    filename: str
    contentType: str

class VastuPropertiesActivityExportData(TypedDict):
    events: List[VastuPropertiesActivityExportDataEventsItem]
    nextCursor: Optional[int]
    format: Literal["jsonl"]
    content: str

class VastuPropertiesActivityListData(TypedDict):
    events: List[VastuPropertiesActivityListDataEventsItem]
    nextCursor: Optional[int]

class VastuPropertiesCollaborationCommentData(TypedDict):
    comment: VastuPropertiesCollaborationCommentDataComment

class VastuPropertiesCollaborationGetData(TypedDict):
    property: VastuPropertiesCollaborationGetDataProperty
    comments: List[VastuPropertiesCollaborationGetDataCommentsItem]
    reviews: List[VastuPropertiesCollaborationGetDataReviewsItem]

class VastuPropertiesCollaborationInviteData(TypedDict):
    invitationId: str
    status: Literal["pending", "accepted"]

class VastuPropertiesCollaborationMembersData(TypedDict):
    members: Dict[str, VastuJsonValue]

class VastuPropertiesCollaborationReviewData(TypedDict):
    review: VastuPropertiesCollaborationReviewDataReview

class _VastuPropertiesCollaborationRevokeDataOptional(TypedDict, total=False):
    accountId: str
    invitationId: str

class VastuPropertiesCollaborationRevokeData(_VastuPropertiesCollaborationRevokeDataOptional):
    revoked: bool

class VastuPropertiesCollaborationUpdateData(TypedDict):
    property: VastuPropertiesCollaborationUpdateDataProperty

class _VastuPropertiesCreateDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPropertiesCreateData(_VastuPropertiesCreateDataOptional):
    propertyId: str
    ownerId: str
    ids: VastuPropertiesCreateDataIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuPropertiesCreateDataArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str

class _VastuPropertiesDeleteDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    erasureStatus: Literal["pending", "completed"]
    erasureReceipt: VastuPropertiesDeleteDataErasureReceipt
    retryAfterEpoch: int
    exportDeleted: bool
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    revisionId: str
    replayed: bool

class VastuPropertiesDeleteData(_VastuPropertiesDeleteDataOptional):
    propertyId: str
    deleted: bool

class _VastuPropertiesGetDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPropertiesGetData(_VastuPropertiesGetDataOptional):
    propertyId: str
    ownerId: str
    ids: VastuPropertiesGetDataIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuPropertiesGetDataArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str

class _VastuPropertiesLinkScanDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPropertiesLinkScanData(_VastuPropertiesLinkScanDataOptional):
    propertyId: str
    ownerId: str
    ids: VastuPropertiesLinkScanDataIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuPropertiesLinkScanDataArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str

class _VastuPropertiesListDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPropertiesListData(_VastuPropertiesListDataOptional):
    properties: List[VastuPropertiesListDataPropertiesItem]
    nextCursor: Optional[str]

class _VastuPropertiesUpdateDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuPropertiesUpdateData(_VastuPropertiesUpdateDataOptional):
    propertyId: str
    ownerId: str
    ids: VastuPropertiesUpdateDataIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int
    expiresAtEpoch: int
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    archiveTier: Optional[VastuPropertiesUpdateDataArchiveTier]
    externalId: Optional[str]
    createdAtEpoch: int
    updatedAtEpoch: int
    contentHash: str

class _VastuQuoteCalculateDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuQuoteCalculateData(_VastuQuoteCalculateDataOptional):
    workflowId: str
    currency: Literal["USD"]
    subtotal: str
    total: str
    lineItems: List[VastuQuoteCalculateDataLineItemsItem]
    explanation: str

class _VastuReceiptVerifyDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuReceiptVerifyData(_VastuReceiptVerifyDataOptional):
    valid: Literal[True]
    receipt: VastuReceiptVerifyDataReceipt
    inputMatched: Optional[bool]
    charged: Literal[0]

class _VastuRemediationTaskDataOptional(TypedDict, total=False):
    assignee: Optional[str]
    dueDate: Optional[str]
    evidence: List[VastuRemediationTaskDataEvidenceItem]
    createdAt: int
    updatedAt: int
    completedAt: Optional[int]
    reassessment: Dict[str, VastuJsonValue]
    reassessmentLink: VastuRemediationTaskDataReassessmentLink
    history: List[Dict[str, VastuJsonValue]]

class VastuRemediationTaskData(_VastuRemediationTaskDataOptional):
    taskId: str
    reportRef: str
    findingRef: str
    remedyKey: str
    title: str
    status: Literal["pending", "in_progress", "completed", "cancelled"]

class _VastuRemedyComparisonDataOptional(TypedDict, total=False):
    meta: Dict[str, VastuJsonValue]
    method: str
    system: str
    tradition: str
    verified: bool
    notAssessed: List[VastuRemedyComparisonDataNotAssessedItem]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuRemedyComparisonData(_VastuRemedyComparisonDataOptional):
    before: VastuRemedyComparisonDataBefore
    after: VastuRemedyComparisonDataAfter
    scoreDelta: Optional[float]
    scoring: Dict[str, VastuJsonValue]
    verdict: Optional[str]
    remediesApplied: List[Dict[str, VastuJsonValue]]
    roomChanges: List[Dict[str, VastuJsonValue]]
    sources: List[str]

class _VastuRoadOrientationDataOptional(TypedDict, total=False):
    chaturMukhi: bool
    hasNorthOrEastRoad: bool
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    provenance: Dict[str, VastuJsonValue]
    summary: str
    system: str
    verdict: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuRoadOrientationData(_VastuRoadOrientationDataOptional):
    roadAnalysis: List[Dict[str, VastuJsonValue]]
    beneficRoads: List[str]
    cautionRoads: List[str]
    veedhiShoola: Dict[str, VastuJsonValue]
    sources: List[str]
    verified: bool

class _VastuRoomDataOptional(TypedDict, total=False):
    storageType: str
    placementVerified: bool
    guidanceClassification: Optional[str]
    uncertainty: VastuMeasurementUncertainty
    roomTypeApplied: Literal["master_bedroom", "bedroom", "guest", "children"]
    roomTypeDefaulted: bool
    roomTypeNote: str
    merchantCatalogId: str
    merchantCatalogRevision: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuRoomData(_VastuRoomDataOptional):
    system: str
    method: str
    room: str
    placement: Dict[str, VastuJsonValue]
    verdict: str
    severity: str
    idealZones: List[str]
    acceptableZones: List[str]
    forbiddenZones: List[str]
    defect: Optional[Dict[str, VastuJsonValue]]
    remedy: Optional[str]
    remedyType: Optional[str]
    guidance: Optional[str]
    citation: Dict[str, VastuJsonValue]
    verified: bool
    meta: Dict[str, VastuJsonValue]

class _VastuRuleVersionsDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuRuleVersionsData(_VastuRuleVersionsDataOptional):
    currentVersion: str
    retainedVersions: int
    versions: List[str]
    scope: str
    scoringVersion: str

class _VastuScanStoredDataOptional(TypedDict, total=False):
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuScanStoredData(_VastuScanStoredDataOptional):
    schemaVersion: Literal[1]
    propertyId: str
    snapshot: VastuJsonValue
    audit: VastuJsonValue
    scanQuality: Optional[VastuJsonValue]
    captureVerification: Literal["unverified-caller-input"]
    geometryUnits: Literal["metres"]
    assessmentNote: str

class _VastuScansDeleteDataOptional(TypedDict, total=False):
    previewNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuScansDeleteData(_VastuScansDeleteDataOptional):
    scanId: str
    deleted: bool
    deletionScope: str
    persistence: Literal["account-store", "preview-only"]

class _VastuScansListDataOptional(TypedDict, total=False):
    paginationNote: str
    previewNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuScansListData(_VastuScansListDataOptional):
    scans: List[VastuJsonValue]
    nextCursor: Optional[str]
    persistence: Literal["account-store", "preview-only"]

class _VastuScansRetrieveDataOptional(TypedDict, total=False):
    previewNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuScansRetrieveData(_VastuScansRetrieveDataOptional):
    scan: VastuJsonValue
    persistence: Literal["account-store", "preview-only"]

class _VastuScansSaveDataOptional(TypedDict, total=False):
    retentionNote: str
    previewNote: str
    deviceAttestation: VastuJsonValue
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuScansSaveData(_VastuScansSaveDataOptional):
    scan: VastuJsonValue
    replayed: bool
    persistence: Literal["account-store", "preview-only"]

class _VastuScansTimelapseDataOptional(TypedDict, total=False):
    previewNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuScansTimelapseData(_VastuScansTimelapseDataOptional):
    propertyId: str
    scans: List[VastuJsonValue]
    comparisonNote: str
    physicalChangeVerified: Literal[False]
    persistence: Literal["account-store", "preview-only"]

class _VastuSingleRoomAuditDataOptional(TypedDict, total=False):
    remedyKey: Optional[str]
    remedyParams: Dict[str, VastuJsonValue]
    remedyClassification: Optional[str]
    remedySource: Optional[str]
    merchantCatalogId: str
    merchantCatalogRevision: int
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuSingleRoomAuditData(_VastuSingleRoomAuditDataOptional):
    input: Dict[str, VastuJsonValue]
    compliance: str
    severity: str
    recommendedZone: Optional[str]
    remedy: str
    sources: List[str]
    verified: bool
    computed: bool
    classification: str

class _VastuSpecializedAuditDataOptional(TypedDict, total=False):
    buildingDirection: Dict[str, VastuJsonValue]
    notAssessed: List[VastuSpecializedAuditDataNotAssessedItem]
    scoreNote: str
    uncertainty: VastuMeasurementUncertainty
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuSpecializedAuditDataReceipt

class VastuSpecializedAuditData(_VastuSpecializedAuditDataOptional):
    system: str
    method: str
    buildingType: str
    score: Optional[float]
    grade: Optional[str]
    scoringBasis: str
    auditedRooms: int
    idealCount: int
    compliantCount: int
    defectCount: int
    findings: List[VastuSpecializedAuditDataFindingsItem]
    remedies: List[Dict[str, VastuJsonValue]]
    unknownRooms: List[Dict[str, VastuJsonValue]]
    sources: List[str]
    provenance: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]

class _VastuSunPathDataOptional(TypedDict, total=False):
    sunriseUtc: str
    sunriseAzimuthDeg: float
    solarNoonUtc: str
    solarNoonAzimuthDeg: float
    solarNoonElevationDeg: float
    sunsetUtc: str
    sunsetAzimuthDeg: float
    declinationDeg: float
    dayStatus: Literal["normal", "polarDay", "polarNight"]
    note: str
    noonUtc: str
    noonElevationDeg: float
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuSunPathData(_VastuSunPathDataOptional):
    input: VastuSunPathDataInput
    arc: List[Dict[str, VastuJsonValue]]
    sources: List[str]
    verified: bool

class _VastuTimingDataOptional(TypedDict, total=False):
    foundationRite: Dict[str, VastuJsonValue]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuTimingData(_VastuTimingDataOptional):
    system: str
    method: str
    activity: str
    input: Dict[str, VastuJsonValue]
    summary: Dict[str, VastuJsonValue]
    auspiciousDates: List[Dict[str, VastuJsonValue]]
    meta: Dict[str, VastuJsonValue]
    guidance: Dict[str, VastuJsonValue]

class _VastuWallAnalysisDataOptional(TypedDict, total=False):
    idealOrdering: str
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    principle: str
    system: str
    tradition: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuWallAnalysisData(_VastuWallAnalysisDataOptional):
    idealWalls: List[Dict[str, VastuJsonValue]]
    observedAnalysis: Optional[Dict[str, VastuJsonValue]]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool

class _VastuWorkflowDataOptional(TypedDict, total=False):
    mutationId: str
    contentHash: str
    expiresAt: int
    updatedAt: int
    deleted: bool
    data: VastuWorkflowDataData
    remedies: List[VastuWorkflowDataRemediesItem]
    merchantCatalogId: str
    merchantCatalogRevision: int

class VastuWorkflowData(_VastuWorkflowDataOptional):
    revision: int

class _VastuWorkspaceDataOptional(TypedDict, total=False):
    record: Dict[str, VastuJsonValue]
    replayed: bool
    records: List[Dict[str, VastuJsonValue]]
    id: str
    title: str
    expiresAt: int
    reset: bool
    deletedRecords: int
    payload: str
    headers: Dict[str, VastuJsonValue]
    deliveryMode: str
    retentionDays: int
    maxRecords: int
    html: str
    svg: str

class VastuWorkspaceData(_VastuWorkspaceDataOptional):
    pass

class _VastuZoneReferenceDataOptional(TypedDict, total=False):
    system: str
    method: str
    note: str
    tradition: str
    meta: Dict[str, VastuJsonValue]
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]

class VastuZoneReferenceData(_VastuZoneReferenceDataOptional):
    zoneCount: int
    zones: List[Dict[str, VastuJsonValue]]
    verified: bool
    referenceVersion: str

class _VastuZoneWiseScoreDataOptional(TypedDict, total=False):
    basis: str
    indexType: str
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    strongestZone: Optional[str]
    system: str
    tradition: str
    weakestZone: Optional[str]
    zoneWeightingNote: str
    notAssessed: List[VastuZoneWiseScoreDataNotAssessedItem]
    scoreNote: str
    rulesVersion: Literal["vastu-rules-2026-09-23", "vastu-rules-2026-10-04"]
    receipt: VastuZoneWiseScoreDataReceipt

class VastuZoneWiseScoreData(_VastuZoneWiseScoreDataOptional):
    zones: List[VastuZoneWiseScoreDataZonesItem]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool
    overallGrade: Optional[str]
    overallScore: Optional[float]
    scoring: VastuZoneWiseScoreDataScoring

class VastuBilling(TypedDict):
    charged: float
    currency: str
    balanceAfter: float
    endpoint: str
    category: str
class VastuMeta(TypedDict):
    engine: str
    version: str
class VastuArScanQualityResponse(TypedDict):
    success: Literal[True]
    data: VastuArScanQualityData
    billing: VastuBilling
    meta: VastuMeta

class VastuArTrueNorthCalibrateResponse(TypedDict):
    success: Literal[True]
    data: VastuArTrueNorthData
    billing: VastuBilling
    meta: VastuMeta

class _VastuAssessmentsResponseOptional(TypedDict, total=False):
    billing: VastuBilling

class VastuAssessmentsResponse(_VastuAssessmentsResponseOptional):
    success: Literal[True]
    data: VastuAssessmentData
    meta: VastuMeta

class VastuAssessmentsBatchResponse(TypedDict):
    success: Literal[True]
    data: VastuAssessmentBatchData


class VastuAuditFloorPlanResponse(TypedDict):
    success: Literal[True]
    data: VastuFloorPlanAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuAuditFloorPlanDetailedResponse(TypedDict):
    success: Literal[True]
    data: VastuDetailedFloorPlanAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuAuditSingleRoomResponse(TypedDict):
    success: Literal[True]
    data: VastuSingleRoomAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuCompareBeforeAfterRemedyResponse(TypedDict):
    success: Literal[True]
    data: VastuRemedyComparisonData
    billing: VastuBilling
    meta: VastuMeta

class VastuCompoundWallAnalysisResponse(TypedDict):
    success: Literal[True]
    data: VastuWallAnalysisData
    billing: VastuBilling
    meta: VastuMeta

class VastuDirectionAuspiciousFacingResponse(TypedDict):
    success: Literal[True]
    data: VastuAuspiciousFacingData
    billing: VastuBilling
    meta: VastuMeta

class VastuDirectionCorrectResponse(TypedDict):
    success: Literal[True]
    data: VastuDirectionCorrectData
    billing: VastuBilling
    meta: VastuMeta

class VastuDirectionDeclinationResponse(TypedDict):
    success: Literal[True]
    data: VastuDirectionDeclinationData
    billing: VastuBilling
    meta: VastuMeta

class VastuDirectionSunPathResponse(TypedDict):
    success: Literal[True]
    data: VastuSunPathData
    billing: VastuBilling
    meta: VastuMeta

class VastuDirectionZoneFromBearingResponse(TypedDict):
    success: Literal[True]
    data: VastuBearingZoneData
    billing: VastuBilling
    meta: VastuMeta

class VastuElementsBalanceSuggestResponse(TypedDict):
    success: Literal[True]
    data: VastuElementBalanceData
    billing: VastuBilling
    meta: VastuMeta

class VastuElementsDistributionResponse(TypedDict):
    success: Literal[True]
    data: VastuElementDistributionData
    billing: VastuBilling
    meta: VastuMeta

class VastuEntranceObstructionCheckResponse(TypedDict):
    success: Literal[True]
    data: VastuObstructionData
    billing: VastuBilling
    meta: VastuMeta

class VastuEntrancePadaResponse(TypedDict):
    success: Literal[True]
    data: VastuEntrancePadaData
    billing: VastuBilling
    meta: VastuMeta

class VastuEntranceRecommendResponse(TypedDict):
    success: Literal[True]
    data: VastuEntranceRecommendData
    billing: VastuBilling
    meta: VastuMeta

class VastuFloorLevelAnalysisResponse(TypedDict):
    success: Literal[True]
    data: VastuLevelAnalysisData
    billing: VastuBilling
    meta: VastuMeta

class VastuFusionChartResponse(TypedDict):
    success: Literal[True]
    data: VastuFusionChartData
    billing: VastuBilling
    meta: VastuMeta

class VastuMandalaProject81PadaResponse(TypedDict):
    success: Literal[True]
    data: VastuMandalaProjectionData
    billing: VastuBilling
    meta: VastuMeta

class VastuMandalaProject9ZoneResponse(TypedDict):
    success: Literal[True]
    data: VastuMandalaProjectionData
    billing: VastuBilling
    meta: VastuMeta

class VastuMandalaProjectBrahmasthanResponse(TypedDict):
    success: Literal[True]
    data: VastuBrahmasthanProjectionData
    billing: VastuBilling
    meta: VastuMeta

class VastuMultiStoreyFloorRulesResponse(TypedDict):
    success: Literal[True]
    data: VastuFloorRulesData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementBalconyResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementBorewellResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementGardenResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementGeneratorElectricalResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementMainGateResponse(TypedDict):
    success: Literal[True]
    data: VastuMainGateData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementOverheadTankResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementSepticTankResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementTreeResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementWellResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlacementWindowResponse(TypedDict):
    success: Literal[True]
    data: VastuPlacementData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlanAnalyzeResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlanFromRequirementsResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanGenerateData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlanGenerateResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanGenerateData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlanOptimizeResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanOptimizeData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlanReportResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlanImportImageResponse(TypedDict):
    success: bool
    data: VastuPlanImportData
    billing: Dict[str, Any]
    meta: Dict[str, Any]

VastuPlanImportPdfResponse = VastuPlanImportImageResponse

class VastuPlanUploadResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlotExtensionsCutsResponse(TypedDict):
    success: Literal[True]
    data: VastuPlotExtensionsCutsData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlotOrientationResponse(TypedDict):
    success: Literal[True]
    data: VastuPlotOrientationData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlotRatioResponse(TypedDict):
    success: Literal[True]
    data: VastuPlotRatioData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlotRoadOrientationResponse(TypedDict):
    success: Literal[True]
    data: VastuRoadOrientationData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlotShapeResponse(TypedDict):
    success: Literal[True]
    data: VastuPlotShapeData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlotSlopeResponse(TypedDict):
    success: Literal[True]
    data: VastuPlotSlopeData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceColorsByZoneResponse(TypedDict):
    success: Literal[True]
    data: VastuZoneReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceDefectsCatalogResponse(TypedDict):
    success: Literal[True]
    data: VastuCatalogReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceDirections16Response(TypedDict):
    success: Literal[True]
    data: VastuDirectionsReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceDirections32Response(TypedDict):
    success: Literal[True]
    data: VastuDirections32ReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceDirections8Response(TypedDict):
    success: Literal[True]
    data: VastuDirectionsReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceGateObstructionsResponse(TypedDict):
    success: Literal[True]
    data: VastuCatalogReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceMandala45DevatasResponse(TypedDict):
    success: Literal[True]
    data: VastuMandalaReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceMandala64PadaResponse(TypedDict):
    success: Literal[True]
    data: VastuMandalaReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceMandala9ZoneResponse(TypedDict):
    success: Literal[True]
    data: VastuMandalaReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceMaterialsByZoneResponse(TypedDict):
    success: Literal[True]
    data: VastuZoneReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuReferenceRemediesCatalogResponse(TypedDict):
    success: Literal[True]
    data: VastuCatalogReferenceData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomBedroomResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomDiningResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomKitchenResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomLivingResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomPoojaResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomStaircaseResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomStoreResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomStudyResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomToiletResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuRoomWaterStorageResponse(TypedDict):
    success: Literal[True]
    data: VastuRoomData
    billing: VastuBilling
    meta: VastuMeta

class VastuScoreComplianceIndexResponse(TypedDict):
    success: Literal[True]
    data: VastuComplianceIndexData
    billing: VastuBilling
    meta: VastuMeta

class VastuScoreOverallResponse(TypedDict):
    success: Literal[True]
    data: VastuOverallScoreData
    billing: VastuBilling
    meta: VastuMeta

class VastuScoreZoneWiseResponse(TypedDict):
    success: Literal[True]
    data: VastuZoneWiseScoreData
    billing: VastuBilling
    meta: VastuMeta

class VastuSpecializedCommercialResponse(TypedDict):
    success: Literal[True]
    data: VastuSpecializedAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuSpecializedEducationalResponse(TypedDict):
    success: Literal[True]
    data: VastuSpecializedAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuSpecializedFactoryResponse(TypedDict):
    success: Literal[True]
    data: VastuSpecializedAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuSpecializedHospitalResponse(TypedDict):
    success: Literal[True]
    data: VastuSpecializedAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuSpecializedResidentialResponse(TypedDict):
    success: Literal[True]
    data: VastuSpecializedAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuSpecializedRestaurantResponse(TypedDict):
    success: Literal[True]
    data: VastuSpecializedAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuSpecializedTempleResponse(TypedDict):
    success: Literal[True]
    data: VastuSpecializedAuditData
    billing: VastuBilling
    meta: VastuMeta

class VastuTimingBhumiPujanResponse(TypedDict):
    success: Literal[True]
    data: VastuTimingData
    billing: VastuBilling
    meta: VastuMeta

class VastuTimingConstructionStartResponse(TypedDict):
    success: Literal[True]
    data: VastuTimingData
    billing: VastuBilling
    meta: VastuMeta

class VastuTimingGrihapraveshResponse(TypedDict):
    success: Literal[True]
    data: VastuTimingData
    billing: VastuBilling
    meta: VastuMeta

class VastuTimingVastuShantiResponse(TypedDict):
    success: Literal[True]
    data: VastuTimingData
    billing: VastuBilling
    meta: VastuMeta

class VastuArHeatmapRasterResponse(TypedDict):
    success: Literal[True]
    data: VastuArHeatmapRasterData
    billing: VastuBilling
    meta: VastuMeta

class VastuArAnchorRecommendationsResponse(TypedDict):
    success: Literal[True]
    data: VastuArAnchorRecommendationsData
    billing: VastuBilling
    meta: VastuMeta

class VastuArCaptureMergeResponse(TypedDict):
    success: bool
    data: VastuArCaptureMergeData
    billing: VastuBilling
    meta: VastuMeta

class VastuPlotFromSurveyResponse(TypedDict):
    success: bool
    data: VastuPlotFromSurveyData
    billing: VastuBilling
    meta: VastuMeta

class VastuArRoomCaptureResponse(TypedDict):
    success: Literal[True]
    data: VastuArRoomCaptureData
    billing: VastuBilling
    meta: VastuMeta

class VastuArZoneTexturesResponse(TypedDict):
    success: Literal[True]
    data: VastuArZoneTexturesData
    billing: VastuBilling
    meta: VastuMeta

class VastuArYantraMeshesResponse(TypedDict):
    success: Literal[True]
    data: VastuArYantraMeshesData
    billing: VastuBilling
    meta: VastuMeta

class VastuArDeityIconsResponse(TypedDict):
    success: Literal[True]
    data: VastuArDeityIconsData
    billing: VastuBilling
    meta: VastuMeta

class _VastuScansSaveResponseOptional(TypedDict, total=False):
    billing: Optional[VastuBilling]
    meta: VastuMeta
class VastuScansSaveResponse(_VastuScansSaveResponseOptional):
    success: Literal[True]
    data: VastuScansSaveData

class _VastuScansRetrieveResponseOptional(TypedDict, total=False):
    billing: Optional[VastuBilling]
    meta: VastuMeta
class VastuScansRetrieveResponse(_VastuScansRetrieveResponseOptional):
    success: Literal[True]
    data: VastuScansRetrieveData

class _VastuScansListResponseOptional(TypedDict, total=False):
    billing: Optional[VastuBilling]
    meta: VastuMeta
class VastuScansListResponse(_VastuScansListResponseOptional):
    success: Literal[True]
    data: VastuScansListData

class _VastuArAttestationChallengeResponseOptional(TypedDict, total=False):
    billing: Optional[VastuBilling]
    meta: VastuMeta
class VastuArAttestationChallengeResponse(_VastuArAttestationChallengeResponseOptional):
    success: Literal[True]
    data: VastuArAttestationChallengeData

class _VastuScansDeleteResponseOptional(TypedDict, total=False):
    billing: Optional[VastuBilling]
    meta: VastuMeta
class VastuScansDeleteResponse(_VastuScansDeleteResponseOptional):
    success: Literal[True]
    data: VastuScansDeleteData

class _VastuScansTimelapseResponseOptional(TypedDict, total=False):
    billing: Optional[VastuBilling]
    meta: VastuMeta
class VastuScansTimelapseResponse(_VastuScansTimelapseResponseOptional):
    success: Literal[True]
    data: VastuScansTimelapseData


class VastuJobsRequestItemsItem(TypedDict):
    id: str
    input: Union[VastuAssessmentsRequest, VastuPlanAnalyzeRequest, VastuPlanReportRequest]

class _VastuJobsRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    webhookId: str

class VastuJobsRequest(_VastuJobsRequestOptional):
    """Queue 1 to 1,000 assessments. Submit needs a caller-retained Idempotency-Key."""
    operation: Literal["assessments", "plan-analyze", "plan-report"]
    items: List[VastuJobsRequestItemsItem]

class _VastuJobResultItemOptional(TypedDict, total=False):
    artifacts: List[Dict[str, str]]
    code: Optional[str]

class VastuJobResultItem(_VastuJobResultItemOptional):
    """One finished item. ``status`` is the HTTP status the single-item call would have returned."""
    id: str
    index: int
    status: int
    response: Dict[str, VastuJsonValue]

class _VastuJobSubmitResultOptional(TypedDict, total=False):
    preview: List[VastuJobResultItem]
    previewNote: str

class VastuJobSubmitResult(_VastuJobSubmitResultOptional):
    """Submit data with the sandbox preview typed as result items."""
    jobId: str
    status: Literal["queued", "running", "completed", "partial", "failed", "cancelled"]
    itemCount: int
    maxCharge: float
    replayed: bool

class VastuJobResultsPage(TypedDict):
    """One page of results with the items typed."""
    jobId: str
    jobStatus: Literal["queued", "running", "completed", "partial", "failed", "cancelled"]
    results: List[VastuJobResultItem]
    nextCursor: Optional[str]

class VastuJobsResponse(TypedDict):
    success: Literal[True]
    data: VastuJobSubmitResult

class VastuJobsIdResponse(TypedDict):
    success: Literal[True]
    data: VastuJobStatusData

class VastuJobsIdResultsResponse(TypedDict):
    success: Literal[True]
    data: VastuJobResultsPage

class VastuJobsIdCancelResponse(TypedDict):
    success: Literal[True]
    data: VastuJobStatusData

_VASTU_JOB_ID = re.compile(r"^vjob_[0-9a-f]{32}$")
_VASTU_UPLOAD_ID = re.compile(r"^vup_[0-9a-f]{32}$")
_VASTU_UPLOAD_KEY = re.compile(r"^[!-~]{1,256}$")
# jobs/{id} and jobs/{id}/results are GET; jobs and jobs/{id}/cancel are POST.
_VASTU_JOB_PATH = re.compile(r"^jobs/([^/]+)(/results|/cancel)?$")


def _vastu_job_id(job_id):
    if not isinstance(job_id, str) or not _VASTU_JOB_ID.match(job_id):
        raise ValueError("job_id must be the vjob_... id returned when the job was submitted")
    return job_id


def _is_vastu_get_path(path):
    """True for the Vastu paths the server answers over GET."""
    if path.startswith("reference/") or path == "direction/declination":
        return True
    match = _VASTU_JOB_PATH.match(path)
    return bool(match) and match.group(2) in (None, "/results")


class _VastuCommerceBillingOptional(TypedDict, total=False):
    chargedCents: int
    actionCents: int
    meterCents: int
    totalCents: int
    storedBytes: int
    refundedCents: int
    endpoint: str
    refundPending: bool

class VastuCommerceBilling(_VastuCommerceBillingOptional):
    pass

class _VastuDrawingSheetRequestTitleBlockOptional(TypedDict, total=False):
    drawingNumber: str
    revision: str
    date: str

class _VastuDrawingSheetResponseOptional(TypedDict, total=False):
    billing: Dict[str, VastuJsonValue]

class VastuDrawingSheetResponse(_VastuDrawingSheetResponseOptional):
    success: bool
    data: VastuDrawingSheetData

class _VastuWorkspaceResponseOptional(TypedDict, total=False):
    billing: Dict[str, VastuJsonValue]

class VastuWorkspaceResponse(_VastuWorkspaceResponseOptional):
    success: bool
    data: VastuWorkspaceData
    mode: Literal["sandbox"]

class VastuDrawingSheetRequestTitleBlock(_VastuDrawingSheetRequestTitleBlockOptional):
    project: str
    architect: str


class _VastuDrawingSheetRequestFieldEvidenceItemOptional(TypedDict, total=False):
    note: str
    roomId: str
    imageDataUrl: str

class VastuDrawingSheetRequestFieldEvidenceItem(_VastuDrawingSheetRequestFieldEvidenceItemOptional):
    label: str


class _VastuDrawingSheetRequestOptional(TypedDict, total=False):
    paperSize: str
    scaleDenominator: int
    format: str
    zoneOverlay: bool
    dimensions: bool
    fieldEvidence: List[VastuDrawingSheetRequestFieldEvidenceItem]

class VastuDrawingSheetRequest(_VastuDrawingSheetRequestOptional):
    plan: Dict[str, VastuJsonValue]
    titleBlock: VastuDrawingSheetRequestTitleBlock


class _VastuWorkspaceRequestDrawingTitleBlockOptional(TypedDict, total=False):
    drawingNumber: str
    revision: str
    date: str

class VastuWorkspaceRequestDrawingTitleBlock(_VastuWorkspaceRequestDrawingTitleBlockOptional):
    project: str
    architect: str


class _VastuWorkspaceRequestDrawingFieldEvidenceItemOptional(TypedDict, total=False):
    note: str
    roomId: str
    imageDataUrl: str

class VastuWorkspaceRequestDrawingFieldEvidenceItem(_VastuWorkspaceRequestDrawingFieldEvidenceItemOptional):
    label: str


class _VastuWorkspaceRequestDrawingOptional(TypedDict, total=False):
    paperSize: str
    scaleDenominator: int
    format: str
    zoneOverlay: bool
    dimensions: bool
    fieldEvidence: List[VastuWorkspaceRequestDrawingFieldEvidenceItem]

class VastuWorkspaceRequestDrawing(_VastuWorkspaceRequestDrawingOptional):
    plan: Dict[str, VastuJsonValue]
    titleBlock: VastuWorkspaceRequestDrawingTitleBlock


class _VastuWorkspaceRequestOptional(TypedDict, total=False):
    propertyId: str
    jobId: str
    idempotencyKey: str
    title: str
    input: Dict[str, VastuJsonValue]
    outcome: str
    webhookSecret: str
    drawing: VastuWorkspaceRequestDrawing

class VastuWorkspaceRequest(_VastuWorkspaceRequestOptional):
    pass


class VastuPropertiesCreateRequestIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class _VastuPropertiesCreateRequestOptional(TypedDict, total=False):
    tenantRef: str
    propertyId: str
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    externalId: str

class VastuPropertiesCreateRequest(_VastuPropertiesCreateRequestOptional):
    ids: VastuPropertiesCreateRequestIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int

class VastuPropertiesUpdateRequestIds(TypedDict):
    project: str
    building: str
    unit: str
    floor: str
    revision: str

class _VastuPropertiesUpdateRequestOptional(TypedDict, total=False):
    tenantRef: str
    linkedScanIds: List[str]
    linkedAssessmentIds: List[str]
    externalId: str

class VastuPropertiesUpdateRequest(_VastuPropertiesUpdateRequestOptional):
    propertyId: str
    ids: VastuPropertiesUpdateRequestIds
    title: str
    data: Dict[str, VastuJsonValue]
    retentionDays: int

class _VastuPropertiesCollaborationGetRequestOptional(TypedDict, total=False):
    ownerId: str

class VastuPropertiesCollaborationGetRequest(_VastuPropertiesCollaborationGetRequestOptional):
    propertyId: str

class VastuPropertiesCollaborationGetResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesCollaborationGetData
    billing: VastuBilling

class _VastuPropertiesCollaborationInviteRequestOptional(TypedDict, total=False):
    ownerId: str
    accountId: str
    email: str
    accept: bool

class VastuPropertiesCollaborationInviteRequest(_VastuPropertiesCollaborationInviteRequestOptional):
    propertyId: str
    role: Literal["viewer", "editor", "reviewer"]

class VastuPropertiesCollaborationInviteResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesCollaborationInviteData
    billing: VastuBilling

class _VastuPropertiesCollaborationRevokeRequestOptional(TypedDict, total=False):
    ownerId: str
    accountId: str
    invitationId: str

class VastuPropertiesCollaborationRevokeRequest(_VastuPropertiesCollaborationRevokeRequestOptional):
    propertyId: str

class VastuPropertiesCollaborationRevokeResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesCollaborationRevokeData
    billing: VastuBilling

class _VastuPropertiesCollaborationMembersRequestOptional(TypedDict, total=False):
    ownerId: str

class VastuPropertiesCollaborationMembersRequest(_VastuPropertiesCollaborationMembersRequestOptional):
    propertyId: str

class VastuPropertiesCollaborationMembersResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesCollaborationMembersData
    billing: VastuBilling

class _VastuPropertiesCollaborationCommentRequestOptional(TypedDict, total=False):
    ownerId: str

class VastuPropertiesCollaborationCommentRequest(_VastuPropertiesCollaborationCommentRequestOptional):
    propertyId: str
    assessmentId: str
    revision: str
    expectedContentHash: str
    text: str

class VastuPropertiesCollaborationCommentResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesCollaborationCommentData
    billing: VastuBilling

class _VastuPropertiesCollaborationReviewRequestOptional(TypedDict, total=False):
    ownerId: str

class VastuPropertiesCollaborationReviewRequest(_VastuPropertiesCollaborationReviewRequestOptional):
    propertyId: str
    assessmentId: str
    revision: str
    expectedContentHash: str
    decision: Literal["approved", "rejected"]

class VastuPropertiesCollaborationReviewResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesCollaborationReviewData
    billing: VastuBilling

class _VastuPropertiesCollaborationUpdateRequestOptional(TypedDict, total=False):
    ownerId: str

class VastuPropertiesCollaborationUpdateRequest(_VastuPropertiesCollaborationUpdateRequestOptional):
    propertyId: str
    revision: str
    expectedContentHash: str
    title: str
    data: Dict[str, VastuJsonValue]

class VastuPropertiesCollaborationUpdateResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesCollaborationUpdateData
    billing: VastuBilling

class _VastuPropertiesActivityListRequestOptional(TypedDict, total=False):
    ownerId: str
    cursor: int
    limit: int

class VastuPropertiesActivityListRequest(_VastuPropertiesActivityListRequestOptional):
    propertyId: str

class VastuPropertiesActivityListResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesActivityListData
    billing: VastuBilling

class _VastuPropertiesActivityExportRequestOptional(TypedDict, total=False):
    ownerId: str
    cursor: int
    limit: int

class VastuPropertiesActivityExportRequest(_VastuPropertiesActivityExportRequestOptional):
    propertyId: str

class VastuPropertiesActivityExportResponse(TypedDict):
    success: Literal[True]
    data: VastuPropertiesActivityExportData
    billing: VastuBilling

class _VastuPropertiesGetRequestAttribution(TypedDict, total=False):
    tenantRef: str

class VastuPropertiesGetRequest(_VastuPropertiesGetRequestAttribution):
    propertyId: str

class _VastuPropertiesListRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    limit: int
    cursor: str

class VastuPropertiesListRequest(_VastuPropertiesListRequestOptional):
    pass

class _VastuPropertiesDeleteRequestAttribution(TypedDict, total=False):
    tenantRef: str

class VastuPropertiesDeleteRequest(_VastuPropertiesDeleteRequestAttribution):
    propertyId: str

class _VastuPropertiesLinkScanRequestOptional(TypedDict, total=False):
    tenantRef: str
    addScanIds: List[str]
    addAssessmentIds: List[str]
    replace: bool

class VastuPropertiesLinkScanRequest(_VastuPropertiesLinkScanRequestOptional):
    propertyId: str

class _VastuArchiveTierRequestOptional(TypedDict, total=False):
    tenantRef: str
    preview: bool

class VastuArchiveTierRequest(_VastuArchiveTierRequestOptional):
    propertyId: str
    months: int

class _VastuArchiveExportRequestAttribution(TypedDict, total=False):
    tenantRef: str

class VastuArchiveExportRequest(_VastuArchiveExportRequestAttribution):
    propertyId: str

class _VastuArchiveDeleteRequestAttribution(TypedDict, total=False):
    tenantRef: str

class VastuArchiveDeleteRequest(_VastuArchiveDeleteRequestAttribution):
    propertyId: str
    confirmPropertyId: str

class _VastuArchiveSummaryRequestAttribution(TypedDict, total=False):
    tenantRef: str

class VastuArchiveSummaryRequest(_VastuArchiveSummaryRequestAttribution):
    propertyId: str

class VastuFeedListingsRequestRowsItemPlanAsset(TypedDict):
    kind: Literal["url", "uploadId"]
    value: str

class _VastuFeedListingsRequestRowsItemOptional(TypedDict, total=False):
    address: Optional[str]
    city: Optional[str]
    bearingDeg: Optional[float]
    planAsset: Optional[VastuFeedListingsRequestRowsItemPlanAsset]
    retentionDays: int

class VastuFeedListingsRequestRowsItem(_VastuFeedListingsRequestRowsItemOptional):
    externalId: str
    revision: str
    project: str
    building: str
    unit: str
    floor: str
    title: str

class _VastuFeedListingsRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    csv: str
    rows: List[VastuFeedListingsRequestRowsItem]
    dryRun: bool
    skipDuplicates: bool

class VastuFeedListingsRequest(_VastuFeedListingsRequestOptional):
    pass

class _VastuQuoteCalculateRequestOperationsItemOptional(TypedDict, total=False):
    quantity: int
    label: str

class VastuQuoteCalculateRequestOperationsItem(_VastuQuoteCalculateRequestOperationsItemOptional):
    op: str

class _VastuQuoteCalculateRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    workflowId: str
    operations: List[VastuQuoteCalculateRequestOperationsItem]
    retentionMonths: int
    retentionStoredBytes: int

class VastuQuoteCalculateRequest(_VastuQuoteCalculateRequestOptional):
    pass

class _VastuPropertiesCreateResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuPropertiesCreateResponse(_VastuPropertiesCreateResponseOptional):
    success: Literal[True]
    data: VastuPropertiesCreateData

class _VastuPropertiesUpdateResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuPropertiesUpdateResponse(_VastuPropertiesUpdateResponseOptional):
    success: Literal[True]
    data: VastuPropertiesUpdateData

class _VastuPropertiesGetResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuPropertiesGetResponse(_VastuPropertiesGetResponseOptional):
    success: Literal[True]
    data: VastuPropertiesGetData

class _VastuPropertiesListResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuPropertiesListResponse(_VastuPropertiesListResponseOptional):
    success: Literal[True]
    data: VastuPropertiesListData

class _VastuPropertiesDeleteResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuPropertiesDeleteResponse(_VastuPropertiesDeleteResponseOptional):
    success: Literal[True]
    data: VastuPropertiesDeleteData

class _VastuPropertiesLinkScanResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuPropertiesLinkScanResponse(_VastuPropertiesLinkScanResponseOptional):
    success: Literal[True]
    data: VastuPropertiesLinkScanData

class _VastuArchiveTierResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuArchiveTierResponse(_VastuArchiveTierResponseOptional):
    success: Literal[True]
    data: VastuArchiveTierData

class _VastuArchiveExportResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuArchiveExportResponse(_VastuArchiveExportResponseOptional):
    success: Literal[True]
    data: VastuArchiveExportData

class _VastuArchiveDeleteResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuArchiveDeleteResponse(_VastuArchiveDeleteResponseOptional):
    success: Literal[True]
    data: VastuArchiveDeleteData

class _VastuArchiveSummaryResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuArchiveSummaryResponse(_VastuArchiveSummaryResponseOptional):
    success: Literal[True]
    data: VastuArchiveSummaryData

class _VastuFeedListingsResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuFeedListingsResponse(_VastuFeedListingsResponseOptional):
    success: Literal[True]
    data: VastuFeedListingsData

class _VastuQuoteCalculateResponseOptional(TypedDict, total=False):
    billing: VastuCommerceBilling
    changed: bool
    preview: bool

class VastuQuoteCalculateResponse(_VastuQuoteCalculateResponseOptional):
    success: Literal[True]
    data: VastuQuoteCalculateData


class _VastuPlanImportDxfRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    maxChargeUsd: str
    fileName: str
    contentType: str
    trueNorthDeg: float
    unitsOverride: int
    layerRoles: Dict[str, str]

class VastuPlanImportDxfRequest(_VastuPlanImportDxfRequestOptional):
    dxf: str

class VastuPlanImportDxfResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanImportDxfData
    billing: VastuBilling
    meta: VastuMeta

class _VastuPlanExportIfcRequestOptional(TypedDict, total=False):
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    outputUnits: Literal["m", "ft", "mm", "in"]
    maxChargeUsd: str
class VastuPlanExportIfcRequest(_VastuPlanExportIfcRequestOptional):
    plan: Dict[str, VastuJsonValue]
class VastuPlanConvertUnitsRequest(TypedDict):
    plan: Dict[str, VastuJsonValue]
    inputUnits: Literal["m", "ft", "mm", "in"]
    outputUnits: Literal["m", "ft", "mm", "in"]
class VastuPlanExportIfcResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanExportIfcData
    billing: VastuBilling
class VastuPlanConvertUnitsResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanConvertUnitsData
    billing: VastuBilling

class _VastuPlanExportDxfRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    outputUnits: Literal["m", "ft", "mm", "in"]
    maxChargeUsd: str
    analysis: Dict[str, VastuJsonValue]
    zones: Literal[8, 16, 32]
    unitsCode: int
    trueNorthDeg: float

class VastuPlanExportDxfRequest(_VastuPlanExportDxfRequestOptional):
    plan: Dict[str, VastuJsonValue]

class VastuPlanExportDxfResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanExportDxfData
    billing: VastuBilling
    meta: VastuMeta

class _VastuPlanImportIfcRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str
    holes: List[List[List[float]]]
    multipolygons: List[Dict[str, VastuJsonValue]]
    units: Literal["m", "ft", "mm", "in"]
    inputUnits: Literal["m", "ft", "mm", "in"]
    maxChargeUsd: str
    trueNorthDeg: float

class VastuPlanImportIfcRequest(_VastuPlanImportIfcRequestOptional):
    ifc: str

class VastuPlanImportIfcResponse(TypedDict):
    success: Literal[True]
    data: VastuPlanImportIfcData
    billing: VastuBilling
    meta: VastuMeta

VastuAnyResponse = Union[VastuDrawingSheetResponse, VastuRemediationTasksUpsertResponse, VastuRemediationTasksListResponse, VastuRemediationTasksDeleteResponse, VastuRemediationReassessResponse, VastuMerchantCatalogUploadResponse, VastuMerchantCatalogGetResponse, VastuMerchantCatalogDeleteResponse, VastuMerchantRemediesResponse, VastuPlanImportDxfResponse, VastuPlanExportDxfResponse, VastuPlanImportIfcResponse, VastuJobsResponse, VastuScansTimelapseResponse, VastuScansDeleteResponse, VastuArAttestationChallengeResponse, VastuScansListResponse, VastuScansRetrieveResponse, VastuScansSaveResponse, VastuArDeityIconsResponse, VastuArRoomCaptureResponse, VastuArYantraMeshesResponse, VastuArZoneTexturesResponse, VastuArAnchorRecommendationsResponse, VastuArHeatmapRasterResponse, VastuAssessmentsBatchResponse, VastuArScanQualityResponse, VastuArTrueNorthCalibrateResponse, VastuAssessmentsResponse, VastuAuditFloorPlanResponse, VastuAuditFloorPlanDetailedResponse, VastuAuditSingleRoomResponse, VastuCompareBeforeAfterRemedyResponse, VastuCompoundWallAnalysisResponse, VastuDirectionAuspiciousFacingResponse, VastuDirectionCorrectResponse, VastuDirectionDeclinationResponse, VastuDirectionSunPathResponse, VastuDirectionZoneFromBearingResponse, VastuElementsBalanceSuggestResponse, VastuElementsDistributionResponse, VastuEntranceObstructionCheckResponse, VastuEntrancePadaResponse, VastuEntranceRecommendResponse, VastuFloorLevelAnalysisResponse, VastuFusionChartResponse, VastuMandalaProject81PadaResponse, VastuMandalaProject9ZoneResponse, VastuMandalaProjectBrahmasthanResponse, VastuMultiStoreyFloorRulesResponse, VastuPlacementBalconyResponse, VastuPlacementBorewellResponse, VastuPlacementGardenResponse, VastuPlacementGeneratorElectricalResponse, VastuPlacementMainGateResponse, VastuPlacementOverheadTankResponse, VastuPlacementSepticTankResponse, VastuPlacementTreeResponse, VastuPlacementWellResponse, VastuPlacementWindowResponse, VastuPlanAnalyzeResponse, VastuPlanFromRequirementsResponse, VastuPlanGenerateResponse, VastuPlanOptimizeResponse, VastuPlanReportResponse, VastuPlanUploadResponse, VastuPlotExtensionsCutsResponse, VastuPlotOrientationResponse, VastuPlotRatioResponse, VastuPlotRoadOrientationResponse, VastuPlotShapeResponse, VastuPlotSlopeResponse, VastuReferenceColorsByZoneResponse, VastuReferenceDefectsCatalogResponse, VastuReferenceDirections16Response, VastuReferenceDirections32Response, VastuReferenceDirections8Response, VastuReferenceGateObstructionsResponse, VastuReferenceMandala45DevatasResponse, VastuReferenceMandala64PadaResponse, VastuReferenceMandala9ZoneResponse, VastuReferenceMaterialsByZoneResponse, VastuReferenceRemediesCatalogResponse, VastuRoomBedroomResponse, VastuRoomDiningResponse, VastuRoomKitchenResponse, VastuRoomLivingResponse, VastuRoomPoojaResponse, VastuRoomStaircaseResponse, VastuRoomStoreResponse, VastuRoomStudyResponse, VastuRoomToiletResponse, VastuRoomWaterStorageResponse, VastuScoreComplianceIndexResponse, VastuScoreOverallResponse, VastuScoreZoneWiseResponse, VastuSpecializedCommercialResponse, VastuSpecializedEducationalResponse, VastuSpecializedFactoryResponse, VastuSpecializedHospitalResponse, VastuSpecializedResidentialResponse, VastuSpecializedRestaurantResponse, VastuSpecializedTempleResponse, VastuTimingBhumiPujanResponse, VastuTimingConstructionStartResponse, VastuTimingGrihapraveshResponse, VastuTimingVastuShantiResponse]
VastuResponse = VastuAnyResponse


def _offset_from_datetime(dt):
    """Extract UTC offset ('+05:30' / 'Z') from an ISO datetime, else None."""
    import re
    m = re.search(r'([+-]\d{2}:?\d{2}|Z)$', dt or '')
    return m.group(1) if m else None

def _v2_payload(result):
    """Unwrap a V2 envelope response ({success, data, billing, meta}) to its
    payload. V2 endpoints (Jun 2026 route migration) wrap the body; the legacy
    typed models predate that. Callers attach the full payload to the returned
    model as `.raw` so no field is ever lost to a model-shape mismatch.

    TS->Rust transition tolerance (3.0.6): recognise the envelope by the
    load-bearing ``success`` + ``data`` (object) signature that BOTH engines
    share, rather than blindly returning any top-level ``data`` key. The cutover
    aligns Rust v2 responses to the live TS contract, but ``billing`` may be
    absent (moved into ``meta`` or omitted on free/idempotent paths), so we do
    NOT require it. A bare reading payload that itself happens to carry a
    ``data`` field (without ``success: True``) is now left untouched, which
    fixes the previous over-eager unwrap.
    """
    if isinstance(result, dict) and isinstance(result.get("data"), dict):
        # Treat as an envelope when ANY canonical envelope marker is present.
        # This stays tolerant whether the engine sends success/billing/meta or
        # just success, while not unwrapping a bare reading that incidentally
        # carries a nested `data` block with no envelope markers around it.
        if ("success" in result) or ("billing" in result) or ("meta" in result):
            return result["data"]
    return result


def _is_vedika_host(host):
    """Legacy domain classifier; not the credential-routing authority.

    Since 3.0.8 the constructor requires the exact official API origin.
    Retained for historical compatibility; its broader result cannot
    authorize another Vedika subdomain.

    Matching is on the registrable name, never a bare string suffix.
    ``notvedika.io`` ends with "vedika.io" but is a different site and must be
    rejected; ``api.vedika.io.attacker.com`` merely starts with ours. A trailing
    dot is the absolute form of the same name, so it is normalised away rather
    than rejected."""
    if not host:
        return False
    h = host.strip("[]").lower().rstrip(".")
    return h == "vedika.io" or h.endswith(".vedika.io")


def _is_loopback_host(host):
    """True only for genuine loopback: the literal ``localhost`` or a loopback IP
    (127.0.0.0/8, ::1). A DNS name that merely starts with "127." (e.g.
    ``127.attacker.invalid``) is NOT loopback and must not bypass the policy."""
    if not host:
        return False
    import ipaddress
    host = host.strip("[]")
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class _VedikaSession(requests.Session):
    """A requests.Session that never follows a redirect.

    Stripping auth headers on a redirect is not enough: a 307 or 308 resends
    the private JSON body, and the retained ``Idempotency-Key``, to whatever
    origin the 3xx names. So every request made through this session is sent
    with ``allow_redirects=False`` (ordinary, streaming and voice alike, since
    all of them go through ``send``), the 3xx comes back as the response, and
    the client turns it into a ``VedikaAPIError``. No second request is made.
    """

    def send(self, request, **kwargs):
        kwargs["allow_redirects"] = False
        return super().send(request, **kwargs)


def _refuse_redirect(response):
    """Raise for any 3xx: it is never followed, so nothing is forwarded."""
    if 300 <= response.status_code < 400:
        raise VedikaAPIError(
            f"Unexpected redirect (HTTP {response.status_code}) not followed; credentials and the "
            "request body were not forwarded. Check base_url.",
            status_code=response.status_code,
        )


_IDEMPOTENCY_HEADER_NAMES = ("idempotency-key", "x-idempotency-key", "x-request-id")
_NO_IDEMPOTENCY = {"Idempotency-Key": None, "X-Idempotency-Key": None, "X-Request-Id": None}
_RETRY_SAFE_METHODS = frozenset(["GET", "HEAD", "OPTIONS", "DELETE", "PUT"])
_RETRYABLE_SERVER_STATUSES = frozenset([500, 502, 503, 504])
# 429 codes that a short wait cannot fix: the allowance resets later, so a retry
# only burns calls. Anything else on a 429 is treated as a per-minute limit.
_NON_RETRYABLE_429_CODES = frozenset(["DAILY_LIMIT_EXCEEDED", "PLAN_LIMIT_EXCEEDED"])


def _number(value):
    """A finite non-negative float from a JSON number or numeric string, else None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    return number if number == number and number not in (float("inf"), float("-inf")) and number >= 0 else None


def _error_body(response):
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _error_code(body):
    code = body.get("code")
    error = body.get("error")
    if not isinstance(code, str) and isinstance(error, dict):
        code = error.get("code")
    return code if isinstance(code, str) and code else None


def _retry_after_seconds(response, body):
    """Seconds to wait from the 429/503 body ``retryAfter`` or the Retry-After header."""
    value = _number(body.get("retryAfter"))
    if value is None:
        error = body.get("error")
        value = _number(error.get("retryAfter")) if isinstance(error, dict) else None
    if value is None:
        value = _number(response.headers.get("Retry-After"))
    return value


def _raise_api_error(response, api_key):
    """Raise the typed SDK exception for a >= 400 response (never retries)."""
    status = response.status_code
    body = _error_body(response)
    code = _error_code(body)
    error = body.get("error")
    message = next((value for value in (
        body.get("message"), error,
        error.get("message") if isinstance(error, dict) else None,
    ) if isinstance(value, str) and value.strip()), None)
    if message is not None:
        message = message.replace(api_key, "[REDACTED]")
    if status == 401:
        raise AuthenticationError("Invalid API key", code=code)
    if status == 402:
        if code == "SUBSCRIPTION_EXPIRED":
            raise SubscriptionExpiredError(message or "Subscription expired", code=code)
        wallet = body.get("wallet")
        if not isinstance(wallet, dict):
            wallet = {}
        purchase_url = body.get("purchaseUrl")
        raise InsufficientCreditsError(
            message or "Payment required",
            code=code,
            required=_number(wallet.get("required")),
            available=_number(wallet.get("available")),
            deficit=_number(wallet.get("deficit")),
            purchase_url=purchase_url if isinstance(purchase_url, str) else None,
        )
    if status == 429:
        retry_after = _retry_after_seconds(response, body)
        if code in _NON_RETRYABLE_429_CODES:
            raise DailyLimitError(message or "Daily call limit reached", code=code, retry_after=retry_after)
        raise RateLimitError(message or "Rate limit exceeded. Please wait a moment.", code=code, retry_after=retry_after)
    if status == 422:
        raise ValidationError(message or "Invalid input", code=code)
    raise VedikaAPIError(message or "API request failed", status_code=status, code=code)


_BODY_IDENTITY_SCAN_OPS = frozenset({"save", "retrieve", "list", "delete", "timelapse"})


def _uses_body_identity(endpoint):
    """True for the scan operations whose retry identity lives in the JSON body."""
    path = endpoint.split("?", 1)[0]
    for prefix in ("/v2/vastu/scans/", "/v2/astrology/vastu/scans/"):
        if path.startswith(prefix):
            return path[len(prefix):] in _BODY_IDENTITY_SCAN_OPS
    return False


class _VastuPortfolioSearchRequestOptional(TypedDict, total=False):
    city: str
    tags: List[str]
    minScore: int
    maxScore: int
    zoneDefects: List[str]
    ruleset: str
    inputSource: str
    sort: str
    limit: int
    cursor: str

class VastuPortfolioSearchRequest(_VastuPortfolioSearchRequestOptional):
    pass

class VastuPortfolioSearchResponse(TypedDict):
    success: bool
    data: VastuPortfolioSearchData
    billing: Dict[str, str]

class _VastuPortfolioCompareRequestOptional(TypedDict, total=False):
    pass

class VastuPortfolioCompareRequest(_VastuPortfolioCompareRequestOptional):
    propertyIds: List[str]

class VastuPortfolioCompareResponse(TypedDict):
    success: bool
    data: VastuPortfolioCompareData
    billing: Dict[str, str]

class _VastuPortfolioAnalyticsRequestOptional(TypedDict, total=False):
    fromEpoch: int
    toEpoch: int
    tag: str
    propertyId: str
    tenantRef: str

class VastuPortfolioAnalyticsRequest(_VastuPortfolioAnalyticsRequestOptional):
    pass

class VastuPortfolioAnalyticsResponse(TypedDict):
    success: bool
    data: VastuPortfolioAnalyticsData
    billing: Dict[str, str]

class _VastuPortfolioUsageRequestOptional(TypedDict, total=False):
    fromEpoch: int
    toEpoch: int
    tag: str
    propertyId: str
    tenantRef: str

class VastuPortfolioUsageRequest(_VastuPortfolioUsageRequestOptional):
    pass

class VastuPortfolioUsageResponse(TypedDict):
    success: bool
    data: VastuPortfolioUsageData
    billing: Dict[str, str]

class _VastuPortfolioUsageExportRequestOptional(TypedDict, total=False):
    fromEpoch: int
    toEpoch: int
    tag: str
    propertyId: str
    tenantRef: str

class VastuPortfolioUsageExportRequest(_VastuPortfolioUsageExportRequestOptional):
    pass

class VastuPortfolioUsageExportResponse(TypedDict):
    success: bool
    data: VastuPortfolioUsageExportData
    billing: Dict[str, str]

class _VastuPortfolioBudgetsSetRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuPortfolioBudgetsSetRequest(_VastuPortfolioBudgetsSetRequestOptional):
    capUsd: Optional[str]

class VastuPortfolioBudgetsSetResponse(TypedDict):
    success: bool
    data: VastuPortfolioBudgetsSetData
    billing: Dict[str, str]

class _VastuPortfolioBudgetsGetRequestOptional(TypedDict, total=False):
    propertyId: str
    tenantRef: str

class VastuPortfolioBudgetsGetRequest(_VastuPortfolioBudgetsGetRequestOptional):
    pass

class VastuPortfolioBudgetsGetResponse(TypedDict):
    success: bool
    data: VastuPortfolioBudgetsGetData
    billing: Dict[str, str]


class VedikaClient:
    """
    Main client for the Vedika Astrology API.

    The ONLY B2B astrology API with AI-powered chatbot queries.

    Args:
        api_key: Your Vedika API key (get one at https://vedika.io/dashboard.html)
        base_url: API base URL (default: production URL). Must be a bare
            ``https://api.vedika.io`` origin on its default port,
            or HTTP loopback for local development. Anything else raises
            ``ValueError`` at construction: pointing the client at a host we do
            not operate sends your live API key there on the first request, so
            it is treated as a credential leak rather than a configuration
            choice. To route through your own gateway, proxy server-side and
            keep the key on your server.
        timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum number of retries for failed requests (default: 3)
        cache_enabled: Enable prompt caching for cost savings (default: True)
        language: Default language for responses (default: "en")
        max_retry_wait: Longest pause in seconds the client takes between
            retries (default: 60). A rate limit that asks for a longer wait is
            raised as ``RateLimitError`` instead of being slept on.
        allow_insecure_http: Deprecated and inert. It formerly permitted the API
            key to travel in cleartext to a remote host. Passing ``True`` with a
            non-loopback ``base_url`` now raises rather than silently doing
            nothing, so a caller who thinks they opted in is told they did not.

    Example:
        >>> from vedika import VedikaClient
        >>> client = VedikaClient(api_key="vk_live_...")
        >>> response = client.ask_question(
        ...     question="What are my career prospects?",
        ...     birth_details={"datetime": "1990-06-15T14:30:00+05:30", ...}
        ... )
    """

    VASTU_OPERATIONS = tuple(operation.value for operation in VastuOperation)
    VASTU_OPERATION_CONTRACTS = _VASTU_OPERATION_CONTRACTS

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.vedika.io",
        timeout: int = 60,
        max_retries: int = 3,
        cache_enabled: bool = True,
        language: str = "en",
        allow_insecure_http: bool = False,
        max_retry_wait: float = 60.0,
    ):
        self.api_key = api_key or os.getenv("VEDIKA_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Get one at https://vedika.io/dashboard.html"
            )

        self.base_url = base_url.rstrip("/")

        # Validate before creating a session that holds credential headers.
        # The legacy allow_insecure_http argument cannot bypass this policy.
        from urllib.parse import urlparse
        try:
            parsed = urlparse(self.base_url)
            scheme = (parsed.scheme or "").lower()
            host = parsed.hostname
            port = parsed.port
        except ValueError:
            raise ValueError("Invalid base_url") from None
        # Reject embedded credentials / path / query / fragment: the URL
        # "https://api.vedika.io@attacker.invalid" parses with host
        # "attacker.invalid" but reads as api.vedika.io, so the Bearer API key
        # would ride to the attacker on the first request.
        if parsed.username or parsed.password:
            raise ValueError(
                "base_url must not contain embedded credentials (user:pass@host)"
            )
        if (parsed.path and parsed.path != "/") or parsed.query or parsed.fragment:
            raise ValueError(
                "base_url must be a bare origin (scheme://host[:port]) with no "
                "path, query, or fragment"
            )
        official = scheme == "https" and host == "api.vedika.io" and port in (None, 443)
        local = scheme == "http" and _is_loopback_host(host)
        if not (official or local):
            raise ValueError(
                "base_url must use https://api.vedika.io or loopback http://; "
                "custom origins are not allowed"
            )

        # Loopback never leaves the machine, so cleartext is fine there and local
        # development against a stub server keeps working without an escape hatch.
        if not _is_loopback_host(parsed.hostname):
            # Retain the Vedika domain guard beneath the stricter exact-origin
            # gate above. It cannot broaden the accepted destination set.
            if not _is_vedika_host(parsed.hostname):
                raise ValueError(
                    "base_url must be a Vedika origin (vedika.io or a "
                    "*.vedika.io subdomain) or loopback - refusing to send the "
                    "API key to %s://%s. To route requests through your own "
                    "gateway, proxy them server-side and keep the key there."
                    % (scheme, parsed.netloc)
                )
            if scheme != "https":
                raise ValueError(
                    "base_url must be https:// - refusing to send the API key "
                    "to %s in the clear." % parsed.netloc
                )

        # `allow_insecure_http` predates the origin policy above. It could only
        # ever have permitted one thing: the API key, in cleartext, to a remote
        # host. That is a credential leak rather than a configuration
        # preference, so it no longer has anything left to allow. The parameter
        # is still accepted so existing callers do not crash on an unexpected
        # keyword, but passing it where it would have mattered now fails loudly
        # instead of silently doing nothing - a caller who believes they opted
        # in deserves to be told they did not.
        if allow_insecure_http and not _is_loopback_host(parsed.hostname):
            raise ValueError(
                "allow_insecure_http no longer permits sending the API key over "
                "remote cleartext HTTP; it was a credential leak. Use https:// "
                "to a Vedika origin, or proxy server-side and keep the key there."
            )

        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self.max_retry_wait = float(max_retry_wait)
        self.cache_enabled = cache_enabled
        self.language = language

        # _VedikaSession never follows a redirect (see the class docstring).
        # Retries are NOT delegated to urllib3: its status retry swallowed the
        # typed 402/429 errors into a generic RetryError once attempts ran out,
        # slept on a daily-limit 429 and trusted an uncapped Retry-After. `_request`
        # runs the retry policy itself (see `_retry_delay`), so the adapter makes
        # exactly one attempt.
        self.session = _VedikaSession()
        adapter = HTTPAdapter(max_retries=0)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Authorization: Bearer is the documented credential and takes
        # precedence at the API. The key is sent once, not duplicated into
        # X-API-Key as well.
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"vedika-python-sdk/{__version__}"
        })

    def _retry_delay(self, response, attempt, retry_safe):
        """Seconds to wait before retrying this response, or None to give up.

        Policy (decided from the response body ``code``, never from the
        ``x-ratelimit-*`` headers, which describe the per-minute limiter even
        when another limiter refused the call):

        * 401, 402, 4xx other than 429: never retried.
        * 429 ``DAILY_LIMIT_EXCEEDED`` / ``PLAN_LIMIT_EXCEEDED``: never retried.
        * any other 429: refused before the call ran, so it is safe to resend.
          Waits the body ``retryAfter`` (or Retry-After), and gives up when
          that exceeds ``max_retry_wait``.
        * 500/502/503/504: retried only when resending cannot charge twice, that
          is GET/DELETE or a call that carries an idempotency key.
        """
        if attempt >= self.max_retries:
            return None
        status = response.status_code
        backoff = min(self.max_retry_wait, 0.5 * (2 ** attempt))
        if status == 429:
            body = _error_body(response)
            if _error_code(body) in _NON_RETRYABLE_429_CODES:
                return None
            wait = _retry_after_seconds(response, body)
            if wait is None:
                return backoff
            return wait if wait <= self.max_retry_wait else None
        if status in _RETRYABLE_SERVER_STATUSES and retry_safe:
            wait = _number(response.headers.get("Retry-After"))
            return min(self.max_retry_wait, wait) if wait is not None else backoff
        return None

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        idempotency_key: Optional[str] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to the API.

        Idempotency: a key is sent only when the caller passes one, or when the
        operation is listed as accepting one (``_idempotency``) and the caller
        set none. Any other operation answers 422 IDEMPOTENCY_NOT_SUPPORTED to a
        key and treats ``X-Request-Id`` as a key too, so none is generated.
        The key is created once per logical call and reused by every retry.
        """
        method = method.upper()
        url = f"{self.base_url}{endpoint}"
        path = endpoint.split("?", 1)[0]

        batch = path in (
            "/v2/vastu/assessments/batch", "/v2/astrology/vastu/assessments/batch",
            "/v2/vastu/jobs", "/v2/astrology/vastu/jobs",
        )
        if (batch or idempotency_key is not None) and (
            not isinstance(idempotency_key, str) or not idempotency_key.strip()
        ):
            raise ValueError("A nonblank caller-retained Idempotency-Key is required")

        # Scan save/retrieve/list/delete/timelapse carry their retry identity in
        # the body (scanId or requestId); the server answers 422 to any retry
        # header, including one set on the session, so all three are removed.
        body_identity = _uses_body_identity(endpoint)
        header_name = certified_header(method, path)
        headers: Optional[Dict[str, Any]] = None
        if body_identity:
            if idempotency_key is not None:
                raise ValueError(
                    "Scan operations use scanId or requestId in the body; do not pass an Idempotency-Key"
                )
            headers = dict(_NO_IDEMPOTENCY)
        elif idempotency_key is not None:
            headers = {header_name or "Idempotency-Key": idempotency_key}
        elif header_name is not None and not any(
            name.lower() in _IDEMPOTENCY_HEADER_NAMES for name in self.session.headers
        ):
            headers = {header_name: str(uuid.uuid4())}

        raw_body = None
        if files is not None:
            # Encode the multipart body ONCE. A retry that let requests encode it
            # again would pick a new boundary, so the same Idempotency-Key would
            # arrive with different bytes and read as a conflicting request.
            raw_body, content_type = requests.models.RequestEncodingMixin._encode_files(files, {})
            headers = {**(headers or {}), "Content-Type": content_type}

        keyed = not body_identity and (
            headers is not None and any(
                name.lower() in _IDEMPOTENCY_HEADER_NAMES and value for name, value in headers.items()
            ) or any(name.lower() in _IDEMPOTENCY_HEADER_NAMES for name in self.session.headers)
        )
        # A POST that carries no key is never resent after a 5xx or a timeout: the
        # first attempt may already have been charged. Scan operations dedupe on
        # the body identity, so they are safe to resend.
        retry_safe = method in _RETRY_SAFE_METHODS or keyed or body_identity
        attempt = 0
        key_dropped = False
        while True:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data if raw_body is None else None,
                    data=raw_body,
                    params=params,
                    timeout=self.timeout,
                    headers=headers,
                )
            except requests.exceptions.RequestException as exc:
                if retry_safe and attempt < self.max_retries:
                    time.sleep(min(self.max_retry_wait, 0.5 * (2 ** attempt)))
                    attempt += 1
                    continue
                if isinstance(exc, requests.exceptions.Timeout):
                    raise VedikaAPIError("Request timed out. For complex queries, try increasing timeout.") from None
                raise VedikaAPIError("Request failed. Check the connection and retry.") from None

            _refuse_redirect(response)
            if response.status_code < 400:
                return response.json()

            body = _error_body(response)
            if (
                response.status_code == 422
                and _error_code(body) == "IDEMPOTENCY_NOT_SUPPORTED"
                and keyed and not key_dropped
            ):
                # Not certified for idempotency and no charge was attempted:
                # resend once without any key. With no key the call is no longer
                # safe to resend on 5xx or timeouts.
                headers = {**(headers or {}), **_NO_IDEMPOTENCY}
                key_dropped = True
                keyed = False
                retry_safe = method in _RETRY_SAFE_METHODS or body_identity
                continue

            delay = self._retry_delay(response, attempt, retry_safe)
            if delay is None:
                _raise_api_error(response, self.api_key)
            time.sleep(delay)
            attempt += 1

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        """Call any API operation, with the client's auth, retry and error handling.

        Use it for operations that have no named method yet. ``path`` is a path on
        the API origin, for example ``"/v2/astrology/kundli"``; a full URL is
        refused so the API key can only travel to ``base_url``. Returns the
        decoded JSON body, or raises the same typed errors as the named methods.

        Pass ``idempotency_key`` only for operations that document an idempotency
        header; the client sends it unchanged on every retry of this call.
        """
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//") or "://" in path or "\\" in path:
            raise ValueError("path must be a path on the API origin such as '/v2/astrology/kundli'")
        return self._request(
            method, path, data=json, params=params, idempotency_key=idempotency_key
        )

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
            speed: Delivery tier — "standard" (default), "fast", or "eco". ("quality"
                was never an accepted value; the API rejects it.) An "eco" request on a
                deploy without the Eco engine fails closed with a masked 503
                ECO_UNAVAILABLE before any wallet debit, so it is never charged.
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

    def ask_vastu_report(
        self,
        question: str,
        report: Optional[Dict[str, Any]] = None,
        *,
        report_ref: Optional[Dict[str, str]] = None,
        conversation_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: Optional[str] = None,
    ) -> QuestionResponse:
        """
        Ask a question about a Vastu report you already hold.

        Pass either ``report`` (the report body) or ``report_ref`` (an uploaded
        report PDF: ``{"type": "upload", "id": upload["uploadId"]}`` from
        ``upload_vastu_report``), never both.

        Pass the body returned by plan/analyze, plan/report, plan/generate,
        audit or score endpoints (up to 64 KB; drop ``svg``). Birth details are
        not needed. On a follow-up, pass ``conversation_id`` and omit
        ``report``; the conversation's saved report is reused.

        Returns:
            QuestionResponse whose ``vastu_context`` lists the report rows the
            answer may cite and the ones it did cite.

        Example:
            >>> report = client.vastu("plan/analyze", {...})
            >>> first = client.ask_vastu_report("What should I fix first?", report)
            >>> client.ask_vastu_report("And the kitchen?",
            ...                         conversation_id=first.conversation_id)
        """
        if report is not None and report_ref is not None:
            raise ValueError("ask_vastu_report takes exactly one of report or report_ref, not both")
        if report_ref is not None and not (
            isinstance(report_ref, Mapping)
            and report_ref.get("type") == "upload"
            and isinstance(report_ref.get("id"), str)
            and _VASTU_UPLOAD_ID.match(report_ref["id"])
        ):
            raise ValueError('report_ref must be {"type": "upload", "id": "vup_..."} from upload_vastu_report')
        if report is None and report_ref is None and not conversation_id:
            raise ValueError("ask_vastu_report needs a report, a report_ref or a conversation_id that already holds one")
        data: Dict[str, Any] = {"question": question, "language": language or self.language}
        if report is not None:
            data["vastuContext"] = {"report": report}
        if report_ref is not None:
            data["vastuContext"] = {"reportRef": {"type": report_ref["type"], "id": report_ref["id"]}}
        if conversation_id is not None:
            data["conversationId"] = conversation_id
        if speed is not None:
            data["speed"] = speed
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

        # Route through self.session (a _VedikaSession) so redirects are never
        # followed — a top-level requests.post() would follow a 307 and resend
        # the private body to another origin.
        with self.session.post(url, json=data, stream=True, timeout=self.timeout) as response:
            _refuse_redirect(response)
            if response.status_code >= 400:
                _raise_api_error(response, self.api_key)
            if response.status_code != 200:
                raise VedikaAPIError(f"Stream request failed: HTTP {response.status_code}", status_code=response.status_code)

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
    # Vastu (98 logical operations, mounted under two public aliases)
    # Mirrors sdks/flutter's Vastu surface. Vastu takes a BUILDING (plot
    # polygon, room list, compass zone) — NEVER a birth chart. Every path
    # below is pinned to the 82 mounted logical routes in vedika-v2/src/vastu.rs.
    # ═══════════════════════════════════════════

    def vastu_plan_import_image(self, params: VastuPlanImportImageRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanImportImageResponse:
        return cast(VastuPlanImportImageResponse, self.vastu("plan/import-image", dict(params), idempotency_key=idempotency_key))

    def vastu_plan_import_pdf(self, params: VastuPlanImportPdfRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanImportPdfResponse:
        return cast(VastuPlanImportPdfResponse, self.vastu("plan/import-pdf", dict(params), idempotency_key=idempotency_key))

    def vastu(self, op: str, params: Dict[str, Any], *, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Any Vastu operation by its path suffix under `/v2/astrology/vastu/`.

        Generic escape hatch for the long tail of the 82-operation surface.
        Vastu takes a BUILDING (plot polygon, rooms, compass zone), never a
        birth chart.

        Args:
            op: Path suffix, e.g. "score/overall", "room/kitchen",
                "audit/floor-plan". A leading slash is stripped.
            params: Building/plot/room payload (NOT birth_details)

        Example:
            >>> client.vastu("score/overall", {"rooms": [...], "plot": {...}})
        """
        path = op.lstrip("/")
        if path.startswith("jobs/"):
            job = _VASTU_JOB_PATH.match(path)
            if not job:
                raise ValueError("Job paths are jobs/{job_id}, jobs/{job_id}/results and jobs/{job_id}/cancel")
            _vastu_job_id(job.group(1))
        # reference/* tables (11, incl. gate-obstructions) are GET-only
        # (POST -> 405); direction/declination is a GET+POST dual whose
        # verified path is GET-with-query; jobs/{id} and jobs/{id}/results are
        # GET. Everything else is POST. Mirrors vedika-v2/src/vastu.rs GET/dual
        # route sets and the job routes in vastu_jobs.rs.
        if _is_vastu_get_path(path):
            return self._request(
                "GET", f"/v2/astrology/vastu/{path}", params=params, idempotency_key=idempotency_key
            )
        return self._request(
            "POST", f"/v2/astrology/vastu/{path}", data=params, idempotency_key=idempotency_key
        )

    def vastu_portfolio_search(self, params: VastuPortfolioSearchRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioSearchResponse:
        return self.vastu_operation(VastuOperation.PORTFOLIO_SEARCH, params, idempotency_key=idempotency_key)

    def vastu_portfolio_compare(self, params: VastuPortfolioCompareRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioCompareResponse:
        return self.vastu_operation(VastuOperation.PORTFOLIO_COMPARE, params, idempotency_key=idempotency_key)

    def vastu_portfolio_analytics(self, params: VastuPortfolioAnalyticsRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioAnalyticsResponse:
        return self.vastu_operation(VastuOperation.PORTFOLIO_ANALYTICS, params, idempotency_key=idempotency_key)

    def vastu_portfolio_usage(self, params: VastuPortfolioUsageRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioUsageResponse:
        return self.vastu_operation(VastuOperation.PORTFOLIO_USAGE, params, idempotency_key=idempotency_key)

    def vastu_portfolio_usage_export(self, params: VastuPortfolioUsageExportRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioUsageExportResponse:
        return self.vastu_operation(VastuOperation.PORTFOLIO_USAGE_EXPORT, params, idempotency_key=idempotency_key)

    def vastu_portfolio_budgets_set(self, params: VastuPortfolioBudgetsSetRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioBudgetsSetResponse:
        return self.vastu_operation(VastuOperation.PORTFOLIO_BUDGETS_SET, params, idempotency_key=idempotency_key)

    def vastu_portfolio_budgets_get(self, params: VastuPortfolioBudgetsGetRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioBudgetsGetResponse:
        return self.vastu_operation(VastuOperation.PORTFOLIO_BUDGETS_GET, params, idempotency_key=idempotency_key)
    def vastu_drawing_sheet(self, params: VastuDrawingSheetRequest, *, idempotency_key: Optional[str] = None) -> VastuDrawingSheetResponse:
        return cast(VastuDrawingSheetResponse, self._request("POST", "/v2/vastu/report/drawing-sheet", data=dict(params), idempotency_key=idempotency_key))

    def vastu_workspace(self, operation: Literal["properties", "jobs", "get", "list", "reset", "webhook", "report"], params: Optional[VastuWorkspaceRequest] = None) -> VastuWorkspaceResponse:
        if operation not in ("properties", "jobs", "get", "list", "reset", "webhook", "report"):
            raise ValueError("Unknown workspace operation")
        return cast(VastuWorkspaceResponse, self._request("POST", f"/sandbox/v2/vastu/workspace/{operation}", data=dict(params or {})))

    def vastu_properties_create(self, params: VastuPropertiesCreateRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCreateResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_CREATE, params, idempotency_key=idempotency_key)

    def vastu_properties_update(self, params: VastuPropertiesUpdateRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesUpdateResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_UPDATE, params, idempotency_key=idempotency_key)

    def vastu_properties_collaboration_get(self, params: VastuPropertiesCollaborationGetRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationGetResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_COLLABORATION_GET, params, idempotency_key=idempotency_key)

    def vastu_properties_collaboration_invite(self, params: VastuPropertiesCollaborationInviteRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationInviteResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_COLLABORATION_INVITE, params, idempotency_key=idempotency_key)

    def vastu_properties_collaboration_revoke(self, params: VastuPropertiesCollaborationRevokeRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationRevokeResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_COLLABORATION_REVOKE, params, idempotency_key=idempotency_key)

    def vastu_properties_collaboration_members(self, params: VastuPropertiesCollaborationMembersRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationMembersResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_COLLABORATION_MEMBERS, params, idempotency_key=idempotency_key)

    def vastu_properties_collaboration_comment(self, params: VastuPropertiesCollaborationCommentRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationCommentResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_COLLABORATION_COMMENT, params, idempotency_key=idempotency_key)

    def vastu_properties_collaboration_review(self, params: VastuPropertiesCollaborationReviewRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationReviewResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_COLLABORATION_REVIEW, params, idempotency_key=idempotency_key)

    def vastu_properties_collaboration_update(self, params: VastuPropertiesCollaborationUpdateRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationUpdateResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_COLLABORATION_UPDATE, params, idempotency_key=idempotency_key)

    def vastu_properties_activity_list(self, params: VastuPropertiesActivityListRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesActivityListResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_ACTIVITY_LIST, params, idempotency_key=idempotency_key)

    def vastu_properties_activity_export(self, params: VastuPropertiesActivityExportRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesActivityExportResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_ACTIVITY_EXPORT, params, idempotency_key=idempotency_key)

    def vastu_properties_get(self, params: VastuPropertiesGetRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesGetResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_GET, params, idempotency_key=idempotency_key)

    def vastu_properties_list(self, params: VastuPropertiesListRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesListResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_LIST, params, idempotency_key=idempotency_key)

    def vastu_properties_delete(self, params: VastuPropertiesDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesDeleteResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_DELETE, params, idempotency_key=idempotency_key)

    def vastu_properties_link_scan(self, params: VastuPropertiesLinkScanRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesLinkScanResponse:
        return self.vastu_operation(VastuOperation.PROPERTIES_LINK_SCAN, params, idempotency_key=idempotency_key)

    def vastu_archive_tier(self, params: VastuArchiveTierRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveTierResponse:
        return self.vastu_operation(VastuOperation.ARCHIVE_TIER, params, idempotency_key=idempotency_key)

    def vastu_archive_export(self, params: VastuArchiveExportRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveExportResponse:
        return self.vastu_operation(VastuOperation.ARCHIVE_EXPORT, params, idempotency_key=idempotency_key)

    def vastu_archive_delete(self, params: VastuArchiveDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveDeleteResponse:
        return self.vastu_operation(VastuOperation.ARCHIVE_DELETE, params, idempotency_key=idempotency_key)

    def vastu_archive_summary(self, params: VastuArchiveSummaryRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveSummaryResponse:
        return self.vastu_operation(VastuOperation.ARCHIVE_SUMMARY, params, idempotency_key=idempotency_key)

    def vastu_feed_listings(self, params: VastuFeedListingsRequest, *, idempotency_key: Optional[str] = None) -> VastuFeedListingsResponse:
        return self.vastu_operation(VastuOperation.FEED_LISTINGS, params, idempotency_key=idempotency_key)

    def vastu_quote_calculate(self, params: VastuQuoteCalculateRequest, *, idempotency_key: Optional[str] = None) -> VastuQuoteCalculateResponse:
        return self.vastu_operation(VastuOperation.QUOTE_CALCULATE, params, idempotency_key=idempotency_key)

    def vastu_remediation_tasks_upsert(self, params: VastuRemediationTasksUpsertRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationTasksUpsertResponse:
        return self.vastu_operation(VastuOperation.REMEDIATION_TASKS_UPSERT, params, idempotency_key=idempotency_key)

    def vastu_remediation_tasks_list(self, params: VastuRemediationTasksListRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationTasksListResponse:
        return self.vastu_operation(VastuOperation.REMEDIATION_TASKS_LIST, params, idempotency_key=idempotency_key)

    def vastu_remediation_tasks_delete(self, params: VastuRemediationTasksDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationTasksDeleteResponse:
        return self.vastu_operation(VastuOperation.REMEDIATION_TASKS_DELETE, params, idempotency_key=idempotency_key)

    def vastu_remediation_reassess(self, params: VastuRemediationReassessRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationReassessResponse:
        return self.vastu_operation(VastuOperation.REMEDIATION_REASSESS, params, idempotency_key=idempotency_key)

    def vastu_merchant_catalog_upload(self, params: VastuMerchantCatalogUploadRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantCatalogUploadResponse:
        return self.vastu_operation(VastuOperation.MERCHANT_CATALOG_UPLOAD, params, idempotency_key=idempotency_key)

    def vastu_merchant_catalog_get(self, params: VastuMerchantCatalogGetRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantCatalogGetResponse:
        return self.vastu_operation(VastuOperation.MERCHANT_CATALOG_GET, params, idempotency_key=idempotency_key)

    def vastu_merchant_catalog_delete(self, params: VastuMerchantCatalogDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantCatalogDeleteResponse:
        return self.vastu_operation(VastuOperation.MERCHANT_CATALOG_DELETE, params, idempotency_key=idempotency_key)

    def vastu_merchant_remedies(self, params: VastuMerchantRemediesRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantRemediesResponse:
        return self.vastu_operation(VastuOperation.MERCHANT_REMEDIES, params, idempotency_key=idempotency_key)

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REMEDIATION_TASKS_UPSERT], params: VastuRemediationTasksUpsertRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationTasksUpsertResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REMEDIATION_TASKS_LIST], params: VastuRemediationTasksListRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationTasksListResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REMEDIATION_TASKS_DELETE], params: VastuRemediationTasksDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationTasksDeleteResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REMEDIATION_REASSESS], params: VastuRemediationReassessRequest, *, idempotency_key: Optional[str] = None) -> VastuRemediationReassessResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MERCHANT_CATALOG_UPLOAD], params: VastuMerchantCatalogUploadRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantCatalogUploadResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MERCHANT_CATALOG_GET], params: VastuMerchantCatalogGetRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantCatalogGetResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MERCHANT_CATALOG_DELETE], params: VastuMerchantCatalogDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantCatalogDeleteResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MERCHANT_REMEDIES], params: VastuMerchantRemediesRequest, *, idempotency_key: Optional[str] = None) -> VastuMerchantRemediesResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PORTFOLIO_SEARCH], params: VastuPortfolioSearchRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioSearchResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PORTFOLIO_COMPARE], params: VastuPortfolioCompareRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioCompareResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PORTFOLIO_ANALYTICS], params: VastuPortfolioAnalyticsRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioAnalyticsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PORTFOLIO_USAGE], params: VastuPortfolioUsageRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioUsageResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PORTFOLIO_USAGE_EXPORT], params: VastuPortfolioUsageExportRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioUsageExportResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PORTFOLIO_BUDGETS_SET], params: VastuPortfolioBudgetsSetRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioBudgetsSetResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PORTFOLIO_BUDGETS_GET], params: VastuPortfolioBudgetsGetRequest, *, idempotency_key: Optional[str] = None) -> VastuPortfolioBudgetsGetResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.DRAWING_SHEET], params: VastuDrawingSheetRequest, *, idempotency_key: Optional[str] = None) -> VastuDrawingSheetResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_CREATE], params: VastuPropertiesCreateRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCreateResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_UPDATE], params: VastuPropertiesUpdateRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesUpdateResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_COLLABORATION_GET], params: VastuPropertiesCollaborationGetRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationGetResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_COLLABORATION_INVITE], params: VastuPropertiesCollaborationInviteRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationInviteResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_COLLABORATION_REVOKE], params: VastuPropertiesCollaborationRevokeRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationRevokeResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_COLLABORATION_MEMBERS], params: VastuPropertiesCollaborationMembersRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationMembersResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_COLLABORATION_COMMENT], params: VastuPropertiesCollaborationCommentRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationCommentResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_COLLABORATION_REVIEW], params: VastuPropertiesCollaborationReviewRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationReviewResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_COLLABORATION_UPDATE], params: VastuPropertiesCollaborationUpdateRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesCollaborationUpdateResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_ACTIVITY_LIST], params: VastuPropertiesActivityListRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesActivityListResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_ACTIVITY_EXPORT], params: VastuPropertiesActivityExportRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesActivityExportResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_GET], params: VastuPropertiesGetRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesGetResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_LIST], params: VastuPropertiesListRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesListResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_DELETE], params: VastuPropertiesDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesDeleteResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PROPERTIES_LINK_SCAN], params: VastuPropertiesLinkScanRequest, *, idempotency_key: Optional[str] = None) -> VastuPropertiesLinkScanResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ARCHIVE_TIER], params: VastuArchiveTierRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveTierResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ARCHIVE_EXPORT], params: VastuArchiveExportRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveExportResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ARCHIVE_DELETE], params: VastuArchiveDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveDeleteResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ARCHIVE_SUMMARY], params: VastuArchiveSummaryRequest, *, idempotency_key: Optional[str] = None) -> VastuArchiveSummaryResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.FEED_LISTINGS], params: VastuFeedListingsRequest, *, idempotency_key: Optional[str] = None) -> VastuFeedListingsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.QUOTE_CALCULATE], params: VastuQuoteCalculateRequest, *, idempotency_key: Optional[str] = None) -> VastuQuoteCalculateResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLOT_SHAPE], params: VastuPlotShapeRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotShapeResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLOT_RATIO], params: VastuPlotRatioRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotRatioResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ENTRANCE_PADA], params: VastuEntrancePadaRequest, *, idempotency_key: Optional[str] = None) -> VastuEntrancePadaResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.DIRECTION_CORRECT], params: VastuDirectionCorrectRequest, *, idempotency_key: Optional[str] = None) -> VastuDirectionCorrectResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.DIRECTION_DECLINATION], params: VastuDirectionDeclinationRequest, *, idempotency_key: Optional[str] = None) -> VastuDirectionDeclinationResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.DIRECTION_ZONE_FROM_BEARING], params: VastuDirectionZoneFromBearingRequest, *, idempotency_key: Optional[str] = None) -> VastuDirectionZoneFromBearingResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AUDIT_FLOOR_PLAN], params: VastuAuditFloorPlanRequest, *, idempotency_key: Optional[str] = None) -> VastuAuditFloorPlanResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AUDIT_FLOOR_PLAN_DETAILED], params: VastuAuditFloorPlanDetailedRequest, *, idempotency_key: Optional[str] = None) -> VastuAuditFloorPlanDetailedResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AUDIT_SINGLE_ROOM], params: VastuAuditSingleRoomRequest, *, idempotency_key: Optional[str] = None) -> VastuAuditSingleRoomResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_SCAN_QUALITY], params: VastuArScanQualityRequest, *, idempotency_key: Optional[str] = None) -> VastuArScanQualityResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MANDALA_PROJECT_9_ZONE], params: VastuMandalaProject9ZoneRequest, *, idempotency_key: Optional[str] = None) -> VastuMandalaProject9ZoneResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MANDALA_PROJECT_81_PADA], params: VastuMandalaProject81PadaRequest, *, idempotency_key: Optional[str] = None) -> VastuMandalaProject81PadaResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MANDALA_PROJECT_BRAHMASTHAN], params: VastuMandalaProjectBrahmasthanRequest, *, idempotency_key: Optional[str] = None) -> VastuMandalaProjectBrahmasthanResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_DIRECTIONS_8], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceDirections8Response: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_MANDALA_9_ZONE], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceMandala9ZoneResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_MANDALA_45_DEVATAS], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceMandala45DevatasResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_DEFECTS_CATALOG], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceDefectsCatalogResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_REMEDIES_CATALOG], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceRemediesCatalogResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_DIRECTIONS_16], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceDirections16Response: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_DIRECTIONS_32], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceDirections32Response: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_COLORS_BY_ZONE], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceColorsByZoneResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_MATERIALS_BY_ZONE], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceMaterialsByZoneResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_MANDALA_64_PADA], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceMandala64PadaResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.REFERENCE_GATE_OBSTRUCTIONS], params: None = None, *, idempotency_key: Optional[str] = None) -> VastuReferenceGateObstructionsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_KITCHEN], params: VastuRoomKitchenRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomKitchenResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_BEDROOM], params: VastuRoomBedroomRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomBedroomResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_POOJA], params: VastuRoomPoojaRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomPoojaResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_TOILET], params: VastuRoomToiletRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomToiletResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_STAIRCASE], params: VastuRoomStaircaseRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomStaircaseResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_STUDY], params: VastuRoomStudyRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomStudyResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_LIVING], params: VastuRoomLivingRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomLivingResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_DINING], params: VastuRoomDiningRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomDiningResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_STORE_OPERATION], params: VastuRoomStoreRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomStoreResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ROOM_WATER_STORAGE], params: VastuRoomWaterStorageRequest, *, idempotency_key: Optional[str] = None) -> VastuRoomWaterStorageResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_BOREWELL], params: VastuPlacementBorewellRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementBorewellResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_WELL], params: VastuPlacementWellRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementWellResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_SEPTIC_TANK], params: VastuPlacementSepticTankRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementSepticTankResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_OVERHEAD_TANK], params: VastuPlacementOverheadTankRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementOverheadTankResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_TREE], params: VastuPlacementTreeRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementTreeResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_GARDEN], params: VastuPlacementGardenRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementGardenResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_BALCONY], params: VastuPlacementBalconyRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementBalconyResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_WINDOW], params: VastuPlacementWindowRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementWindowResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_GENERATOR_ELECTRICAL], params: VastuPlacementGeneratorElectricalRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementGeneratorElectricalResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLACEMENT_MAIN_GATE], params: VastuPlacementMainGateRequest, *, idempotency_key: Optional[str] = None) -> VastuPlacementMainGateResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLOT_EXTENSIONS_CUTS], params: VastuPlotExtensionsCutsRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotExtensionsCutsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLOT_SLOPE], params: VastuPlotSlopeRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotSlopeResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLOT_ORIENTATION], params: VastuPlotOrientationRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotOrientationResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLOT_ROAD_ORIENTATION], params: VastuPlotRoadOrientationRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotRoadOrientationResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ENTRANCE_RECOMMEND], params: VastuEntranceRecommendRequest, *, idempotency_key: Optional[str] = None) -> VastuEntranceRecommendResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ELEMENTS_DISTRIBUTION], params: VastuElementsDistributionRequest, *, idempotency_key: Optional[str] = None) -> VastuElementsDistributionResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ELEMENTS_BALANCE_SUGGEST], params: VastuElementsBalanceSuggestRequest, *, idempotency_key: Optional[str] = None) -> VastuElementsBalanceSuggestResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.DIRECTION_AUSPICIOUS_FACING], params: VastuDirectionAuspiciousFacingRequest, *, idempotency_key: Optional[str] = None) -> VastuDirectionAuspiciousFacingResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCORE_OVERALL], params: VastuScoreOverallRequest, *, idempotency_key: Optional[str] = None) -> VastuScoreOverallResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCORE_ZONE_WISE], params: VastuScoreZoneWiseRequest, *, idempotency_key: Optional[str] = None) -> VastuScoreZoneWiseResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCORE_COMPLIANCE_INDEX], params: VastuScoreComplianceIndexRequest, *, idempotency_key: Optional[str] = None) -> VastuScoreComplianceIndexResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.MULTI_STOREY_FLOOR_RULES], params: VastuMultiStoreyFloorRulesRequest, *, idempotency_key: Optional[str] = None) -> VastuMultiStoreyFloorRulesResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.COMPOUND_WALL_ANALYSIS], params: VastuCompoundWallAnalysisRequest, *, idempotency_key: Optional[str] = None) -> VastuCompoundWallAnalysisResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.FLOOR_LEVEL_ANALYSIS], params: VastuFloorLevelAnalysisRequest, *, idempotency_key: Optional[str] = None) -> VastuFloorLevelAnalysisResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SPECIALIZED_RESIDENTIAL], params: VastuSpecializedResidentialRequest, *, idempotency_key: Optional[str] = None) -> VastuSpecializedResidentialResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SPECIALIZED_COMMERCIAL], params: VastuSpecializedCommercialRequest, *, idempotency_key: Optional[str] = None) -> VastuSpecializedCommercialResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SPECIALIZED_TEMPLE], params: VastuSpecializedTempleRequest, *, idempotency_key: Optional[str] = None) -> VastuSpecializedTempleResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SPECIALIZED_FACTORY], params: VastuSpecializedFactoryRequest, *, idempotency_key: Optional[str] = None) -> VastuSpecializedFactoryResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SPECIALIZED_HOSPITAL], params: VastuSpecializedHospitalRequest, *, idempotency_key: Optional[str] = None) -> VastuSpecializedHospitalResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SPECIALIZED_RESTAURANT], params: VastuSpecializedRestaurantRequest, *, idempotency_key: Optional[str] = None) -> VastuSpecializedRestaurantResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SPECIALIZED_EDUCATIONAL], params: VastuSpecializedEducationalRequest, *, idempotency_key: Optional[str] = None) -> VastuSpecializedEducationalResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.TIMING_BHUMI_PUJAN], params: VastuTimingBhumiPujanRequest, *, idempotency_key: Optional[str] = None) -> VastuTimingBhumiPujanResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.TIMING_GRIHAPRAVESH], params: VastuTimingGrihapraveshRequest, *, idempotency_key: Optional[str] = None) -> VastuTimingGrihapraveshResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.TIMING_CONSTRUCTION_START], params: VastuTimingConstructionStartRequest, *, idempotency_key: Optional[str] = None) -> VastuTimingConstructionStartResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.TIMING_VASTU_SHANTI], params: VastuTimingVastuShantiRequest, *, idempotency_key: Optional[str] = None) -> VastuTimingVastuShantiResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_ANALYZE], params: VastuPlanAnalyzeRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanAnalyzeResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_IMPORT_DXF], params: VastuPlanImportDxfRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanImportDxfResponse: ...
    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_EXPORT_DXF], params: VastuPlanExportDxfRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanExportDxfResponse: ...
    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_IMPORT_IFC], params: VastuPlanImportIfcRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanImportIfcResponse: ...
    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_UPLOAD], params: VastuPlanUploadRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanUploadResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_REPORT], params: VastuPlanReportRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanReportResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_GENERATE], params: VastuPlanGenerateRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanGenerateResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_FROM_REQUIREMENTS], params: VastuPlanFromRequirementsRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanFromRequirementsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLAN_OPTIMIZE], params: VastuPlanOptimizeRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanOptimizeResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.FUSION_CHART], params: VastuFusionChartRequest, *, idempotency_key: Optional[str] = None) -> VastuFusionChartResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.COMPARE_BEFORE_AFTER_REMEDY], params: VastuCompareBeforeAfterRemedyRequest, *, idempotency_key: Optional[str] = None) -> VastuCompareBeforeAfterRemedyResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ENTRANCE_OBSTRUCTION_CHECK], params: VastuEntranceObstructionCheckRequest, *, idempotency_key: Optional[str] = None) -> VastuEntranceObstructionCheckResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.DIRECTION_SUN_PATH], params: VastuDirectionSunPathRequest, *, idempotency_key: Optional[str] = None) -> VastuDirectionSunPathResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_TRUE_NORTH_CALIBRATE], params: VastuArTrueNorthCalibrateRequest, *, idempotency_key: Optional[str] = None) -> VastuArTrueNorthCalibrateResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ASSESSMENTS], params: VastuAssessmentsRequest, *, idempotency_key: Optional[str] = None) -> VastuAssessmentsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.ASSESSMENTS_BATCH], params: VastuAssessmentsBatchRequest, *, idempotency_key: str) -> VastuAssessmentsBatchResponse: ...
    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.JOBS], params: VastuJobsRequest, *, idempotency_key: str) -> VastuJobsResponse: ...
    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_HEATMAP_RASTER], params: VastuArHeatmapRasterRequest, *, idempotency_key: Optional[str] = None) -> VastuArHeatmapRasterResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_ANCHOR_RECOMMENDATIONS], params: VastuArAnchorRecommendationsRequest, *, idempotency_key: Optional[str] = None) -> VastuArAnchorRecommendationsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_ZONE_TEXTURES], params: VastuArZoneTexturesRequest, *, idempotency_key: Optional[str] = None) -> VastuArZoneTexturesResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_YANTRA_MESHES], params: VastuArYantraMeshesRequest, *, idempotency_key: Optional[str] = None) -> VastuArYantraMeshesResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_DEITY_ICONS], params: VastuArDeityIconsRequest, *, idempotency_key: Optional[str] = None) -> VastuArDeityIconsResponse: ...

    def vastu_capture_merge(self, params: VastuArCaptureMergeRequest, *, idempotency_key: Optional[str] = None) -> VastuArCaptureMergeResponse:
        return self.vastu_operation(VastuOperation.AR_CAPTURE_MERGE, params, idempotency_key=idempotency_key)

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_CAPTURE_MERGE], params: VastuArCaptureMergeRequest, *, idempotency_key: Optional[str] = None) -> VastuArCaptureMergeResponse: ...

    def vastu_from_survey(self, params: VastuPlotFromSurveyRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotFromSurveyResponse:
        return self.vastu_operation(VastuOperation.PLOT_FROM_SURVEY, params, idempotency_key=idempotency_key)

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.PLOT_FROM_SURVEY], params: VastuPlotFromSurveyRequest, *, idempotency_key: Optional[str] = None) -> VastuPlotFromSurveyResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_ROOM_CAPTURE], params: VastuArRoomCaptureRequest, *, idempotency_key: Optional[str] = None) -> VastuArRoomCaptureResponse: ...
    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_ATTESTATION_CHALLENGE], params: VastuArAttestationChallengeRequest, *, idempotency_key: Optional[str] = None) -> VastuArAttestationChallengeResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCANS_SAVE], params: VastuScansSaveRequest, *, idempotency_key: Optional[str] = None) -> VastuScansSaveResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCANS_RETRIEVE], params: VastuScansRetrieveRequest, *, idempotency_key: Optional[str] = None) -> VastuScansRetrieveResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCANS_LIST], params: VastuScansListRequest, *, idempotency_key: Optional[str] = None) -> VastuScansListResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCANS_DELETE], params: VastuScansDeleteRequest, *, idempotency_key: Optional[str] = None) -> VastuScansDeleteResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.SCANS_TIMELAPSE], params: VastuScansTimelapseRequest, *, idempotency_key: Optional[str] = None) -> VastuScansTimelapseResponse: ...

    def vastu_operation(
        self,
        operation: VastuOperation,
        params: Optional[Mapping[str, VastuJsonValue]] = None,
        *,
        idempotency_key: Optional[str] = None,
    ) -> VastuAnyResponse:
        """Call one entry from the exact OpenAPI-derived operation contract map.

        Each overload supplies its operation-specific request and response type.
        """
        if params is None:
            payload: Dict[str, VastuJsonValue] = {}
        elif isinstance(params, Mapping):
            payload = dict(params)
        else:
            raise TypeError("Vastu request body must be a mapping")
        path = operation.value
        if "{id}" in path:
            raise ValueError(f"{path} carries a job id; use vastu_job_status, vastu_job_results or vastu_job_cancel")
        if _is_vastu_get_path(path):
            result = self._request("GET", f"/v2/astrology/vastu/{path}", params=payload, idempotency_key=idempotency_key)
        else:
            result = self._request("POST", f"/v2/astrology/vastu/{path}", data=payload, idempotency_key=idempotency_key)
        return cast(VastuAnyResponse, result)

    def vastu_job_submit(self, request: VastuJobsRequest, *, idempotency_key: str) -> VastuJobsResponse:
        """Queue 1 to 1,000 assessments and get a ``jobId`` back at once (202).

        ``idempotency_key`` is mandatory and must be retained by the caller.
        Save it with this exact request: after a lost response, submit the same
        body with the same key and the original job comes back
        (``data["replayed"]`` is True) instead of a second paid job. A different
        body under the same key is refused with 409. Each item is charged only
        after it succeeds.
        """
        return cast(VastuJobsResponse, self.vastu_operation(
            VastuOperation.JOBS, cast(Mapping[str, VastuJsonValue], request), idempotency_key=idempotency_key
        ))

    def vastu_job_status(self, job_id: str) -> VastuJobsIdResponse:
        """Status, per-state counts and billing of a job. Free."""
        return cast(VastuJobsIdResponse, self._request(
            "GET", f"/v2/astrology/vastu/jobs/{_vastu_job_id(job_id)}"
        ))

    def vastu_job_results(self, job_id: str, *, cursor: Optional[str] = None) -> VastuJobsIdResultsResponse:
        """One page (up to 50) of finished item results, in item order. Free.

        Cursor pagination only: pass the previous page's ``nextCursor``; it is
        None on the last page. See ``vastu_job_result_items`` to walk them all.
        """
        if cursor is not None and (not isinstance(cursor, str) or not cursor or len(cursor) > 32):
            raise ValueError("cursor must be the nextCursor of the previous page (1 to 32 characters)")
        return cast(VastuJobsIdResultsResponse, self._request(
            "GET", f"/v2/astrology/vastu/jobs/{_vastu_job_id(job_id)}/results",
            params={"cursor": cursor} if cursor is not None else None,
        ))

    def vastu_job_result_items(self, job_id: str) -> Iterator[VastuJobResultItem]:
        """Every finished item of a job, following ``nextCursor`` until it is None."""
        cursor: Optional[str] = None
        while True:
            page = self.vastu_job_results(job_id, cursor=cursor)
            for item in page["data"]["results"]:
                yield item
            following = page["data"]["nextCursor"]
            if not following:
                return
            if following == cursor:
                raise ValueError("The server returned the same results cursor twice")
            cursor = following

    def vastu_job_cancel(self, job_id: str) -> VastuJobsIdCancelResponse:
        """Stop a queued or running job. Items already charged stay charged; the rest are not run. Free."""
        return cast(VastuJobsIdCancelResponse, self._request(
            "POST", f"/v2/astrology/vastu/jobs/{_vastu_job_id(job_id)}/cancel"
        ))

    def upload_vastu_report(
        self, data: bytes, *, idempotency_key: str, filename: str = "report.pdf"
    ) -> VastuChatUploadData:
        """Upload a report PDF (5 MiB, 40 pages, text layer) to ask questions about it.

        Pass the result to ``ask_vastu_report(question, report_ref={"type":
        "upload", "id": upload["uploadId"]})``. The upload is paid.

        ``idempotency_key`` is mandatory and names this one file permanently:
        after a lost response, call again with the same key and the same file
        and the original upload comes back without a second charge. Use a new
        key for every new file. 1 to 256 visible ASCII characters.
        """
        if not isinstance(idempotency_key, str) or not _VASTU_UPLOAD_KEY.match(idempotency_key):
            raise ValueError("A caller-retained Idempotency-Key of 1 to 256 visible ASCII characters is required")
        if not isinstance(data, (bytes, bytearray, memoryview)) or len(data) == 0:
            raise ValueError("data must be the non-empty bytes of a PDF")
        safe_name = re.sub(r'[\r\n"\\]', "_", filename or "report.pdf")
        return cast(VastuChatUploadData, self._request(
            "POST", "/api/v1/vastu/chat/uploads",
            files={"file": (safe_name, bytes(data), "application/pdf")},
            idempotency_key=idempotency_key,
        ))

    def vastu_reference(self, table: str) -> Dict[str, Any]:
        """Get a Vastu reference table (no building/chart input required).

        Args:
            table: Path suffix under reference/, e.g. "reference/mandala/9-zone",
                "reference/mandala/45-devatas", "reference/directions/8",
                "reference/defects/catalog", "reference/remedies/catalog",
                "reference/colors-by-zone", "reference/materials-by-zone",
                "reference/gate-obstructions"
        """
        return self._request("GET", f"/v2/astrology/vastu/{table.lstrip('/')}")

    def vastu_mandala_project(
        self, scheme: str, params: Dict[str, Any], *, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Project a mandala onto a plot.

        Args:
            scheme: "9-zone", "81-pada", or "brahmasthan"
            params: Building payload, e.g. {"plotPolygon": [...], "bearingDeg": 0}
            idempotency_key: Optional caller-retained key. Save it to retry the
                same logical call after a lost response without paying twice.
        """
        return self._request(
            "POST", f"/v2/astrology/vastu/mandala/project/{scheme}", data=params,
            idempotency_key=idempotency_key,
        )

    def vastu_entrance_pada(
        self, params: VastuEntrancePadaRequest, *, idempotency_key: Optional[str] = None
    ) -> VastuEntrancePadaResponse:
        """Door-pada classifier.

        Args:
            params: Building payload, e.g. {"plotPolygon": [...], "doorXY": [...],
                "bearingDeg": 0}
        """
        return self.vastu_operation(VastuOperation.ENTRANCE_PADA, params, idempotency_key=idempotency_key)

    def vastu_entrance_recommend(
        self, params: VastuEntranceRecommendRequest, *, idempotency_key: Optional[str] = None
    ) -> VastuEntranceRecommendResponse:
        """Entrance recommendation.

        Args:
            params: Building payload, e.g. {"plot": {...}}
        """
        return self.vastu_operation(VastuOperation.ENTRANCE_RECOMMEND, params, idempotency_key=idempotency_key)

    def vastu_ar_scan_quality(
        self, params: VastuArScanQualityRequest, *, idempotency_key: Optional[str] = None
    ) -> VastuArScanQualityResponse:
        """Grade an AR scan before you pay to audit it.

        Returns ``score`` (0-100), ``grade`` (A-F), per-dimension ``dimensions``,
        ``missingData``, ``warnings``, ``reScanSuggestions`` and
        ``acceptForAudit`` -- the one field worth branching on. Call this BEFORE
        an audit or assessment: a scan the grader will not accept produces
        findings nobody should be billed for.

        Every reading is optional, and an ABSENT reading is not a bad one -- the
        grader scores a missing dimension at a neutral 50 and says so in that
        dimension's ``reason``. Do not pass zeros for readings you do not have;
        that grades the scan as failing.

        Args:
            params: Any of ``pointCloudDensity`` (float), ``polygonClosure``
                (bool), ``roomsTagged`` (bool), ``compassConfidence`` (float),
                ``gpsConfidence`` (float), ``scanDurationSec`` (float),
                ``scannedAreaM2`` (float). These names are read verbatim by the
                handler; a misspelling is silently ignored.

        Example:
            >>> q = client.vastu_ar_scan_quality({
            ...     "pointCloudDensity": 850, "polygonClosure": True,
            ...     "roomsTagged": True, "compassConfidence": 0.9,
            ...     "gpsConfidence": 0.85, "scanDurationSec": 240,
            ...     "scannedAreaM2": 60,
            ... })
            >>> if not q["data"]["acceptForAudit"]:
            ...     print(q["data"]["reScanSuggestions"])
        """
        return self.vastu_operation(VastuOperation.AR_SCAN_QUALITY, params, idempotency_key=idempotency_key)

    def vastu_ar_true_north_calibrate(
        self, params: VastuArTrueNorthCalibrateRequest, *, idempotency_key: Optional[str] = None
    ) -> VastuArTrueNorthCalibrateResponse:
        """Derive true north from a sun sighting, for a compass you cannot trust.

        Apply the returned ``offsetDeg`` as
        ``trueHeadingDeg = (deviceHeadingDeg + offsetDeg) % 360``.

        ALWAYS check ``reliable`` first. The sun is refused as a reference near
        the horizon and near the zenith (above ~70 degrees elevation), where its
        azimuth moves too fast to fix a heading; there ``reliable`` is False,
        ``reason`` says why, and ``offsetDeg`` must not be used.

        Args:
            params: ``lat``, ``lon``, ``datetime`` (ISO-8601 instant of the
                sighting) and ``deviceHeadingAtSunDeg``. All four required.
                Supply ``deviceHeadingAccuracyDeg`` and ``headingSampleAgeMs``
                for the reported quality gate; otherwise reliable is false.

        Example:
            >>> cal = client.vastu_ar_true_north_calibrate({
            ...     "lat": 28.61, "lon": 77.21,
            ...     "datetime": "2025-12-21T03:30:00Z",
            ...     "deviceHeadingAtSunDeg": 130.0,
            ... })
            >>> if cal["data"]["reliable"]:
            ...     apply_offset(cal["data"]["offsetDeg"])
        """
        return self.vastu_operation(VastuOperation.AR_TRUE_NORTH_CALIBRATE, params, idempotency_key=idempotency_key)

    def vastu_room(
        self, room_type: str, params: Dict[str, Any], *, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Single-room placement, e.g. vastu_room("kitchen", {"zone": "southeast"}).

        Args:
            room_type: kitchen, bedroom, pooja, toilet, staircase, study, living,
                dining, store, or water-storage
            params: Building/room payload
        """
        return self._request(
            "POST", f"/v2/astrology/vastu/room/{room_type}", data=params, idempotency_key=idempotency_key
        )

    def vastu_placement(
        self, feature: str, params: Dict[str, Any], *, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Site placement, e.g. vastu_placement("borewell", {"zone": "north-east"}).

        Args:
            feature: balcony, borewell, garden, generator-electrical, main-gate,
                overhead-tank, septic-tank, tree, well, or window
            params: Building/site payload
        """
        return self._request(
            "POST", f"/v2/astrology/vastu/placement/{feature}", data=params, idempotency_key=idempotency_key
        )

    def vastu_audit(
        self, kind: str, params: Dict[str, Any], *, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compliance audit.

        Args:
            kind: "single-room", "floor-plan", or "floor-plan-detailed"
            params: Building payload, e.g. {"rooms": [...], "plot": {...}}
        """
        return self._request(
            "POST", f"/v2/astrology/vastu/audit/{kind}", data=params, idempotency_key=idempotency_key
        )

    def vastu_listing_assessment(
        self, params: Dict[str, Any], *, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assess a real-estate listing's Vastu compliance.

        Folds ``score/overall``, the 9-zone reference, ``entrance/pada``, and
        ``ar/scan-quality`` into one buyer-facing verdict with a badge.

        Args:
            params: Must include ``inputSource`` ("seller-typed" |
                "plan-derived" | "ar-measured") -- it decides the badge and
                confidence ceiling and is never inferred. Only
                "plan-derived" and "ar-measured" listings can ever carry an
                assessed badge; "seller-typed" input is scored but never
                badge-eligible. Also takes ``rooms``, ``plot``, etc. like
                ``vastu_audit``.

        Returns:
            dict with ``score``, ``confidence``, ``badgeEligibility``
            (``{inputSource, badge, eligible, variant}``), ``findings``,
            ``grade``, and ``confidenceBasis``. Check
            ``badgeEligibility["eligible"]`` before showing a badge to a buyer.
        """
        return self._request(
            "POST", "/v2/astrology/vastu/assessments", data=params, idempotency_key=idempotency_key
        )

    def vastu_compare_versions(self, params: VastuCompareVersionsRequest, *, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return self._request("POST", "/v2/astrology/vastu/plan/compare-versions", data=params, idempotency_key=idempotency_key)

    def vastu_verify_receipt(self, params: VastuReceiptVerifyRequest) -> Dict[str, Any]:
        return self._request("POST", "/v2/astrology/vastu/receipt/verify", data=params)

    def vastu_rule_versions(self) -> Dict[str, Any]:
        return self._request("GET", "/v2/astrology/vastu/rules/versions")

    def vastu_score(
        self, kind: str, params: Dict[str, Any], *, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Vastu score.

        Args:
            kind: "overall", "zone-wise", or "compliance-index"
            params: Building payload
        """
        return self._request(
            "POST", f"/v2/astrology/vastu/score/{kind}", data=params, idempotency_key=idempotency_key
        )

    def vastu_plan_import_dxf(self, params: VastuPlanImportDxfRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanImportDxfResponse:
        """Paid CAD geometry interchange; inspect needsReview before analysis."""
        return self.vastu_operation(VastuOperation.PLAN_IMPORT_DXF, params, idempotency_key=idempotency_key)

    def vastu_plan_export_dxf(self, params: VastuPlanExportDxfRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanExportDxfResponse:
        """Paid CAD geometry interchange; inspect needsReview before analysis."""
        return self.vastu_operation(VastuOperation.PLAN_EXPORT_DXF, params, idempotency_key=idempotency_key)

    def vastu_plan_export_ifc(self, params: VastuPlanExportIfcRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanExportIfcResponse:
        return self.vastu_operation(VastuOperation.PLAN_EXPORT_IFC, params, idempotency_key=idempotency_key)

    def vastu_plan_convert_units(self, params: VastuPlanConvertUnitsRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanConvertUnitsResponse:
        return self.vastu_operation(VastuOperation.PLAN_CONVERT_UNITS, params, idempotency_key=idempotency_key)

    def vastu_plan_import_ifc(self, params: VastuPlanImportIfcRequest, *, idempotency_key: Optional[str] = None) -> VastuPlanImportIfcResponse:
        """Paid CAD geometry interchange; inspect needsReview before analysis."""
        return self.vastu_operation(VastuOperation.PLAN_IMPORT_IFC, params, idempotency_key=idempotency_key)

    def vastu_plan_generate(
        self, params: VastuPlanGenerateRequest, *, idempotency_key: Optional[str] = None
    ) -> VastuPlanGenerateResponse:
        """Generate up to 3 ranked floor plans from a plot + room programme.

        Args:
            params: Building payload, e.g. {"plot": {...}, "rooms": [...]}
        """
        return self.vastu_operation(VastuOperation.PLAN_GENERATE, params, idempotency_key=idempotency_key)

    def vastu_plan_from_requirements(
        self, params: VastuPlanFromRequirementsRequest, *, idempotency_key: Optional[str] = None
    ) -> VastuPlanFromRequirementsResponse:
        """Generate a floor plan from a high-level brief (BHK, bathrooms, parking...).

        Args:
            params: Requirements payload, e.g. {"bhk": 3, "bathrooms": 2, "plot": {...}}
        """
        return self.vastu_operation(VastuOperation.PLAN_FROM_REQUIREMENTS, params, idempotency_key=idempotency_key)

    def vastu_declination(
        self, lat: float, lon: float, date: Optional[str] = None, *, idempotency_key: Optional[str] = None
    ) -> VastuDirectionDeclinationResponse:
        """Magnetic declination (true-north correction) for a location. India grid.

        Args:
            lat: Latitude
            lon: Longitude
            date: Optional date (defaults to server's "today")
        """
        params: VastuDirectionDeclinationRequest = {"lat": lat, "lon": lon}
        if date is not None:
            params["date"] = date
        return self.vastu_operation(VastuOperation.DIRECTION_DECLINATION, params, idempotency_key=idempotency_key)

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

    # Divisional charts the API serves on their own path. Any other division,
    # including D2 (hora), goes through /v2/astrology/divisional-chart.
    _NAMED_DIVISIONAL_CHARTS = frozenset([
        "navamsa", "dashamsa", "saptamsa", "dwadashamsa", "chaturthamsa",
        "shodasamsa", "vimsamsa", "chaturvimsamsa", "bhamsa", "trimsamsa",
        "khavedamsa", "akshavedamsa", "shashtiamsa",
    ])

    def get_divisional_chart(self, chart: Union[str, int], birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get divisional chart (D1-D60).

        Args:
            chart: a chart name (navamsa, dashamsa, saptamsa, dwadashamsa, ...),
                "hora", or a division as ``9``, ``"D9"`` or ``"9"``. Supported
                divisions: 1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60.
            birth_details: dict with datetime, latitude, longitude, timezone
        """
        name = str(chart).strip().lower()
        if name in self._NAMED_DIVISIONAL_CHARTS:
            return self._request("POST", f"/v2/astrology/{name}", data=birth_details)
        if name == "hora":
            name = "d2"
        digits = name[1:] if name.startswith("d") else name
        if not digits.isdigit():
            raise ValueError(f"Unknown divisional chart {chart!r}; use a name such as 'navamsa' or a division such as 9 or 'D9'")
        # The generic endpoint takes the division number in the body.
        return self._request(
            "POST", "/v2/astrology/divisional-chart", data={**birth_details, "division": int(digits)}
        )

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

        TS->Rust transition note (3.0.6): the result is normalized so the
        transition-divergent prose keys (``interpretation``, per-aspect
        ``orb_quality`` / ``signifies``) are always present — the Rust engine
        may omit them while the computed geometry stays parity-exact. Code that
        reads those keys never raises a KeyError from either engine. The full
        payload is preserved; only missing keys are backfilled with empty values.
        """
        result = _v2_payload(self._request("POST", f"/v2/western/{type}",
                                            data={"person1": person1, "person2": person2}))
        return normalize_western_relationship(result if isinstance(result, dict) else {})

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

    def get_conversations(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> Dict[str, Any]:
        """List recent active conversations, ordered by last activity.

        The server defaults to 10 results. Limit accepts 1..100.
        Pass data.nextCursor to continue, including after an empty page; stop at null.
        data.paginationAvailable=false means the serving backend cannot continue.
        Activity can change between calls; the listing is not a snapshot.
        """
        if limit is not None and (type(limit) is not int or not 1 <= limit <= 100):
            raise ValueError("limit must be an integer between 1 and 100")
        if cursor is not None and (not isinstance(cursor, str) or not 1 <= len(cursor) <= 2048):
            raise ValueError("cursor must be a non-empty string of at most 2048 characters")
        params = {} if limit is None else {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return self._request("GET", "/api/v1/conversations", params=params or None)

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
    # typed voice envelope
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
            tier: Voice tier identifier from the current API catalog.
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
        import contextlib
        import json as _json

        with contextlib.ExitStack() as stack:
            # Normalize audio input to (name, fileobj-or-bytes, mime) tuple.
            if hasattr(audio, "read"):
                audio_tuple = ("audio", audio, audio_mime)
            elif isinstance(audio, (bytes, bytearray)):
                audio_tuple = ("audio", bytes(audio), audio_mime)
            elif isinstance(audio, str):
                # File path
                audio_tuple = ("audio", stack.enter_context(open(audio, "rb")), audio_mime)
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

            url = f"{self.base_url}/api/v1/voice"
            # Route through self.session (a _VedikaSession) so redirects are never
            # followed — a top-level requests.post() would follow a 307 and resend
            # the private body to another origin. Content-Type:
            # None drops the session's JSON default so requests sets the multipart
            # boundary; the session still supplies auth headers. /api/v1/voice is
            # not an idempotency-certified operation: a key would be answered with
            # 422, so none is sent. The call is made once and never resent.
            response = self.session.post(
                url,
                files=files,
                data=data,
                headers={"Content-Type": None},
                timeout=self.timeout,
            )

            _refuse_redirect(response)
            if response.status_code >= 400:
                _raise_api_error(response, self.api_key)

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
    # Extended Domain Sub-Clients
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
            # TS->Rust transition (3.0.6): unwrap the v2 envelope like every other
            # v2 domain (this path previously parsed the raw envelope, which on an
            # enveloped response silently zeroed the score — a money/verdict-
            # sensitive family). Full payload kept on `.raw`. The matchmaking
            # TOTAL may differ by engine (value divergence, not shape); kootas /
            # doshaAnalysis are passthrough dicts so either engine parses cleanly.
            _r = _v2_payload(self._c._request("POST", "/v2/matrimony/unified-match",
                                              data={"person1": person1, "person2": person2}))
            _o = MatchResult.from_dict(_r)
            _o.raw = _r
            return _o

        def dosha_cancellation(self, person1: Dict[str, Any], person2: Dict[str, Any]) -> DoshaMatchResult:
            """Check dosha cancellation between two charts.

            Args:
                person1: dict with datetime, latitude, longitude, timezone
                person2: dict with datetime, latitude, longitude, timezone
            """
            _r = _v2_payload(self._c._request("POST", "/v2/matrimony/dosha-cancellation",
                                              data={"person1": person1, "person2": person2}))
            _o = DoshaMatchResult.from_dict(_r)
            _o.raw = _r
            return _o

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
            # TS->Rust transition (3.0.6): unwrap the v2 envelope before parsing
            # (was parsing the raw envelope). Each system block is a passthrough
            # dict, so a missing optional system from either engine never crashes.
            _r = _v2_payload(self._c._request("POST", "/v2/astrology/dasha/current-all", data=birth_details))
            _o = AllDashaResult.from_dict(_r)
            _o.raw = _r
            return _o

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
