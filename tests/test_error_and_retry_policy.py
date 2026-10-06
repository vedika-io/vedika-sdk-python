"""Typed errors and the retry policy, against the documented API behaviour.

402 is never retried and carries the wallet figures. A 429 is read by its body
`code`: RATE_LIMIT_EXCEEDED waits `retryAfter` (capped) and retries,
DAILY_LIMIT_EXCEEDED is never retried, and the `x-ratelimit-*` headers are never
consulted. 401 is never retried. A POST without an idempotency key is not
resent after a 5xx.
"""

import json
import re
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import pytest

import vedika
from vedika import (
    AuthenticationError,
    DailyLimitError,
    InsufficientCreditsError,
    RateLimitError,
    ValidationError,
    VedikaAPIError,
    VedikaClient,
)

BIRTH = {"datetime": "1990-06-15T14:30:00", "latitude": 28.6139, "longitude": 77.209, "timezone": "+05:30"}
OK = {"success": True, "data": {}}
IDEM = ("idempotency-key", "x-idempotency-key", "x-request-id")


@contextmanager
def serve(answer):
    """`answer(index, request)` returns (status, body) or (status, body, headers)."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def _handle(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
            request = {
                "method": self.command,
                "path": self.path,
                "headers": {k.lower(): v for k, v in self.headers.items()},
                "body": json.loads(raw) if raw[:1] in (b"{", b"[") else raw,
            }
            seen.append(request)
            result = answer(len(seen) - 1, request)
            status, body = result[0], result[1]
            extra = result[2] if len(result) > 2 else {}
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            for name, value in extra.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(payload)

        do_GET = do_POST = do_DELETE = _handle

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def client(**kwargs):
        return VedikaClient(api_key="vk_test_x", base_url=f"http://127.0.0.1:{server.server_address[1]}", **kwargs)

    try:
        yield seen, client
    finally:
        server.shutdown()


def idem_headers(request):
    return {name: value for name, value in request["headers"].items() if name in IDEM}


# ---- 402 ----------------------------------------------------------------

@pytest.mark.parametrize("code", ["INSUFFICIENT_BALANCE", "INSUFFICIENT_BALANCE_PRECHECK", "INSUFFICIENT_BALANCE_RESERVATION"])
def test_402_raises_typed_error_with_wallet_figures_and_is_never_retried(code, sleeps):
    body = {
        "success": False, "error": "Insufficient balance", "message": "Top up your wallet", "code": code,
        "wallet": {"required": 0.5, "available": 0.2, "deficit": 0.3},
        "purchaseUrl": "https://vedika.io/dashboard.html#wallet",
    }
    with serve(lambda i, r: (402, body)) as (seen, client):
        with pytest.raises(InsufficientCreditsError) as error:
            client(max_retries=3).get_kundli(BIRTH)
    assert len(seen) == 1 and sleeps == []
    exc = error.value
    assert exc.status_code == 402 and exc.code == code
    assert (exc.required, exc.available, exc.deficit) == (0.5, 0.2, 0.3)
    assert exc.purchase_url == "https://vedika.io/dashboard.html#wallet"


def test_402_without_wallet_block_leaves_figures_none():
    with serve(lambda i, r: (402, {"code": "INSUFFICIENT_BALANCE", "message": "no funds"})) as (seen, client):
        with pytest.raises(InsufficientCreditsError) as error:
            client().get_usage()
    assert error.value.required is None and error.value.deficit is None


# ---- 429 ----------------------------------------------------------------

def test_daily_limit_is_never_retried_and_ignores_headers(sleeps):
    body = {"success": False, "code": "DAILY_LIMIT_EXCEEDED", "message": "Daily limit", "retryAfter": 3600}
    headers = {"x-ratelimit-remaining": "59", "Retry-After": "1"}
    with serve(lambda i, r: (429, body, headers)) as (seen, client):
        with pytest.raises(DailyLimitError) as error:
            client(max_retries=3).get_usage()
    assert len(seen) == 1 and sleeps == []
    assert isinstance(error.value, RateLimitError)
    assert error.value.code == "DAILY_LIMIT_EXCEEDED" and error.value.retry_after == 3600


def test_rate_limit_waits_retry_after_and_retries(sleeps):
    limited = {"success": False, "code": "RATE_LIMIT_EXCEEDED", "retryAfter": 2}
    with serve(lambda i, r: (429, limited, {"x-ratelimit-remaining": "0"}) if i == 0 else (200, {"ok": True})) as (seen, client):
        assert client().get_usage() == {"ok": True}
    assert len(seen) == 2 and sleeps == [2.0]


def test_rate_limit_ignores_remaining_header_when_the_call_succeeds(sleeps):
    with serve(lambda i, r: (200, {"ok": True}, {"x-ratelimit-remaining": "0"})) as (seen, client):
        client().get_usage()
    assert len(seen) == 1 and sleeps == []


def test_rate_limit_asking_for_more_than_the_cap_raises_without_sleeping(sleeps):
    limited = {"success": False, "code": "RATE_LIMIT_EXCEEDED", "retryAfter": 3600}
    with serve(lambda i, r: (429, limited)) as (seen, client):
        with pytest.raises(RateLimitError) as error:
            client(max_retry_wait=30).get_usage()
    assert not isinstance(error.value, DailyLimitError)
    assert len(seen) == 1 and sleeps == [] and error.value.retry_after == 3600


def test_persistent_rate_limit_ends_in_a_typed_error_not_a_generic_one(sleeps):
    limited = {"success": False, "code": "RATE_LIMIT_EXCEEDED", "retryAfter": 1}
    with serve(lambda i, r: (429, limited)) as (seen, client):
        with pytest.raises(RateLimitError):
            client(max_retries=2).get_usage()
    assert len(seen) == 3 and sleeps == [1.0, 1.0]


def test_unknown_429_code_honours_retry_after_header_with_a_cap(sleeps):
    with serve(lambda i, r: (429, {"code": "SOMETHING_NEW"}, {"Retry-After": "5"}) if i == 0 else (200, {"ok": True})) as (seen, client):
        assert client().get_usage() == {"ok": True}
    assert sleeps == [5.0]


def test_rate_limit_retry_is_safe_for_an_unkeyed_post(sleeps):
    limited = {"success": False, "code": "RATE_LIMIT_EXCEEDED", "retryAfter": 1}
    with serve(lambda i, r: (429, limited) if i == 0 else (200, OK)) as (seen, client):
        client().get_kundli(BIRTH)
    assert len(seen) == 2 and all(idem_headers(r) == {} for r in seen)


# ---- 401, 5xx ------------------------------------------------------------

def test_401_is_never_retried(sleeps):
    with serve(lambda i, r: (401, {"error": "bad key"})) as (seen, client):
        with pytest.raises(AuthenticationError):
            client(max_retries=3).get_usage()
    assert len(seen) == 1 and sleeps == []


def test_unkeyed_post_is_not_resent_after_a_503(sleeps):
    with serve(lambda i, r: (503, {"error": "down"})) as (seen, client):
        with pytest.raises(VedikaAPIError) as error:
            client(max_retries=3).get_kundli(BIRTH)
    assert len(seen) == 1 and sleeps == [] and error.value.status_code == 503
    assert idem_headers(seen[0]) == {}


def test_get_is_resent_after_a_503_with_backoff(sleeps):
    with serve(lambda i, r: (503, {"error": "down"}) if i < 2 else (200, {"ok": True})) as (seen, client):
        assert client(max_retries=3).get_usage() == {"ok": True}
    assert len(seen) == 3 and sleeps == [0.5, 1.0]


def test_retry_after_on_a_503_is_capped(sleeps):
    with serve(lambda i, r: (503, {}, {"Retry-After": "9999"}) if i == 0 else (200, {"ok": True})) as (seen, client):
        client(max_retry_wait=7).get_usage()
    assert sleeps == [7.0]


# ---- idempotency -----------------------------------------------------------

def test_ask_question_sends_x_idempotency_key_only_and_reuses_it_on_retry(sleeps):
    with serve(lambda i, r: (503, {}) if i == 0 else (200, {"success": True, "answer": "ok"})) as (seen, client):
        client().ask_question("Career?", BIRTH)
    assert len(seen) == 2
    keys = [idem_headers(r) for r in seen]
    assert set(keys[0]) == {"x-idempotency-key"} and keys[0] == keys[1] and keys[0]["x-idempotency-key"]


def test_uncertified_calls_send_no_idempotency_or_request_id_header():
    with serve(lambda i, r: (200, OK)) as (seen, client):
        c = client()
        c.get_kundli(BIRTH)
        c.get_birth_chart("1990-06-15T14:30:00", 28.6, 77.2)
        c.vastu_score("overall", {})
        c.get_panchang(date="2026-10-06")
    assert len(seen) == 4
    assert all(idem_headers(r) == {} for r in seen), [idem_headers(r) for r in seen]


def test_caller_key_on_an_unsupported_operation_is_resent_once_without_it(sleeps):
    refusal = {"success": False, "code": "IDEMPOTENCY_NOT_SUPPORTED",
               "message": "Remove the idempotency header and retry; no charge was attempted."}
    with serve(lambda i, r: (422, refusal) if i == 0 else (200, {"ok": True})) as (seen, client):
        result = client().vastu_score("overall", {}, idempotency_key="mine-1")
    assert result == {"ok": True}
    assert len(seen) == 2
    assert idem_headers(seen[0]) == {"idempotency-key": "mine-1"}
    assert idem_headers(seen[1]) == {}


def test_a_second_idempotency_422_is_raised_not_looped():
    refusal = {"success": False, "code": "IDEMPOTENCY_NOT_SUPPORTED", "message": "no"}
    with serve(lambda i, r: (422, refusal)) as (seen, client):
        with pytest.raises(ValidationError) as error:
            client().vastu_score("overall", {}, idempotency_key="mine-1")
    assert len(seen) == 2 and error.value.code == "IDEMPOTENCY_NOT_SUPPORTED"


def test_other_idempotency_codes_are_not_swallowed():
    with serve(lambda i, r: (409, {"code": "IDEMPOTENCY_KEY_CONFLICT", "message": "reused"})) as (seen, client):
        with pytest.raises(VedikaAPIError) as error:
            client().vastu("properties/list", {}, idempotency_key="k")
    assert len(seen) == 1 and error.value.code == "IDEMPOTENCY_KEY_CONFLICT"


def test_certified_header_table():
    from vedika._idempotency import certified_header

    assert certified_header("POST", "/api/v1/astrology/query") == "X-Idempotency-Key"
    assert certified_header("POST", "/v2/vastu/jobs") == "Idempotency-Key"
    assert certified_header("POST", "/v2/astrology/vastu/properties/create") == "Idempotency-Key"
    assert certified_header("GET", "/v2/lifestyle/zodiac-food/aries") == "Idempotency-Key"
    assert certified_header("POST", "/v2/astrology/kundli") is None
    assert certified_header("POST", "/v2/vastu/score/overall") is None
    assert certified_header("GET", "/v2/vastu/jobs") is None


# ---- auth and shared paths ---------------------------------------------------

def test_credentials_are_sent_once_as_bearer():
    with serve(lambda i, r: (200, {"ok": True})) as (seen, client):
        client().get_usage()
    headers = seen[0]["headers"]
    assert headers["authorization"] == "Bearer vk_test_x"
    assert "x-api-key" not in headers
    assert headers["user-agent"] == f"vedika-python-sdk/{vedika.__version__}"


def test_default_base_url_is_the_production_origin():
    assert VedikaClient(api_key="vk_test_x").base_url == "https://api.vedika.io"


def test_voice_sends_no_idempotency_key_and_maps_402():
    client = VedikaClient(api_key="vk_test_x")
    seen = {}

    class Response:
        status_code = 402
        headers = {}
        content = b"{}"

        def json(self):
            return {"code": "INSUFFICIENT_BALANCE", "wallet": {"required": 1, "available": 0, "deficit": 1}}

    def post(url, **kwargs):
        seen.update(kwargs)
        return Response()

    with patch.object(client.session, "post", side_effect=post):
        with pytest.raises(InsufficientCreditsError) as error:
            client.ask_voice(b"RIFF....WAVE", birth_details=BIRTH)
    assert not {name.lower() for name in seen["headers"]} & set(IDEM)
    assert error.value.deficit == 1


def test_stream_errors_are_typed():
    with serve(lambda i, r: (429, {"code": "DAILY_LIMIT_EXCEEDED", "message": "used up"})) as (seen, client):
        with pytest.raises(DailyLimitError):
            list(client().ask_question_stream("Career?", BIRTH))
    assert len(seen) == 1


# ---- escape hatch ----------------------------------------------------------------

def test_request_escape_hatch_sends_with_client_auth_and_returns_json():
    with serve(lambda i, r: (200, {"success": True, "data": {"n": 1}})) as (seen, client):
        result = client().request("POST", "/v2/astrology/kundli", json=BIRTH)
        client().request("GET", "/api/v1/usage/wallet-balance", params={"x": "1"})
    assert result["data"] == {"n": 1}
    assert seen[0]["path"] == "/v2/astrology/kundli" and seen[0]["body"] == BIRTH
    assert seen[0]["headers"]["authorization"] == "Bearer vk_test_x"
    assert seen[1]["path"] == "/api/v1/usage/wallet-balance?x=1"


@pytest.mark.parametrize("path", [
    "https://evil.example/steal", "//evil.example/x", "v2/astrology/kundli", "/ok@evil.example://x", "/a\\b", "",
])
def test_request_escape_hatch_refuses_anything_but_a_path_on_the_origin(path):
    client = VedikaClient(api_key="vk_test_x")
    with patch.object(client.session, "request") as transport:
        with pytest.raises(ValueError):
            client.request("GET", path)
        transport.assert_not_called()


# ---- divisional charts -----------------------------------------------------------

@pytest.mark.parametrize("chart,path,division", [
    ("navamsa", "/v2/astrology/navamsa", None),
    ("hora", "/v2/astrology/divisional-chart", 2),
    ("D2", "/v2/astrology/divisional-chart", 2),
    ("D9", "/v2/astrology/divisional-chart", 9),
    (60, "/v2/astrology/divisional-chart", 60),
    ("12", "/v2/astrology/divisional-chart", 12),
])
def test_divisional_chart_uses_a_path_the_api_serves(chart, path, division):
    with serve(lambda i, r: (200, OK)) as (seen, client):
        client().get_divisional_chart(chart, BIRTH)
    assert seen[0]["path"] == path
    assert seen[0]["body"].get("division") == division
    assert seen[0]["path"] != "/v2/astrology/hora-chart"


def test_divisional_chart_rejects_an_unknown_name():
    with pytest.raises(ValueError):
        VedikaClient(api_key="vk_test_x").get_divisional_chart("nonsense", BIRTH)


# ---- version consistency -----------------------------------------------------------

def test_version_is_the_same_everywhere():
    root = Path(__file__).resolve().parent.parent
    setup_version = re.search(r'version="([^"]+)"', (root / "setup.py").read_text(encoding="utf-8")).group(1)
    changelog_version = re.search(r"^## \[([^\]]+)\]", (root / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
    assert setup_version == vedika.__version__ == changelog_version
    client = VedikaClient(api_key="vk_test_x")
    assert client.session.headers["User-Agent"] == f"vedika-python-sdk/{setup_version}"
