"""Vastu transport + credential-routing tests.

Covers:
- generic vastu(op) verb parity: reference/* and direction/declination -> GET
  (params as query), everything else -> POST (params as body);
- the API key is NEVER forwarded across a cross-origin redirect (including legacy authentication headers);
- the base_url origin policy (official HTTPS or loopback HTTP; no remote-origin opt-in).
"""

import threading
from typing import get_args, get_type_hints
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock

import pytest

from vedika.client import VedikaClient
from vedika.exceptions import VedikaAPIError

# The 11 GET-only reference tables + the GET+POST dual, from the Rust router
# (VASTU_GET_REFERENCE_ROUTES + VASTU_DUAL_ROUTE in vedika-v2/src/vastu.rs).
GET_OPS = [
    "reference/directions/8",
    "reference/directions/16",
    "reference/directions/32",
    "reference/mandala/9-zone",
    "reference/mandala/45-devatas",
    "reference/mandala/64-pada",
    "reference/defects/catalog",
    "reference/remedies/catalog",
    "reference/colors-by-zone",
    "reference/materials-by-zone",
    "reference/gate-obstructions",
    "direction/declination",
]
POST_OPS = ["score/overall", "placement/borewell", "entrance/pada", "plan/analyze"]


def test_typed_inventory_exposes_every_mounted_logical_operation_once():
    operations = VedikaClient.VASTU_OPERATIONS
    assert len(operations) == 147
    assert len(set(operations)) == 147
    assert {
        "reference/gate-obstructions",
        "entrance/obstruction-check",
        "direction/sun-path",
        "ar/true-north-calibrate",
        "assessments",
        "plan/import-image",
        "plan/import-pdf",
        "ar/capture-merge",
        "plot/from-survey",
    } <= set(operations)


def test_assessments_types_match_canonical_request_and_optional_billing_response():
    from vedika.client import (
        VastuAssessmentBadgeEligibility,
        VastuAssessmentData,
        VastuAssessmentRoom,
        VastuAssessmentsRequest,
        VastuAssessmentsResponse,
    )

    assert VastuAssessmentsRequest.__required_keys__ == frozenset({"inputSource"})
    assert VastuAssessmentRoom.__required_keys__ == frozenset({"roomType", "zone"})
    assert {"plotPolygon", "doorXY", "bearingDeg"} <= set(get_type_hints(VastuAssessmentsRequest))
    assert {"inputSource", "badge", "eligible", "variant", "reason"} == set(
        VastuAssessmentBadgeEligibility.__required_keys__
    )
    assert "billing" not in VastuAssessmentsResponse.__required_keys__
    assert {
        "system", "method", "status", "confidence", "badgeEligibility",
        "confidenceBasis", "meta",
    } == set(VastuAssessmentData.__required_keys__)
    assert type(None) in get_args(get_type_hints(VastuAssessmentData)["scanQuality"])

    # Both the billable assessment and the valid unbilled insufficient-data
    # response are representable by the public SDK types.
    request: VastuAssessmentsRequest = {
        "inputSource": "plan-derived",
        "rooms": [{"roomType": "kitchen", "zone": "SE"}],
        "plotPolygon": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]],
        "doorXY": [5.0, 0.0],
    }
    assert request["rooms"][0]["roomType"] == "kitchen"


def test_each_operation_exposes_generated_contract_metadata():
    contracts = VedikaClient.VASTU_OPERATION_CONTRACTS
    assert len(contracts) == 147
    for operation, contract in contracts.items():
        assert contract["method"] in {"GET", "POST", "GET_OR_POST"}
        assert contract["requestSchema"] is None or contract["requestSchema"].startswith("Vastu")
        assert contract["requestSchema"] != "VastuOperationRequest"
        assert contract["responseSchema"].startswith("Vastu")
        assert contract["responseSchema"].endswith("Response")
        assert contract["responseSchema"] != "VastuOperationResponse"
        assert contract["auth"] == "apiKey"
        assert 401 in contract["errors"]
        assert len(contract["errors"]) == len(set(contract["errors"]))
        assert not operation.startswith("/v2/")


def test_concrete_named_helpers_keep_exact_types_and_typed_dispatch():
    def type_name(annotation):
        return getattr(annotation, "__name__", str(annotation))

    typed_helpers = {
        "vastu_entrance_pada": ("VastuEntrancePadaRequest", "VastuEntrancePadaResponse"),
        "vastu_entrance_recommend": (
            "VastuEntranceRecommendRequest",
            "VastuEntranceRecommendResponse",
        ),
        "vastu_ar_scan_quality": ("VastuArScanQualityRequest", "VastuArScanQualityResponse"),
        "vastu_ar_true_north_calibrate": (
            "VastuArTrueNorthCalibrateRequest",
            "VastuArTrueNorthCalibrateResponse",
        ),
        "vastu_plan_generate": ("VastuPlanGenerateRequest", "VastuPlanGenerateResponse"),
        "vastu_plan_from_requirements": (
            "VastuPlanFromRequirementsRequest",
            "VastuPlanFromRequirementsResponse",
        ),
    }
    for name, (request_type, response_type) in typed_helpers.items():
        annotations = getattr(VedikaClient, name).__annotations__
        assert type_name(annotations["params"]) == request_type
        assert type_name(annotations["return"]) == response_type

    declination = VedikaClient.vastu_declination.__annotations__
    assert type_name(declination["lat"]) == "float"
    assert type_name(declination["lon"]) == "float"
    assert type_name(declination["return"]) == "VastuDirectionDeclinationResponse"

    client = VedikaClient(api_key="vk_test_x")
    client._request = MagicMock(return_value={"success": True, "data": {}})
    client.vastu_entrance_pada(
        {"plotPolygon": [[0, 0], [1, 0], [1, 1]], "doorXY": [0.5, 0]}
    )
    client.vastu_entrance_recommend({"facing": "east"})
    client.vastu_plan_generate({"plot": {"width": 40, "length": 60}})
    client.vastu_plan_from_requirements({"plot": {"width": 40, "length": 60}})
    client.vastu_declination(28.61, 77.21, "2026-08-25")

    calls = client._request.call_args_list
    assert [call.args[1] for call in calls] == [
        "/v2/astrology/vastu/entrance/pada",
        "/v2/astrology/vastu/entrance/recommend",
        "/v2/astrology/vastu/plan/generate",
        "/v2/astrology/vastu/plan/from-requirements",
        "/v2/astrology/vastu/direction/declination",
    ]
    assert [call.args[0] for call in calls] == ["POST", "POST", "POST", "POST", "GET"]


def test_vastu_verb_dispatch():
    client = VedikaClient(api_key="vk_test_x")
    client._request = MagicMock(return_value={"ok": True})

    for op in GET_OPS:
        client._request.reset_mock()
        client.vastu(op, {"lat": 1, "lon": 2})
        args, kwargs = client._request.call_args
        assert args[0] == "GET", f"{op} must dispatch GET"
        assert args[1] == f"/v2/astrology/vastu/{op}"
        assert kwargs.get("params") == {"lat": 1, "lon": 2}, op
        assert kwargs.get("data") is None, f"{op} GET must not send a body"

    for op in POST_OPS:
        client._request.reset_mock()
        client.vastu(op, {"zone": "north"})
        args, kwargs = client._request.call_args
        assert args[0] == "POST", f"{op} must dispatch POST"
        assert args[1] == f"/v2/astrology/vastu/{op}"
        assert kwargs.get("data") == {"zone": "north"}, op


def test_vastu_leading_slash_normalized():
    client = VedikaClient(api_key="vk_test_x")
    client._request = MagicMock(return_value={"ok": True})
    client.vastu("/score/overall", {"zone": "north"})
    args, _ = client._request.call_args
    assert args[1] == "/v2/astrology/vastu/score/overall"


def _serve(handler_cls):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_cross_origin_redirect_is_refused_and_the_other_origin_sees_nothing():
    """A 302 to a different origin is not followed: the other origin gets no request at all."""
    seen = []

    class Collector(BaseHTTPRequestHandler):
        def _record_and_ok(self):
            seen.append(dict(self.headers))
            payload = b'{"success": true, "data": {"ok": true}}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_GET = _record_and_ok
        do_POST = _record_and_ok

        def log_message(self, *args):
            pass

    collector = _serve(Collector)
    collector_port = collector.server_address[1]

    class Redirector(BaseHTTPRequestHandler):
        def _redirect(self):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{collector_port}/collect")
            self.end_headers()

        do_GET = _redirect
        do_POST = _redirect

        def log_message(self, *args):
            pass

    redirector = _serve(Redirector)
    redirector_port = redirector.server_address[1]

    try:
        client = VedikaClient(
            api_key="vk_test_secret",
            base_url=f"http://127.0.0.1:{redirector_port}",
        )
        with pytest.raises(VedikaAPIError, match="(?i)redirect"):
            client.vastu("score/overall", {"zone": "north"})
    finally:
        collector.shutdown()
        redirector.shutdown()

    assert seen == [], "a redirect target received a request"


def test_no_top_level_requests_call_bypasses_the_session():
    """EVERY credential-bearing HTTP call must go through the client's
    _VedikaSession (which strips X-API-Key on a cross-origin redirect). A
    top-level requests.post/get/etc. bypasses rebuild_auth and leaks the key
    across redirects (the streaming and voice redirect bug)."""
    import pathlib
    import re

    src = (
        pathlib.Path(__file__).resolve().parent.parent
        / "vedika" / "client.py"
    ).read_text()
    # Strip line comments so prose that mentions requests.post() doesn't match.
    code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
    bad = re.findall(r"(?<![\w.])requests\.(?:post|get|request|put|delete|patch)\s*\(", code)
    assert not bad, f"top-level requests.* bypasses _VedikaSession (leaks key on redirect): {bad}"


def test_base_url_origin_policy():
    VedikaClient(api_key="k", base_url="https://api.vedika.io")
    VedikaClient(api_key="k", base_url="http://127.0.0.1:8080")
    VedikaClient(api_key="k", base_url="http://localhost:8080")

    with pytest.raises(ValueError):
        VedikaClient(api_key="k", base_url="http://api.vedika.io")

    # Spoof hosts that merely START with "127." are NOT loopback -> rejected.
    with pytest.raises(ValueError):
        VedikaClient(api_key="k", base_url="http://127.attacker.invalid")
    with pytest.raises(ValueError):
        VedikaClient(api_key="k", base_url="http://127.example.com")

    # The legacy opt-in cannot send credentials to a remote origin.
    with pytest.raises(ValueError):
        VedikaClient(api_key="k", base_url="http://api.vedika.io", allow_insecure_http=True)

    with pytest.raises(ValueError):
        VedikaClient(api_key="k", base_url="ftp://api.vedika.io")


def test_base_url_must_be_a_vedika_origin():
    """THE HOLE THIS CLOSES, found 2026-09-07.

    Every other rule in the guard constrains the SHAPE of the URL - scheme, no
    userinfo, bare origin. None of them constrained WHERE the key goes, so a
    perfectly well-formed `https://attacker.invalid` passed and the first
    request carried a live `vk_live_*` in both `Authorization` and `X-API-Key`
    to a host we do not operate.
    """
    # Allowed: the official API origin on its default HTTPS port.
    VedikaClient(api_key="k", base_url="https://api.vedika.io")
    # Case is not significant in a hostname.
    VedikaClient(api_key="k", base_url="https://API.Vedika.IO")

    # Refused: anywhere else, however plausible it looks.
    for hostile in [
        "https://vedika.io",
        "https://staging.api.vedika.io",
        "https://api.vedika.io.",
        "https://localhost:8443",
        "https://attacker.invalid",
        # Ends with our name but is a DIFFERENT registrable domain. A bare
        # `endswith("vedika.io")` check would have let this through.
        "https://notvedika.io",
        "https://api.notvedika.io",
        # Starts with our name; the real host is the last label.
        "https://api.vedika.io.attacker.com",
        # Our name appears, but not as the host.
        "https://attacker.invalid/api.vedika.io",
        "https://evil.example.com:8443",
    ]:
        with pytest.raises(ValueError):
            VedikaClient(api_key="k", base_url=hostile)


def test_embedded_credentials_cannot_smuggle_an_off_domain_host():
    """`https://api.vedika.io@attacker.invalid` READS as ours and RESOLVES to
    theirs. Rejected on the userinfo rule before the host rule even runs."""
    for smuggled in [
        "https://api.vedika.io@attacker.invalid",
        "https://user:pass@api.vedika.io",
    ]:
        with pytest.raises(ValueError):
            VedikaClient(api_key="k", base_url=smuggled)


# ---------------------------------------------------------------------------
# AR operations
#
# Both server prefixes are aliases of the same Rust operation inventory. The
# named helpers use the SDK's established /v2/astrology/vastu/ prefix.
# ---------------------------------------------------------------------------


def test_vastu_ar_scan_quality_posts_readings_verbatim():
    client = VedikaClient(api_key="k")
    client._request = MagicMock(return_value={"score": 88, "acceptForAudit": True})

    # Exactly the field names the live handler reads
    # (ported::vastu::ar_scan_quality). A misspelling is silently ignored by the
    # server and costs a neutral 50 on that dimension, so the test pins them.
    readings = {
        "pointCloudDensity": 850,
        "polygonClosure": True,
        "roomsTagged": True,
        "compassConfidence": 0.9,
        "gpsConfidence": 0.85,
        "scanDurationSec": 240,
        "scannedAreaM2": 60,
    }
    out = client.vastu_ar_scan_quality(readings)

    args, kwargs = client._request.call_args
    assert args[0] == "POST"
    assert args[1] == "/v2/astrology/vastu/ar/scan-quality"
    assert kwargs["data"] == readings
    assert out["acceptForAudit"] is True


def test_vastu_ar_scan_quality_forwards_a_partial_scan_unchanged():
    # An absent reading is NOT a bad reading -- the grader scores it a neutral
    # 50. The SDK must not fill in zeros, which would grade the scan as failing.
    client = VedikaClient(api_key="k")
    client._request = MagicMock(return_value={})
    client.vastu_ar_scan_quality({"pointCloudDensity": 100})
    _, kwargs = client._request.call_args
    assert kwargs["data"] == {"pointCloudDensity": 100}


def test_vastu_ar_true_north_calibrate_posts_the_sun_sighting():
    client = VedikaClient(api_key="k")
    client._request = MagicMock(return_value={"reliable": True, "offsetDeg": 2.05})

    sighting = {
        "lat": 28.61,
        "lon": 77.21,
        "datetime": "2025-12-21T03:30:00Z",
        "deviceHeadingAtSunDeg": 130.0,
    }
    out = client.vastu_ar_true_north_calibrate(sighting)

    args, kwargs = client._request.call_args
    assert args[0] == "POST"
    assert args[1] == "/v2/astrology/vastu/ar/true-north-calibrate"
    assert kwargs["data"] == sighting
    assert out["reliable"] is True


# ---------------------------------------------------------------------------
# Listing assessment
#
# /v2/astrology/vastu/assessments is a real, mounted, documented endpoint
# (web/vedika-public/openapi.json) but had no dedicated named helper -- only
# the generic vastu() escape hatch could reach it. This pins the named helper.
# ---------------------------------------------------------------------------


def test_vastu_listing_assessment_posts_to_assessments():
    client = VedikaClient(api_key="k")
    client._request = MagicMock(return_value={
        "score": 78,
        "confidence": 0.95,
        "badgeEligibility": {"inputSource": "plan-derived", "badge": "plan-derived", "eligible": True},
    })

    body = {"inputSource": "plan-derived", "rooms": [{"roomType": "kitchen", "zone": "southeast"}]}
    out = client.vastu_listing_assessment(body)

    args, kwargs = client._request.call_args
    assert args[0] == "POST"
    assert args[1] == "/v2/astrology/vastu/assessments"
    assert kwargs["data"] == body
    assert out["badgeEligibility"]["eligible"] is True

@pytest.mark.parametrize("base_url", [
    "https://attacker.invalid", "https://api.vedika.io.attacker.invalid",
    "https://api.vedika.io:8443", "https://127.0.0.1:443",
    "http://api.vedika.io", "http://127.attacker.invalid",
    "https://api.vedika.io/path", "https://api.vedika.io/?key=SECRET_SENTINEL",
    "https://user:SECRET_SENTINEL@api.vedika.io", "https://api.vedika.io:bad",
    "https://[SECRET_SENTINEL",
])
def test_credential_first_hop_rejected_before_session_creation(base_url):
    from unittest.mock import patch
    with patch("vedika.client._VedikaSession") as session:
        for allow_insecure_http in (False, True):
            with pytest.raises(ValueError) as error:
                VedikaClient(api_key="vk_test", base_url=base_url, allow_insecure_http=allow_insecure_http)
            assert "SECRET_SENTINEL" not in str(error.value)
        session.assert_not_called()

@pytest.mark.parametrize("base_url", [
    "https://api.vedika.io", "https://api.vedika.io:443/",
    "http://127.0.0.1:8080", "http://localhost:8080", "http://[::1]:8080",
])
def test_trusted_credential_first_hop(base_url):
    VedikaClient(api_key="vk_test", base_url=base_url)

def test_portfolio_named_methods_forward_exact_requests():
    client = VedikaClient(api_key="vk_test_synthetic")
    client._request = MagicMock(return_value={"success": True, "data": {}})
    for suffix, path, request in [
        ("search", "search", {"city": "Pune"}),
        ("compare", "compare", {"propertyIds": ["p1", "p2"]}),
        ("analytics", "analytics", {"tag": "rental"}),
        ("usage", "usage", {"tenantRef": "t1"}),
        ("usage_export", "usage/export", {"propertyId": "p1"}),
        ("budgets_set", "budgets/set", {"tenantRef": "t1", "capUsd": "1.21"}),
        ("budgets_get", "budgets/get", {"tenantRef": "t1"}),
    ]:
        getattr(client, "vastu_portfolio_" + suffix)(request)
        args = client._request.call_args.args
        assert args[:2] == ("POST", "/v2/astrology/vastu/portfolio/" + path)
        assert client._request.call_args.kwargs["data"] == request

def test_typed_assessment_attribution_is_optional():
    from vedika.client import VastuAssessmentsRequest
    assert {"propertyId", "tenantRef"} <= VastuAssessmentsRequest.__optional_keys__
    assert VastuAssessmentsRequest.__required_keys__ == frozenset({"inputSource"})


def test_property_collaboration_helpers_preserve_exact_route_payload_and_types():
    client = VedikaClient(api_key="vk_test_x")
    client._request = MagicMock(return_value={"success": True, "data": {}})
    payload = {"propertyId": "property-fixture", "ownerId": "owner-fixture"}
    for route in ["collaboration/get", "collaboration/invite", "collaboration/revoke", "collaboration/members", "collaboration/comment", "collaboration/review", "collaboration/update", "activity/list", "activity/export"]:
        helper = getattr(client, "vastu_properties_" + route.replace("/", "_"))
        annotations = get_type_hints(helper)
        assert annotations["params"].__name__.endswith("Request")
        assert annotations["return"].__name__.endswith("Response")
        helper(payload)
        call = client._request.call_args
        assert call.args[:2] == ("POST", "/v2/astrology/vastu/properties/" + route)
        assert call.kwargs["data"] == payload


def test_invite_pending_contract_and_consent_payload():
    client = VedikaClient(api_key="vk_test_x")
    pending = {"success": True, "data": {"invitationId": "00000000-0000-4000-8000-000000000001", "status": "pending"}, "billing": {"chargedCents": 0}}
    client._request = MagicMock(return_value=pending)
    body = {"propertyId": "property-fixture", "email": "synthetic@example.invalid", "role": "viewer"}
    assert client.vastu_properties_collaboration_invite(body) == pending
    client.vastu_properties_collaboration_invite({**body, "ownerId": "synthetic-owner", "accept": True})
    assert client._request.call_args.kwargs["data"]["accept"] is True
    client.vastu_properties_collaboration_revoke({"propertyId": "property-fixture", "invitationId": pending["data"]["invitationId"]})
    assert client._request.call_args.kwargs["data"]["invitationId"] == pending["data"]["invitationId"]
