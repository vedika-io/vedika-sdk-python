"""
Vedika API Client
Main client class for interacting with the Vedika Astrology API.
"""

from __future__ import annotations

import os
import uuid
from enum import Enum
from typing import Dict, Any, Optional, Iterator, List, Mapping, TypedDict, Literal, Union, overload, cast  # noqa: F401
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
    InsufficientCreditsError,
    SubscriptionExpiredError,
    ValidationError
)


class VastuOperation(str, Enum):
    """One member per mounted logical Vastu route; URL aliases are not duplicated."""
    SCANS_TIMELAPSE = "scans/timelapse"
    SCANS_DELETE = "scans/delete"
    SCANS_LIST = "scans/list"
    SCANS_RETRIEVE = "scans/retrieve"
    SCANS_SAVE = "scans/save"
    AR_DEITY_ICONS = "ar/deity-icons"
    AR_ROOM_CAPTURE = "ar/room-capture"
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

_VASTU_OPERATION_CONTRACTS = {
    "scans/timelapse": {"method": "POST", "requestSchema": "VastuScansTimelapseRequest", "responseSchema": "VastuScansTimelapseResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "scans/delete": {"method": "POST", "requestSchema": "VastuScansDeleteRequest", "responseSchema": "VastuScansDeleteResponse", "auth": "apiKey", "errors": (400, 401, 404, 405, 409, 410, 413, 415, 503)},
    "scans/list": {"method": "POST", "requestSchema": "VastuScansListRequest", "responseSchema": "VastuScansListResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "scans/retrieve": {"method": "POST", "requestSchema": "VastuScansRetrieveRequest", "responseSchema": "VastuScansRetrieveResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "scans/save": {"method": "POST", "requestSchema": "VastuScansSaveRequest", "responseSchema": "VastuScansSaveResponse", "auth": "apiKey", "errors": (400, 401, 402, 404, 405, 409, 410, 413, 415, 422, 503)},
    "ar/deity-icons": {"method": "POST", "requestSchema": "VastuArDeityIconsRequest", "responseSchema": "VastuArDeityIconsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/room-capture": {"method": "POST", "requestSchema": "VastuArRoomCaptureRequest", "responseSchema": "VastuArRoomCaptureResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/yantra-meshes": {"method": "POST", "requestSchema": "VastuArYantraMeshesRequest", "responseSchema": "VastuArYantraMeshesResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/zone-textures": {"method": "POST", "requestSchema": "VastuArZoneTexturesRequest", "responseSchema": "VastuArZoneTexturesResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/anchor-recommendations": {"method": "POST", "requestSchema": "VastuArAnchorRecommendationsRequest", "responseSchema": "VastuArAnchorRecommendationsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/heatmap-raster": {"method": "POST", "requestSchema": "VastuArHeatmapRasterRequest", "responseSchema": "VastuArHeatmapRasterResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/scan-quality": {"method": "POST", "requestSchema": "VastuArScanQualityRequest", "responseSchema": "VastuArScanQualityResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "ar/true-north-calibrate": {"method": "POST", "requestSchema": "VastuArTrueNorthCalibrateRequest", "responseSchema": "VastuArTrueNorthCalibrateResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "assessments": {"method": "POST", "requestSchema": "VastuAssessmentsRequest", "responseSchema": "VastuAssessmentsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "assessments/batch": {"method": "POST", "requestSchema": "VastuAssessmentsBatchRequest", "responseSchema": "VastuAssessmentsBatchResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
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
    "plan/analyze": {"method": "POST", "requestSchema": "VastuPlanAnalyzeRequest", "responseSchema": "VastuPlanAnalyzeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/from-requirements": {"method": "POST", "requestSchema": "VastuPlanFromRequirementsRequest", "responseSchema": "VastuPlanFromRequirementsResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/generate": {"method": "POST", "requestSchema": "VastuPlanGenerateRequest", "responseSchema": "VastuPlanGenerateResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/optimize": {"method": "POST", "requestSchema": "VastuPlanOptimizeRequest", "responseSchema": "VastuPlanOptimizeResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "plan/report": {"method": "POST", "requestSchema": "VastuPlanReportRequest", "responseSchema": "VastuPlanReportResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
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
    "score/compliance-index": {"method": "POST", "requestSchema": "VastuScoreComplianceIndexRequest", "responseSchema": "VastuScoreComplianceIndexResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "score/overall": {"method": "POST", "requestSchema": "VastuScoreOverallRequest", "responseSchema": "VastuScoreOverallResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
    "score/zone-wise": {"method": "POST", "requestSchema": "VastuScoreZoneWiseRequest", "responseSchema": "VastuScoreZoneWiseResponse", "auth": "apiKey", "errors": (400, 401, 402, 405, 415, 500)},
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

class VastuArHeatmapRasterRequestRoomsItem(TypedDict):
    roomType: str
    zone: str

class _VastuArHeatmapRasterRequestOptional(TypedDict, total=False):
    plotPolygon: List[List[float]]
    bearingDeg: float

class VastuArHeatmapRasterRequest(_VastuArHeatmapRasterRequestOptional):
    rooms: List[VastuArHeatmapRasterRequestRoomsItem]

class VastuArPlanToWorld(TypedDict):
    units: Literal["metres"]
    origin: List[float]
    xAxis: List[float]
    yAxis: List[float]

class VastuArAnchorRecommendationsRequest(TypedDict):
    plotPolygon: List[List[float]]
    bearingDeg: float
    planToWorld: VastuArPlanToWorld

class _VastuArZoneTexturesRequestOptional(TypedDict, total=False):
    zone: Literal["NW", "N", "NE", "W", "CENTER", "E", "SW", "S", "SE"]

class VastuArZoneTexturesRequest(_VastuArZoneTexturesRequestOptional):
    pass

class _VastuArYantraMeshesRequestOptional(TypedDict, total=False):
    format: Literal["gltf", "usdz"]

class VastuArYantraMeshesRequest(_VastuArYantraMeshesRequestOptional):
    model: Literal["nine-zone-mandala"]

class _VastuArDeityIconsRequestOptional(TypedDict, total=False):
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
    planToWorld: Optional[VastuArPlanToWorld]

class VastuRoomCaptureFrame(_VastuRoomCaptureFrameOptional):
    units: Literal["metres"]
    axes: Literal["+X east,+Y true north"]
    north: VastuRoomCaptureFrameNorth

class VastuRoomCaptureOutline(TypedDict):
    polygon: List[List[float]]
    source: Literal["traced"]

class _VastuRoomCaptureRoomsItemOpeningsItemOptional(TypedDict, total=False):
    heightM: Optional[float]

class VastuRoomCaptureRoomsItemOpeningsItem(_VastuRoomCaptureRoomsItemOpeningsItemOptional):
    kind: Literal["door", "window", "opening"]
    centerXY: List[float]
    widthM: float
    confidence: Literal["low", "medium", "high"]

class _VastuRoomCaptureRoomsItemOptional(TypedDict, total=False):
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

class _VastuArRoomCaptureRequestOptional(TypedDict, total=False):
    zoneResolution: Literal[8, 16, 32]

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

class VastuScansSaveRequest(TypedDict):
    scanId: str
    propertyId: str
    title: str
    retentionDays: int
    snapshot: VastuScanSnapshot

class VastuScansRetrieveRequest(TypedDict):
    requestId: str
    scanId: str

class _VastuScansListRequestOptional(TypedDict, total=False):
    cursor: Optional[str]

class VastuScansListRequest(_VastuScansListRequestOptional):
    requestId: str
    limit: int

class VastuScansDeleteRequest(TypedDict):
    scanId: str

class VastuScansTimelapseRequest(TypedDict):
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

class VastuArScanQualityRequest(_VastuArScanQualityRequestOptional):
    pass

class _VastuArTrueNorthCalibrateRequestOptional(TypedDict, total=False):
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

class VastuAssessmentsBatchRequest(TypedDict):
    """One to twenty items with unique IDs; retain the caller key for retries."""
    items: List[VastuAssessmentsBatchRequestItemsItem]


class _VastuAuditFloorPlanDetailedRequestOptional(TypedDict, total=False):
    plotPolygon: List[List[float]]
    bearingDeg: float

class VastuAuditFloorPlanDetailedRequest(_VastuAuditFloorPlanDetailedRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuAuditFloorPlanRequestOptional(TypedDict, total=False):
    rooms: List[Dict[str, VastuJsonValue]]
    text: str

class VastuAuditFloorPlanRequest(_VastuAuditFloorPlanRequestOptional):
    pass

class VastuAuditSingleRoomRequest(TypedDict):
    roomType: str
    zone: str

class _VastuCompareBeforeAfterRemedyRequestOptional(TypedDict, total=False):
    rooms: List[Dict[str, VastuJsonValue]]
    text: str

class VastuCompareBeforeAfterRemedyRequest(_VastuCompareBeforeAfterRemedyRequestOptional):
    remedies: List[Dict[str, VastuJsonValue]]

class _VastuCompoundWallAnalysisRequestOptional(TypedDict, total=False):
    walls: Union[List[Dict[str, VastuJsonValue]], Dict[str, VastuJsonValue]]

class VastuCompoundWallAnalysisRequest(_VastuCompoundWallAnalysisRequestOptional):
    pass

class _VastuDirectionAuspiciousFacingRequestOptional(TypedDict, total=False):
    occupant: str

class VastuDirectionAuspiciousFacingRequest(_VastuDirectionAuspiciousFacingRequestOptional):
    purpose: str

class _VastuDirectionCorrectRequestOptional(TypedDict, total=False):
    date: str

class VastuDirectionCorrectRequest(_VastuDirectionCorrectRequestOptional):
    direction: str
    lat: float
    lon: float

class _VastuDirectionDeclinationRequestOptional(TypedDict, total=False):
    date: str

class VastuDirectionDeclinationRequest(_VastuDirectionDeclinationRequestOptional):
    lat: float
    lon: float

class _VastuDirectionSunPathRequestOptional(TypedDict, total=False):
    date: str

class VastuDirectionSunPathRequest(_VastuDirectionSunPathRequestOptional):
    lat: float
    lon: float

class VastuDirectionZoneFromBearingRequest(TypedDict):
    bearingDeg: float

class _VastuElementsBalanceSuggestRequestOptional(TypedDict, total=False):
    distribution: Dict[str, VastuJsonValue]
    deficient: List[str]
    excess: List[str]

class VastuElementsBalanceSuggestRequest(_VastuElementsBalanceSuggestRequestOptional):
    pass

class VastuElementsDistributionRequest(TypedDict):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuEntranceObstructionCheckRequestOptional(TypedDict, total=False):
    houseHeightMeters: float
    distanceMeters: float

class VastuEntranceObstructionCheckRequest(_VastuEntranceObstructionCheckRequestOptional):
    feature: str

class _VastuEntrancePadaRequestOptional(TypedDict, total=False):
    bearingDeg: float

class VastuEntrancePadaRequest(_VastuEntrancePadaRequestOptional):
    plotPolygon: List[List[float]]
    doorXY: List[float]

class VastuEntranceRecommendRequest(TypedDict):
    facing: str

class _VastuFloorLevelAnalysisRequestOptional(TypedDict, total=False):
    levels: Union[List[Dict[str, VastuJsonValue]], Dict[str, VastuJsonValue]]

class VastuFloorLevelAnalysisRequest(_VastuFloorLevelAnalysisRequestOptional):
    pass

class _VastuFusionChartRequestOptional(TypedDict, total=False):
    timezone: str
    facing: str

class VastuFusionChartRequest(_VastuFusionChartRequestOptional):
    datetime: str
    latitude: float
    longitude: float

class _VastuMandalaProject81PadaRequestOptional(TypedDict, total=False):
    bearingDeg: float
    doorXY: List[float]

class VastuMandalaProject81PadaRequest(_VastuMandalaProject81PadaRequestOptional):
    plotPolygon: List[List[float]]

class _VastuMandalaProject9ZoneRequestOptional(TypedDict, total=False):
    bearingDeg: float
    doorXY: List[float]

class VastuMandalaProject9ZoneRequest(_VastuMandalaProject9ZoneRequestOptional):
    plotPolygon: List[List[float]]

class _VastuMandalaProjectBrahmasthanRequestOptional(TypedDict, total=False):
    bearingDeg: float
    doorXY: List[float]

class VastuMandalaProjectBrahmasthanRequest(_VastuMandalaProjectBrahmasthanRequestOptional):
    plotPolygon: List[List[float]]

class VastuMultiStoreyFloorRulesRequest(TypedDict):
    floors: int

class _VastuPlacementBalconyRequestOptional(TypedDict, total=False):
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
    direction: str
    zone: str
    pada: int

class VastuPlacementMainGateRequest(_VastuPlacementMainGateRequestOptional):
    facing: str

class _VastuPlacementOverheadTankRequestOptional(TypedDict, total=False):
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
    zone: str
    direction: str
    proposedZone: str
    proposedDirection: str
    placement: str
    latitude: float
    longitude: float

class VastuPlacementWindowRequest(_VastuPlacementWindowRequestOptional):
    pass

class _VastuPlanAnalyzeRequestOptional(TypedDict, total=False):
    plot: Dict[str, VastuJsonValue]
    zoneResolution: Literal[8, 16, 32]

class VastuPlanAnalyzeRequest(_VastuPlanAnalyzeRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuPlanFromRequirementsRequestOptional(TypedDict, total=False):
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
    plot: Dict[str, VastuJsonValue]
    includeSvg: bool

class VastuPlanOptimizeRequest(_VastuPlanOptimizeRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class VastuPlanReportRequestBrand(TypedDict, total=False):
    reportTitle: str
    generatedFor: str

class _VastuPlanReportRequestOptional(TypedDict, total=False):
    plot: Dict[str, VastuJsonValue]
    format: Literal["json", "html"]
    brand: VastuPlanReportRequestBrand
    reportTitle: str
    generatedFor: str
    tenantName: str

class VastuPlanReportRequest(_VastuPlanReportRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuPlanUploadRequestOptional(TypedDict, total=False):
    rooms: List[Dict[str, VastuJsonValue]]
    layout: Dict[str, VastuJsonValue]
    asciiGrid: str
    plot: Dict[str, VastuJsonValue]

class VastuPlanUploadRequest(_VastuPlanUploadRequestOptional):
    pass

class _VastuPlotExtensionsCutsRequestOptional(TypedDict, total=False):
    plotPolygon: List[List[float]]
    length: float
    width: float

class VastuPlotExtensionsCutsRequest(_VastuPlotExtensionsCutsRequestOptional):
    pass

class _VastuPlotOrientationRequestOptional(TypedDict, total=False):
    facingBearingDeg: float
    bearingDeg: float

class VastuPlotOrientationRequest(_VastuPlotOrientationRequestOptional):
    pass

class _VastuPlotRatioRequestOptional(TypedDict, total=False):
    bearingDeg: float
    doorXY: List[float]

class VastuPlotRatioRequest(_VastuPlotRatioRequestOptional):
    plotPolygon: List[List[float]]

class _VastuPlotRoadOrientationRequestOptional(TypedDict, total=False):
    roads: List[str]
    roadSides: List[str]
    veedhiShoola: str
    tPointFrom: str
    roadThrustFrom: str

class VastuPlotRoadOrientationRequest(_VastuPlotRoadOrientationRequestOptional):
    pass

class _VastuPlotShapeRequestOptional(TypedDict, total=False):
    bearingDeg: float
    doorXY: List[float]

class VastuPlotShapeRequest(_VastuPlotShapeRequestOptional):
    plotPolygon: List[List[float]]

class _VastuPlotSlopeRequestOptional(TypedDict, total=False):
    slopeDirection: str
    lowSide: str
    lowCorner: str
    slopeBearingDeg: float

class VastuPlotSlopeRequest(_VastuPlotSlopeRequestOptional):
    pass

class _VastuRoomBedroomRequestOptional(TypedDict, total=False):
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
    plot: Dict[str, VastuJsonValue]

class VastuScoreComplianceIndexRequest(_VastuScoreComplianceIndexRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuScoreOverallRequestOptional(TypedDict, total=False):
    plot: Dict[str, VastuJsonValue]

class VastuScoreOverallRequest(_VastuScoreOverallRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuScoreZoneWiseRequestOptional(TypedDict, total=False):
    plot: Dict[str, VastuJsonValue]

class VastuScoreZoneWiseRequest(_VastuScoreZoneWiseRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedCommercialRequestOptional(TypedDict, total=False):
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedCommercialRequest(_VastuSpecializedCommercialRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedEducationalRequestOptional(TypedDict, total=False):
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedEducationalRequest(_VastuSpecializedEducationalRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedFactoryRequestOptional(TypedDict, total=False):
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedFactoryRequest(_VastuSpecializedFactoryRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedHospitalRequestOptional(TypedDict, total=False):
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedHospitalRequest(_VastuSpecializedHospitalRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedResidentialRequestOptional(TypedDict, total=False):
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedResidentialRequest(_VastuSpecializedResidentialRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedRestaurantRequestOptional(TypedDict, total=False):
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedRestaurantRequest(_VastuSpecializedRestaurantRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuSpecializedTempleRequestOptional(TypedDict, total=False):
    facing: str
    buildingFacing: str
    lat: float
    lon: float

class VastuSpecializedTempleRequest(_VastuSpecializedTempleRequestOptional):
    rooms: List[Dict[str, VastuJsonValue]]

class _VastuTimingBhumiPujanRequestOptional(TypedDict, total=False):
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingBhumiPujanRequest(_VastuTimingBhumiPujanRequestOptional):
    latitude: float
    longitude: float

class _VastuTimingConstructionStartRequestOptional(TypedDict, total=False):
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingConstructionStartRequest(_VastuTimingConstructionStartRequestOptional):
    latitude: float
    longitude: float

class _VastuTimingGrihapraveshRequestOptional(TypedDict, total=False):
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingGrihapraveshRequest(_VastuTimingGrihapraveshRequestOptional):
    latitude: float
    longitude: float

class _VastuTimingVastuShantiRequestOptional(TypedDict, total=False):
    datetime: str
    date: str
    time: str
    timezone: str
    windowDays: int

class VastuTimingVastuShantiRequest(_VastuTimingVastuShantiRequestOptional):
    latitude: float
    longitude: float

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

class VastuArRoomCaptureDataCaptureOutline(TypedDict):
    polygon: List[List[float]]
    source: Literal["traced"]
    width: float
    length: float
    areaM2: float

class VastuArRoomCaptureDataCapture(TypedDict):
    captureId: str
    capturedAtEpoch: int
    device: Dict[str, VastuJsonValue]
    north: Dict[str, VastuJsonValue]
    floorIndex: int
    outline: VastuArRoomCaptureDataCaptureOutline
    originShiftM: List[float]
    roomCount: int
    openingCount: int

class VastuArRoomCaptureDataRoomsItem(TypedDict):
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

class VastuPlanAuditDataRoomByRoomItem(_VastuPlanAuditDataRoomByRoomItemOptional):
    pass

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

class VastuPlanAuditDataDefectsItem(_VastuPlanAuditDataDefectsItemOptional):
    pass

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

class VastuPlanAuditDataRemediesItem(_VastuPlanAuditDataRemediesItemOptional):
    pass

class VastuPlanAuditDataArtifact(TypedDict):
    contentType: Literal["text/html; charset=utf-8"]
    filename: Literal["vastu-report.html"]
    content: str

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
    score: int
    grade: str
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
    score: int
    grade: str
    defectCount: int
    prescribedCount: int
    defects: List[VastuRemedyComparisonDataAfterDefectsItem]

class VastuRemedyComparisonDataAfter(_VastuRemedyComparisonDataAfterOptional):
    pass

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

class VastuSunPathDataInput(TypedDict):
    lat: float
    lon: float
    date: str

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

class VastuArAnchorRecommendationsData(TypedDict):
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

class VastuArDeityIconsData(TypedDict):
    icons: List[VastuArDeityIconsDataIconsItem]
    verified: Literal[False]
    provenance: VastuJsonValue

class VastuArHeatmapRasterData(TypedDict):
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

class VastuArRoomCaptureData(TypedDict):
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

class VastuArScanQualityData(TypedDict):
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

class VastuArTrueNorthData(TypedDict):
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

class VastuArYantraMeshesData(TypedDict):
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

class VastuArZoneTexturesData(TypedDict):
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

class VastuAssessmentBatchData(TypedDict):
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

class VastuCatalogReferenceData(_VastuCatalogReferenceDataOptional):
    verified: bool
    referenceVersion: str

class _VastuComplianceIndexDataOptional(TypedDict, total=False):
    basis: str
    defectsSummary: Dict[str, VastuJsonValue]
    indexLabel: str
    indexScale: List[Dict[str, VastuJsonValue]]
    indexScaleNote: str
    indexType: str
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    system: str
    tradition: str
    verdict: str

class VastuComplianceIndexData(_VastuComplianceIndexDataOptional):
    score: float
    complianceIndex: str
    drivingDefects: List[VastuComplianceIndexDataDrivingDefectsItem]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool
    scoring: VastuComplianceIndexDataScoring

class _VastuDetailedFloorPlanAuditDataOptional(TypedDict, total=False):
    bearingAssumedNorth: bool
    gradeScale: Dict[str, VastuJsonValue]

class VastuDetailedFloorPlanAuditData(_VastuDetailedFloorPlanAuditDataOptional):
    score: float
    grade: str
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

class VastuDirectionCorrectData(_VastuDirectionCorrectDataOptional):
    input: Dict[str, VastuJsonValue]
    magneticBearingDeg: Optional[float]
    declinationDeg: float
    trueBearingDeg: Optional[float]
    correctedZone: str
    sources: List[str]
    verified: bool

class _VastuDirectionDeclinationDataOptional(TypedDict, total=False):
    declinationCoverage: str

class VastuDirectionDeclinationData(_VastuDirectionDeclinationDataOptional):
    lat: float
    lon: float
    date: str
    declinationDeg: float
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

class VastuDirectionsReferenceData(_VastuDirectionsReferenceDataOptional):
    directionCount: int
    directions: List[VastuDirectionsReferenceDataDirectionsItem]
    verified: bool
    referenceVersion: str

class _VastuElementBalanceDataOptional(TypedDict, total=False):
    meta: Dict[str, VastuJsonValue]
    method: str
    summary: str
    system: str

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

class VastuElementDistributionData(_VastuElementDistributionDataOptional):
    elementDistribution: List[Dict[str, VastuJsonValue]]
    idealModel: Dict[str, VastuJsonValue]
    dominantElement: str
    deficientElements: List[str]
    excessElements: List[str]
    zoneBreakdown: List[Dict[str, VastuJsonValue]]

class VastuEntrancePadaData(TypedDict):
    doorXY: List[float]
    plotCentroid: List[float]
    rawBearingDeg: float
    trueBearingDeg: float
    pada: VastuEntrancePadaDataPada
    edgeRefined: bool
    sources: List[str]
    verified: bool

class _VastuEntranceRecommendDataOptional(TypedDict, total=False):
    facingCaution: Optional[Dict[str, VastuJsonValue]]
    meta: Dict[str, VastuJsonValue]
    method: str
    poojaPrescribedHere: Optional[Dict[str, VastuJsonValue]]
    prescribedRoomsAtFacing: List[str]
    system: str

class VastuEntranceRecommendData(_VastuEntranceRecommendDataOptional):
    facing: Dict[str, VastuJsonValue]
    bestEntrancePada: Dict[str, VastuJsonValue]
    recommendedPadas: List[Dict[str, VastuJsonValue]]
    avoidPadas: List[Dict[str, VastuJsonValue]]

class _VastuFloorPlanAuditDataOptional(TypedDict, total=False):
    gradeScale: Dict[str, VastuJsonValue]
    textParse: VastuFloorPlanAuditDataTextParse

class VastuFloorPlanAuditData(_VastuFloorPlanAuditDataOptional):
    score: float
    grade: str
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

class VastuFusionChartData(_VastuFusionChartDataOptional):
    ascendant: Dict[str, VastuJsonValue]
    grahaDirections: List[Dict[str, VastuJsonValue]]
    favourableDirections: List[Dict[str, VastuJsonValue]]
    cautionDirections: List[str]
    methodology: Dict[str, VastuJsonValue]
    summary: str
    sources: List[str]

class _VastuLevelAnalysisDataOptional(TypedDict, total=False):
    idealOrdering: str
    input: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]
    method: str
    principle: str
    system: str
    tradition: str

class VastuLevelAnalysisData(_VastuLevelAnalysisDataOptional):
    idealLevels: List[Dict[str, VastuJsonValue]]
    observedAnalysis: Optional[Dict[str, VastuJsonValue]]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool

class _VastuMainGateDataOptional(TypedDict, total=False):
    padaVerdict: Dict[str, VastuJsonValue]
    feature: str
    meta: Dict[str, VastuJsonValue]
    method: str
    remedyType: str
    system: str
    verified: bool

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

class VastuMandalaReferenceData(_VastuMandalaReferenceDataOptional):
    verified: bool
    referenceVersion: str

class _VastuObstructionDataOptional(TypedDict, total=False):
    rangeClassification: str
    rangeSource: str

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
    gradeLabel: str
    indexType: str
    input: Dict[str, VastuJsonValue]
    maxScore: float
    meta: Dict[str, VastuJsonValue]
    method: str
    scoreBreakdown: Dict[str, VastuJsonValue]
    system: str
    tradition: str
    verdict: str

class VastuOverallScoreData(_VastuOverallScoreDataOptional):
    score: float
    grade: str
    placements: List[VastuOverallScoreDataPlacementsItem]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool
    scoring: VastuOverallScoreDataScoring

class _VastuPlacementDataOptional(TypedDict, total=False):
    deityClassification: Literal["classical", "convention"]
    deitySource: str
    elementSource: str
    tradition: str

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
    tracedGeometry: Dict[str, VastuJsonValue]
    gradeLabel: str
    scoreDisclaimer: str
    artifact: VastuPlanAuditDataArtifact

class VastuPlanAuditData(_VastuPlanAuditDataOptional):
    system: str
    method: str
    input: Dict[str, VastuJsonValue]
    facing: Dict[str, VastuJsonValue]
    plotShape: Dict[str, VastuJsonValue]
    overallScore: float
    grade: str
    summary: str
    zoneCompliance: List[Dict[str, VastuJsonValue]]
    roomByRoom: List[VastuPlanAuditDataRoomByRoomItem]
    defects: List[VastuPlanAuditDataDefectsItem]
    remedies: List[VastuPlanAuditDataRemediesItem]
    elementBalance: Dict[str, VastuJsonValue]
    sources: List[str]
    provenance: Dict[str, VastuJsonValue]
    meta: Dict[str, VastuJsonValue]

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

class VastuPlanGenerateData(_VastuPlanGenerateDataOptional):
    plot: Dict[str, VastuJsonValue]
    entrance: Dict[str, VastuJsonValue]
    rooms: List[Dict[str, VastuJsonValue]]
    mandala: Dict[str, VastuJsonValue]
    compliance: Dict[str, VastuJsonValue]
    openings: Dict[str, VastuJsonValue]
    variants: List[Dict[str, VastuJsonValue]]
    recommendedVariant: str

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

class VastuPlotExtensionsCutsData(_VastuPlotExtensionsCutsDataOptional):
    directions: List[Dict[str, VastuJsonValue]]
    extensions: List[str]
    cuts: List[Dict[str, VastuJsonValue]]
    severeCuts: List[Dict[str, VastuJsonValue]]
    sources: List[str]
    verified: bool

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

class VastuPlotOrientationData(_VastuPlotOrientationDataOptional):
    facing: str
    grade: str
    doorPadaScheme: Dict[str, VastuJsonValue]
    sources: List[str]
    verified: bool

class VastuPlotRatioData(TypedDict):
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

class VastuPlotShapeData(TypedDict):
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

class VastuPlotSlopeData(_VastuPlotSlopeDataOptional):
    downSlopeDirection: str
    classicalReference: Dict[str, VastuJsonValue]
    sources: List[str]
    verified: bool

class _VastuRemedyComparisonDataOptional(TypedDict, total=False):
    meta: Dict[str, VastuJsonValue]
    method: str
    system: str
    tradition: str
    verified: bool

class VastuRemedyComparisonData(_VastuRemedyComparisonDataOptional):
    before: VastuRemedyComparisonDataBefore
    after: VastuRemedyComparisonDataAfter
    scoreDelta: float
    scoring: Dict[str, VastuJsonValue]
    verdict: str
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

class VastuScanStoredData(TypedDict):
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

class VastuScansDeleteData(_VastuScansDeleteDataOptional):
    scanId: str
    deleted: bool
    deletionScope: str
    persistence: Literal["account-store", "preview-only"]

class _VastuScansListDataOptional(TypedDict, total=False):
    paginationNote: str
    previewNote: str

class VastuScansListData(_VastuScansListDataOptional):
    scans: List[VastuJsonValue]
    nextCursor: Optional[str]
    persistence: Literal["account-store", "preview-only"]

class _VastuScansRetrieveDataOptional(TypedDict, total=False):
    previewNote: str

class VastuScansRetrieveData(_VastuScansRetrieveDataOptional):
    scan: VastuJsonValue
    persistence: Literal["account-store", "preview-only"]

class _VastuScansSaveDataOptional(TypedDict, total=False):
    retentionNote: str
    previewNote: str

class VastuScansSaveData(_VastuScansSaveDataOptional):
    scan: VastuJsonValue
    replayed: bool
    persistence: Literal["account-store", "preview-only"]

class _VastuScansTimelapseDataOptional(TypedDict, total=False):
    previewNote: str

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

class VastuSpecializedAuditData(_VastuSpecializedAuditDataOptional):
    system: str
    method: str
    buildingType: str
    score: float
    grade: str
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

class VastuSunPathData(TypedDict):
    input: VastuSunPathDataInput
    sunriseUtc: str
    sunriseAzimuthDeg: float
    solarNoonUtc: str
    solarNoonAzimuthDeg: float
    solarNoonElevationDeg: float
    sunsetUtc: str
    sunsetAzimuthDeg: float
    declinationDeg: float
    arc: List[Dict[str, VastuJsonValue]]
    sources: List[str]
    verified: bool

class _VastuTimingDataOptional(TypedDict, total=False):
    foundationRite: Dict[str, VastuJsonValue]

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

class VastuWallAnalysisData(_VastuWallAnalysisDataOptional):
    idealWalls: List[Dict[str, VastuJsonValue]]
    observedAnalysis: Optional[Dict[str, VastuJsonValue]]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool

class _VastuZoneReferenceDataOptional(TypedDict, total=False):
    system: str
    method: str
    note: str
    tradition: str
    meta: Dict[str, VastuJsonValue]

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
    strongestZone: str
    system: str
    tradition: str
    weakestZone: str
    zoneWeightingNote: str

class VastuZoneWiseScoreData(_VastuZoneWiseScoreDataOptional):
    zones: List[VastuZoneWiseScoreDataZonesItem]
    sources: List[Dict[str, VastuJsonValue]]
    verified: bool
    overallGrade: str
    overallScore: float
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

VastuAnyResponse = Union[VastuScansTimelapseResponse, VastuScansDeleteResponse, VastuScansListResponse, VastuScansRetrieveResponse, VastuScansSaveResponse, VastuArDeityIconsResponse, VastuArRoomCaptureResponse, VastuArYantraMeshesResponse, VastuArZoneTexturesResponse, VastuArAnchorRecommendationsResponse, VastuArHeatmapRasterResponse, VastuAssessmentsBatchResponse, VastuArScanQualityResponse, VastuArTrueNorthCalibrateResponse, VastuAssessmentsResponse, VastuAuditFloorPlanResponse, VastuAuditFloorPlanDetailedResponse, VastuAuditSingleRoomResponse, VastuCompareBeforeAfterRemedyResponse, VastuCompoundWallAnalysisResponse, VastuDirectionAuspiciousFacingResponse, VastuDirectionCorrectResponse, VastuDirectionDeclinationResponse, VastuDirectionSunPathResponse, VastuDirectionZoneFromBearingResponse, VastuElementsBalanceSuggestResponse, VastuElementsDistributionResponse, VastuEntranceObstructionCheckResponse, VastuEntrancePadaResponse, VastuEntranceRecommendResponse, VastuFloorLevelAnalysisResponse, VastuFusionChartResponse, VastuMandalaProject81PadaResponse, VastuMandalaProject9ZoneResponse, VastuMandalaProjectBrahmasthanResponse, VastuMultiStoreyFloorRulesResponse, VastuPlacementBalconyResponse, VastuPlacementBorewellResponse, VastuPlacementGardenResponse, VastuPlacementGeneratorElectricalResponse, VastuPlacementMainGateResponse, VastuPlacementOverheadTankResponse, VastuPlacementSepticTankResponse, VastuPlacementTreeResponse, VastuPlacementWellResponse, VastuPlacementWindowResponse, VastuPlanAnalyzeResponse, VastuPlanFromRequirementsResponse, VastuPlanGenerateResponse, VastuPlanOptimizeResponse, VastuPlanReportResponse, VastuPlanUploadResponse, VastuPlotExtensionsCutsResponse, VastuPlotOrientationResponse, VastuPlotRatioResponse, VastuPlotRoadOrientationResponse, VastuPlotShapeResponse, VastuPlotSlopeResponse, VastuReferenceColorsByZoneResponse, VastuReferenceDefectsCatalogResponse, VastuReferenceDirections16Response, VastuReferenceDirections32Response, VastuReferenceDirections8Response, VastuReferenceGateObstructionsResponse, VastuReferenceMandala45DevatasResponse, VastuReferenceMandala64PadaResponse, VastuReferenceMandala9ZoneResponse, VastuReferenceMaterialsByZoneResponse, VastuReferenceRemediesCatalogResponse, VastuRoomBedroomResponse, VastuRoomDiningResponse, VastuRoomKitchenResponse, VastuRoomLivingResponse, VastuRoomPoojaResponse, VastuRoomStaircaseResponse, VastuRoomStoreResponse, VastuRoomStudyResponse, VastuRoomToiletResponse, VastuRoomWaterStorageResponse, VastuScoreComplianceIndexResponse, VastuScoreOverallResponse, VastuScoreZoneWiseResponse, VastuSpecializedCommercialResponse, VastuSpecializedEducationalResponse, VastuSpecializedFactoryResponse, VastuSpecializedHospitalResponse, VastuSpecializedResidentialResponse, VastuSpecializedRestaurantResponse, VastuSpecializedTempleResponse, VastuTimingBhumiPujanResponse, VastuTimingConstructionStartResponse, VastuTimingGrihapraveshResponse, VastuTimingVastuShantiResponse]
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
    """A requests.Session that also drops the legacy ``X-API-Key`` header on any
    redirect where requests itself would strip ``Authorization`` — i.e. a
    cross-origin redirect or an HTTPS->HTTP downgrade.

    Without this, requests strips ``Authorization`` on a cross-host redirect but
    forwards a manually-set ``X-API-Key`` to the redirect destination, leaking
    the API key to whatever origin a 3xx points at. Same-origin redirects keep
    both headers.
    """

    def rebuild_auth(self, prepared_request, response):
        super().rebuild_auth(prepared_request, response)
        original = getattr(response.request, "url", None)
        target = getattr(prepared_request, "url", None)
        if original and target and self.should_strip_auth(original, target):
            # CaseInsensitiveDict.pop matches any header casing.
            prepared_request.headers.pop("X-API-Key", None)
            prepared_request.headers.pop("Authorization", None)


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
        allow_insecure_http: bool = False
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
        self.cache_enabled = cache_enabled
        self.language = language

        # Configure session with retries. _VedikaSession also strips the key on
        # cross-origin / downgrade redirects (see the class docstring).
        #
        # urllib3's Retry() defaults `allowed_methods` to
        # the idempotent-by-definition set (GET/HEAD/PUT/DELETE/OPTIONS/TRACE),
        # which EXCLUDES POST. Every paid Vastu operation is POST, so those
        # calls were never retried no matter what max_retries said. POST is
        # only safe to retry because `_request` (below) now attaches a client
        # `Idempotency-Key` header for billing deduplication. The SAME prepared request, header
        # included, is what urllib3 re-sends on each attempt, so the key is
        # identical across retries of one logical call.
        self.session = _VedikaSession()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=frozenset(["GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE"]),
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # X-API-Key is DEPRECATED at server level
        # (sunset 2026-10-20). Send Authorization: Bearer as primary auth.
        # Keep X-API-Key for backwards-compat with pre-v2.3 server middleware.
        # User-Agent synced to actual package version.
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,  # DEPRECATED — remove after 2026-10-20
            "User-Agent": "vedika-python-sdk/3.0.10"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"

        # Mutating requests and the twelve billed Vastu GET operations need a
        # client key: even a reference-table read deducts a charge. The server
        # dedupes a retried charge keyed on this
        # header. Generated ONCE per logical call and passed to `session.request`,
        # which urllib3 re-sends verbatim on every retry of the SAME prepared
        # request — the key is identical across attempts by construction.
        batch = endpoint.split("?", 1)[0] in (
            "/v2/vastu/assessments/batch", "/v2/astrology/vastu/assessments/batch"
        )
        if (batch or idempotency_key is not None) and (
            not isinstance(idempotency_key, str) or not idempotency_key.strip()
        ):
            raise ValueError("A nonblank caller-retained Idempotency-Key is required")
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        billed_vastu_get = False
        if method.upper() == "GET":
            path = endpoint.split("?", 1)[0]
            for prefix in ("/v2/vastu/", "/v2/astrology/vastu/"):
                if path.startswith(prefix):
                    contract = _VASTU_OPERATION_CONTRACTS.get(path[len(prefix):])
                    billed_vastu_get = bool(contract and contract["method"] in ("GET", "GET_OR_POST"))
                    break
        has_client_key = any(name.lower() in ("idempotency-key", "x-idempotency-key", "x-request-id")
                             for name in self.session.headers)
        if (method.upper() in ("POST", "PUT", "PATCH", "DELETE") or billed_vastu_get) and not has_client_key and headers is None:
            headers = {"Idempotency-Key": str(uuid.uuid4())}

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
                headers=headers,
            )

            if response.status_code >= 400:
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                if not isinstance(body, dict):
                    body = {}
                error = body.get("error")
                message = next((value for value in (
                    body.get("message"), error,
                    error.get("message") if isinstance(error, dict) else None,
                ) if isinstance(value, str) and value.strip()), None)
                if message is not None:
                    message = message.replace(self.api_key, "[REDACTED]")
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                if response.status_code == 402:
                    if body.get("code") == "SUBSCRIPTION_EXPIRED":
                        raise SubscriptionExpiredError(message or "Subscription expired")
                    raise InsufficientCreditsError(message or "Payment required")
                if response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded. Please wait a moment.")
                if response.status_code == 422:
                    raise ValidationError(message or "Invalid input")
                raise VedikaAPIError(message or "API request failed", status_code=response.status_code)

            return response.json()

        except requests.exceptions.Timeout:
            raise VedikaAPIError("Request timed out. For complex queries, try increasing timeout.")
        except requests.exceptions.RequestException:
            raise VedikaAPIError("Request failed. Check the connection and retry.") from None

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
        conversation_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: Optional[str] = None,
    ) -> QuestionResponse:
        """
        Ask a question about a Vastu report you already hold.

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
        if report is None and not conversation_id:
            raise ValueError("ask_vastu_report needs a report or a conversation_id that already holds one")
        data: Dict[str, Any] = {"question": question, "language": language or self.language}
        if report is not None:
            data["vastuContext"] = {"report": report}
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

        # Route through self.session (a _VedikaSession) so the redirect guard
        # applies — a top-level requests.post() bypasses rebuild_auth and would
        # forward X-API-Key across a cross-origin redirect.
        with self.session.post(url, json=data, stream=True, timeout=self.timeout) as response:
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
    # Vastu (82 logical operations, mounted under two public aliases)
    # Mirrors sdks/flutter's Vastu surface. Vastu takes a BUILDING (plot
    # polygon, room list, compass zone) — NEVER a birth chart. Every path
    # below is pinned to the 82 mounted logical routes in vedika-v2/src/vastu.rs.
    # ═══════════════════════════════════════════

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
        # reference/* tables (11, incl. gate-obstructions) are GET-only
        # (POST -> 405); direction/declination is a GET+POST dual whose
        # verified path is GET-with-query. Everything else is POST. Mirrors
        # vedika-v2/src/vastu.rs GET/dual route sets.
        if path.startswith("reference/") or path == "direction/declination":
            return self._request(
                "GET", f"/v2/astrology/vastu/{path}", params=params, idempotency_key=idempotency_key
            )
        return self._request(
            "POST", f"/v2/astrology/vastu/{path}", data=params, idempotency_key=idempotency_key
        )

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
    def vastu_operation(self, operation: Literal[VastuOperation.AR_HEATMAP_RASTER], params: VastuArHeatmapRasterRequest, *, idempotency_key: Optional[str] = None) -> VastuArHeatmapRasterResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_ANCHOR_RECOMMENDATIONS], params: VastuArAnchorRecommendationsRequest, *, idempotency_key: Optional[str] = None) -> VastuArAnchorRecommendationsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_ZONE_TEXTURES], params: VastuArZoneTexturesRequest, *, idempotency_key: Optional[str] = None) -> VastuArZoneTexturesResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_YANTRA_MESHES], params: VastuArYantraMeshesRequest, *, idempotency_key: Optional[str] = None) -> VastuArYantraMeshesResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_DEITY_ICONS], params: VastuArDeityIconsRequest, *, idempotency_key: Optional[str] = None) -> VastuArDeityIconsResponse: ...

    @overload
    def vastu_operation(self, operation: Literal[VastuOperation.AR_ROOM_CAPTURE], params: VastuArRoomCaptureRequest, *, idempotency_key: Optional[str] = None) -> VastuArRoomCaptureResponse: ...

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
        if path.startswith("reference/") or path == "direction/declination":
            result = self._request("GET", f"/v2/astrology/vastu/{path}", params=payload, idempotency_key=idempotency_key)
        else:
            result = self._request("POST", f"/v2/astrology/vastu/{path}", data=payload, idempotency_key=idempotency_key)
        return cast(VastuAnyResponse, result)

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

    def vastu_mandala_project(self, scheme: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Project a mandala onto a plot.

        Args:
            scheme: "9-zone", "81-pada", or "brahmasthan"
            params: Building payload, e.g. {"plotPolygon": [...], "bearingDeg": 0}
        """
        return self._request(
            "POST", f"/v2/astrology/vastu/mandala/project/{scheme}", data=params
        )

    def vastu_entrance_pada(
        self, params: VastuEntrancePadaRequest
    ) -> VastuEntrancePadaResponse:
        """Door-pada classifier.

        Args:
            params: Building payload, e.g. {"plotPolygon": [...], "doorXY": [...],
                "bearingDeg": 0}
        """
        return self.vastu_operation(VastuOperation.ENTRANCE_PADA, params)

    def vastu_entrance_recommend(
        self, params: VastuEntranceRecommendRequest
    ) -> VastuEntranceRecommendResponse:
        """Entrance recommendation.

        Args:
            params: Building payload, e.g. {"plot": {...}}
        """
        return self.vastu_operation(VastuOperation.ENTRANCE_RECOMMEND, params)

    def vastu_ar_scan_quality(
        self, params: VastuArScanQualityRequest
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
        return self.vastu_operation(VastuOperation.AR_SCAN_QUALITY, params)

    def vastu_ar_true_north_calibrate(
        self, params: VastuArTrueNorthCalibrateRequest
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
        return self.vastu_operation(VastuOperation.AR_TRUE_NORTH_CALIBRATE, params)

    def vastu_room(self, room_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Single-room placement, e.g. vastu_room("kitchen", {"zone": "southeast"}).

        Args:
            room_type: kitchen, bedroom, pooja, toilet, staircase, study, living,
                dining, store, or water-storage
            params: Building/room payload
        """
        return self._request("POST", f"/v2/astrology/vastu/room/{room_type}", data=params)

    def vastu_placement(self, feature: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Site placement, e.g. vastu_placement("borewell", {"zone": "north-east"}).

        Args:
            feature: balcony, borewell, garden, generator-electrical, main-gate,
                overhead-tank, septic-tank, tree, well, or window
            params: Building/site payload
        """
        return self._request("POST", f"/v2/astrology/vastu/placement/{feature}", data=params)

    def vastu_audit(self, kind: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compliance audit.

        Args:
            kind: "single-room", "floor-plan", or "floor-plan-detailed"
            params: Building payload, e.g. {"rooms": [...], "plot": {...}}
        """
        return self._request("POST", f"/v2/astrology/vastu/audit/{kind}", data=params)

    def vastu_listing_assessment(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
        return self._request("POST", "/v2/astrology/vastu/assessments", data=params)

    def vastu_score(self, kind: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vastu score.

        Args:
            kind: "overall", "zone-wise", or "compliance-index"
            params: Building payload
        """
        return self._request("POST", f"/v2/astrology/vastu/score/{kind}", data=params)

    def vastu_plan_generate(
        self, params: VastuPlanGenerateRequest
    ) -> VastuPlanGenerateResponse:
        """Generate up to 3 ranked floor plans from a plot + room programme.

        Args:
            params: Building payload, e.g. {"plot": {...}, "rooms": [...]}
        """
        return self.vastu_operation(VastuOperation.PLAN_GENERATE, params)

    def vastu_plan_from_requirements(
        self, params: VastuPlanFromRequirementsRequest
    ) -> VastuPlanFromRequirementsResponse:
        """Generate a floor plan from a high-level brief (BHK, bathrooms, parking...).

        Args:
            params: Requirements payload, e.g. {"bhk": 3, "bathrooms": 2, "plot": {...}}
        """
        return self.vastu_operation(VastuOperation.PLAN_FROM_REQUIREMENTS, params)

    def vastu_declination(
        self, lat: float, lon: float, date: Optional[str] = None
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
        return self.vastu_operation(VastuOperation.DIRECTION_DECLINATION, params)

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
            # Route through self.session (a _VedikaSession) so the redirect guard
            # applies — a top-level requests.post() bypasses rebuild_auth and would
            # forward X-API-Key across a cross-origin redirect. Content-Type:
            # None drops the session's JSON default so requests sets the multipart
            # boundary; the session still supplies auth headers. Idempotency-Key is
            # required here too: POST is now auto-retried by the mounted adapter
            # (see __init__), and voice is a billed call.
            response = self.session.post(
                url,
                files=files,
                data=data,
                headers={"Content-Type": None, "Idempotency-Key": str(uuid.uuid4())},
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
