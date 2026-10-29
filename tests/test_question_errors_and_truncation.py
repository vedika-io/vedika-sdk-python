"""Typed refusals, retry rules and truncation fields on the AI question routes.

The API refuses some requests before billing and reports a cut-off answer in the
response metadata. These tests answer from a real HTTP server and pin three
things: the typed errors, the retry rules (a 400 is never resent, a monthly-spend
429 is never resent, a 503 is resent only with its idempotency key and never on
another tier), and the truncation fields that reach the caller.
"""

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import vedika
from vedika import (
    DailyLimitError,
    OutputBudgetExhaustedError,
    ProUltraUnavailableError,
    QuestionErrorCode,
    ServerError,
    VedikaAPIError,
    VedikaClient,
)
from vedika.models import QuestionResponse

BIRTH = {"datetime": "1990-06-15T14:30:00+05:30", "latitude": 28.6139, "longitude": 77.209, "timezone": "+05:30"}
IDEM = ("idempotency-key", "x-idempotency-key", "x-request-id")

PRO_ULTRA_DOWN = {"success": False, "error": "Vedika Pro Ultra is temporarily unavailable", "code": "PRO_ULTRA_UNAVAILABLE"}
BUDGET_EXHAUSTED = {
    "success": False,
    "error": "The output budget for this request was used up before an answer was written. "
             "You were not charged. Retry with a higher 'maxTokens', or set 'detail' to \"brief\".",
    "code": "OUTPUT_BUDGET_EXHAUSTED",
}
CUT_OFF = {
    "success": True,
    "response": "Your career is shaped by the tenth house, where",
    "answer": "Your career is shaped by the tenth house, where",
    "conversationId": "conv_1",
    "metadata": {
        "speed": "pro-ultra",
        "language": "en",
        "finishReason": "length",
        "truncated": True,
        "degraded": True,
        "degradedReason": "budget_truncated",
        "cost": {"total": "0"},
    },
}


@contextmanager
def serve(answer):
    """`answer(index, request)` returns (status, body[, headers]); a bytes body is sent as SSE."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
            seen.append({
                "path": self.path,
                "headers": {k.lower(): v for k, v in self.headers.items()},
                "body": json.loads(raw) if raw else {},
            })
            result = answer(len(seen) - 1, seen[-1])
            status, body = result[0], result[1]
            extra = result[2] if len(result) > 2 else {}
            if isinstance(body, bytes):
                payload, content_type = body, "text/event-stream"
            else:
                payload, content_type = json.dumps(body).encode(), "application/json"
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            for name, value in extra.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(payload)

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
        server.server_close()


def idem(request):
    return {name: value for name, value in request["headers"].items() if name in IDEM}


# ---- 503 PRO_ULTRA_UNAVAILABLE ---------------------------------------------

def test_pro_ultra_unavailable_is_typed_still_a_server_error_and_carries_code_and_retry_after(sleeps):
    with serve(lambda i, r: (503, PRO_ULTRA_DOWN, {"Retry-After": "5"})) as (seen, client):
        with pytest.raises(ProUltraUnavailableError) as raised:
            client(max_retries=0).ask_question("Career?", BIRTH, speed="pro-ultra")
    error = raised.value
    assert isinstance(error, ServerError) and isinstance(error, VedikaAPIError)
    assert error.status_code == 503
    assert error.code == QuestionErrorCode.PRO_ULTRA_UNAVAILABLE == "PRO_ULTRA_UNAVAILABLE"
    assert error.retry_after == 5.0
    assert error.message == "Vedika Pro Ultra is temporarily unavailable"
    assert str(error) == "[HTTP 503] Vedika Pro Ultra is temporarily unavailable"
    assert len(seen) == 1


def test_pro_ultra_unavailable_is_resent_only_under_the_same_key_and_always_on_pro_ultra(sleeps):
    with serve(lambda i, r: (503, PRO_ULTRA_DOWN, {"Retry-After": "5"})) as (seen, client):
        with pytest.raises(ProUltraUnavailableError):
            client(max_retries=3).ask_question("Career?", BIRTH, speed="pro-ultra", max_tokens=600)
    # One attempt and three retries, each waiting the API's Retry-After.
    assert len(seen) == 4 and sleeps == [5.0, 5.0, 5.0]
    keys = [idem(request) for request in seen]
    assert set(keys[0]) == {"x-idempotency-key", "idempotency-key"} and keys[0]["x-idempotency-key"]
    assert keys[0]["x-idempotency-key"] == keys[0]["idempotency-key"]
    assert all(key == keys[0] for key in keys)
    for request in seen:
        assert request["path"] == "/api/v1/astrology/query"
        assert request["body"]["speed"] == "pro-ultra" and request["body"]["maxTokens"] == 600


def test_a_stream_is_never_resent_and_fails_with_the_same_type_before_any_chunk(sleeps):
    with serve(lambda i, r: (503, PRO_ULTRA_DOWN, {"Retry-After": "5"})) as (seen, client):
        with pytest.raises(ProUltraUnavailableError) as raised:
            list(client(max_retries=3).ask_question_stream("Career?", BIRTH, speed="pro-ultra"))
    assert raised.value.code == "PRO_ULTRA_UNAVAILABLE" and raised.value.retry_after == 5.0
    assert len(seen) == 1 and sleeps == []
    assert seen[0]["path"] == "/api/v1/astrology/query/stream"


def test_a_503_without_that_code_stays_a_plain_api_error(sleeps):
    with serve(lambda i, r: (503, {"error": "down", "code": "SERVICE_UNAVAILABLE"})) as (seen, client):
        with pytest.raises(VedikaAPIError) as raised:
            client(max_retries=0).ask_question("Career?", BIRTH, speed="pro-ultra")
    assert not isinstance(raised.value, ProUltraUnavailableError)
    assert raised.value.status_code == 503 and raised.value.code == "SERVICE_UNAVAILABLE"


# ---- 400 OUTPUT_BUDGET_EXHAUSTED -------------------------------------------

def test_output_budget_exhausted_is_typed_with_the_api_message_and_never_resent(sleeps):
    with serve(lambda i, r: (400, BUDGET_EXHAUSTED)) as (seen, client):
        with pytest.raises(OutputBudgetExhaustedError) as raised:
            client(max_retries=3).ask_question("Career?", None, speed="pro-ultra", max_tokens=600)
    error = raised.value
    assert isinstance(error, VedikaAPIError) and not isinstance(error, ServerError)
    assert error.status_code == 400
    assert error.code == QuestionErrorCode.OUTPUT_BUDGET_EXHAUSTED == "OUTPUT_BUDGET_EXHAUSTED"
    assert error.message == BUDGET_EXHAUSTED["error"]
    # The client never raises max_tokens or changes detail for the caller.
    assert len(seen) == 1 and sleeps == []
    assert seen[0]["body"]["maxTokens"] == 600 and "detail" not in seen[0]["body"]


def test_a_400_on_a_stream_call_is_mapped_the_same_way_and_not_resent(sleeps):
    with serve(lambda i, r: (400, BUDGET_EXHAUSTED)) as (seen, client):
        with pytest.raises(OutputBudgetExhaustedError):
            list(client(max_retries=3).ask_question_stream("Career?", BIRTH, speed="pro-ultra", max_tokens=600))
    assert len(seen) == 1 and sleeps == []


# ---- every other 400 ---------------------------------------------------------

@pytest.mark.parametrize("code, controls", [
    ("CONTROL_UNSUPPORTED_FOR_TIER", {"speed": "pro-ultra", "seed": 7}),
    ("INVALID_DETAIL", {"detail": "verbose"}),
    ("INVALID_STOP", {"stop": []}),
    ("STOP_MATCHED_BEFORE_ANSWER", {"stop": ["Your"]}),
    ("DETAIL_BUDGET_CONFLICT", {"detail": "detailed", "max_tokens": 128}),
    ("VALIDATION_ERROR", {"speed": "fast", "version": "2"}),
])
def test_a_400_comes_back_once_as_an_api_error_with_its_code(code, controls, sleeps):
    body = {"success": False, "error": f"refused: {code}", "code": code}
    with serve(lambda i, r: (400, body)) as (seen, client):
        with pytest.raises(VedikaAPIError) as raised:
            client(max_retries=3).ask_question("Career?", BIRTH, **controls)
    error = raised.value
    assert not isinstance(error, OutputBudgetExhaustedError)
    assert error.status_code == 400 and error.code == code and error.message == f"refused: {code}"
    assert len(seen) == 1 and sleeps == []
    wire = {"max_tokens": "maxTokens"}
    for name, value in controls.items():
        assert seen[0]["body"][wire.get(name, name)] == value


def test_question_error_codes_name_every_code_the_controls_can_return():
    names = {name: getattr(QuestionErrorCode, name) for name in vars(QuestionErrorCode) if name.isupper()}
    assert names == {
        "CONTROL_UNSUPPORTED_FOR_TIER": "CONTROL_UNSUPPORTED_FOR_TIER",
        "INVALID_DETAIL": "INVALID_DETAIL",
        "INVALID_STOP": "INVALID_STOP",
        "STOP_MATCHED_BEFORE_ANSWER": "STOP_MATCHED_BEFORE_ANSWER",
        "DETAIL_BUDGET_CONFLICT": "DETAIL_BUDGET_CONFLICT",
        "OUTPUT_BUDGET_EXHAUSTED": "OUTPUT_BUDGET_EXHAUSTED",
        "PRO_ULTRA_UNAVAILABLE": "PRO_ULTRA_UNAVAILABLE",
        "ECO_UNAVAILABLE": "ECO_UNAVAILABLE",
        "VERSION_UNAVAILABLE": "VERSION_UNAVAILABLE",
    }
    for name in ("ProUltraUnavailableError", "OutputBudgetExhaustedError", "QuestionErrorCode", "ServerError"):
        assert name in vedika.__all__ and getattr(vedika, name) is not None


# ---- 429 MONTHLY_SPEND_LIMIT_REACHED -------------------------------------------

def test_monthly_spend_limit_is_raised_at_once_on_a_pro_ultra_question(sleeps):
    body = {"success": False, "error": "Monthly spend limit reached", "code": "MONTHLY_SPEND_LIMIT_REACHED", "retryAfter": 2}
    with serve(lambda i, r: (429, body, {"Retry-After": "2"})) as (seen, client):
        with pytest.raises(DailyLimitError) as raised:
            client(max_retries=3).ask_question("Career?", BIRTH, speed="pro-ultra")
    assert raised.value.code == "MONTHLY_SPEND_LIMIT_REACHED"
    assert len(seen) == 1 and sleeps == []


# ---- a cut-off answer ----------------------------------------------------------

def test_a_cut_off_answer_returns_normally_with_its_completion_fields(sleeps):
    with serve(lambda i, r: (200, CUT_OFF)) as (seen, client):
        answer = client().ask_question("Career?", BIRTH, speed="pro-ultra", max_tokens=300)
    assert isinstance(answer, QuestionResponse)
    assert answer.finish_reason == "length"
    assert answer.truncated is True
    assert answer.degraded is True
    assert answer.degraded_reason == "budget_truncated"
    assert answer.raw["metadata"]["cost"] == {"total": "0"}
    assert answer.answer == CUT_OFF["answer"] and answer.conversation_id == "conv_1"
    # One call: a truncated answer is not an error, and the client does not ask again.
    assert len(seen) == 1 and sleeps == []


def test_a_vastu_report_answer_carries_the_same_fields(sleeps):
    with serve(lambda i, r: (200, CUT_OFF)) as (seen, client):
        answer = client().ask_vastu_report("What first?", report={"method": "audit"}, speed="pro-ultra")
    assert (answer.finish_reason, answer.truncated, answer.degraded_reason) == ("length", True, "budget_truncated")


@pytest.mark.parametrize("reason, truncated", [
    ("complete", False), ("budgetExceeded", True), ("stopSequence", False), ("filtered", False), ("unknown", False),
])
def test_every_finish_reason_the_api_returns_is_passed_through(reason, truncated):
    data = {"success": True, "response": "ok", "metadata": {"finishReason": reason, "truncated": truncated}}
    answer = QuestionResponse.from_dict(data)
    assert answer.finish_reason == reason and answer.truncated is truncated
    assert answer.degraded is None and answer.degraded_reason is None


def test_a_normal_answer_has_no_completion_fields_and_odd_types_are_ignored():
    plain = QuestionResponse.from_dict({"success": True, "response": "ok", "metadata": {"model": "Vedika AI"}})
    assert (plain.finish_reason, plain.truncated, plain.degraded, plain.degraded_reason) == (None, None, None, None)
    bare = QuestionResponse.from_dict({"answer": "ok"})
    assert (bare.finish_reason, bare.truncated, bare.degraded, bare.degraded_reason) == (None, None, None, None)
    odd = QuestionResponse.from_dict({
        "response": "ok",
        "metadata": {"finishReason": 3, "truncated": "yes", "degraded": 1, "degradedReason": ["x"]},
    })
    assert (odd.finish_reason, odd.truncated, odd.degraded, odd.degraded_reason) == (None, None, None, None)
    assert QuestionResponse.from_dict({"response": "ok", "metadata": None}).truncated is None


def test_the_final_completed_frame_of_a_stream_carries_the_same_fields(sleeps):
    frame = json.dumps({"success": True, "response": CUT_OFF["response"], "metadata": CUT_OFF["metadata"]})
    sse = f'event: started\ndata: {{"stage":0}}\n\nevent: completed\ndata: {frame}\n\n'.encode()
    with serve(lambda i, r: (200, sse)) as (seen, client):
        frames = [json.loads(chunk) for chunk in client().ask_question_stream("Career?", BIRTH, speed="pro-ultra")]
    completed = frames[-1]
    assert completed["metadata"]["finishReason"] == "length"
    assert completed["metadata"]["truncated"] is True
    assert completed["metadata"]["degradedReason"] == "budget_truncated"
