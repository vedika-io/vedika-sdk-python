"""The AI question routes take a delivery tier (`speed`) and answer-length controls.

The API validates `version`, `detail`, `maxTokens`, `stop` and `seed` against
the tier and refuses an unsupported control before billing, so the client only
has to put each one on the wire under the right name. These tests read the
bodies a real HTTP server receives.
"""

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from vedika.client import VedikaClient

BIRTH = {"datetime": "1990-06-15T14:30:00+05:30", "latitude": 28.6139, "longitude": 77.209, "timezone": "+05:30"}
ANSWER = {"success": True, "response": "ok", "conversationId": "conv_1"}


@contextmanager
def api(stream=False):
    """A local API that records every request body and answers JSON, or SSE when `stream` is set."""
    requests_seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            requests_seen.append((self.path, json.loads(self.rfile.read(length))))
            if stream:
                payload = b'event: completed\ndata: {"success":true}\n\n'
                content_type = "text/event-stream"
            else:
                payload = json.dumps(ANSWER).encode()
                content_type = "application/json"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        client = VedikaClient(api_key="vk_test_x", base_url=f"http://127.0.0.1:{server.server_address[1]}")
        yield client, requests_seen
    finally:
        server.shutdown()
        server.server_close()


def test_ask_question_pro_ultra_with_controls():
    with api() as (client, seen):
        client.ask_question(
            "What are my career prospects?",
            BIRTH,
            speed="pro-ultra",
            detail="brief",
            max_tokens=600,
            stop=["END", "STOP"],
        )
    assert seen == [(
        "/api/v1/astrology/query",
        {
            "question": "What are my career prospects?",
            "birthDetails": BIRTH,
            "language": "en",
            "speed": "pro-ultra",
            "detail": "brief",
            "maxTokens": 600,
            "stop": ["END", "STOP"],
        },
    )]


def test_ask_question_standard_version_seed_and_single_stop():
    with api() as (client, seen):
        client.ask_question("q", BIRTH, speed="standard", version="2", seed=0, stop="END", detail="detailed")
        client.ask_question("q", BIRTH, version="2.5", seed=42, stop=("A", "B"))
    assert seen[0][1] == {
        "question": "q", "birthDetails": BIRTH, "language": "en",
        "speed": "standard", "version": "2", "detail": "detailed", "stop": "END", "seed": 0,
    }
    assert seen[1][1] == {
        "question": "q", "birthDetails": BIRTH, "language": "en", "version": "2.5", "seed": 42, "stop": ["A", "B"],
    }


@pytest.mark.parametrize("speed", ["standard", "fast", "eco", "pro-ultra"])
def test_every_published_tier_reaches_the_wire_unchanged(speed):
    with api() as (client, seen):
        client.ask_question("q", BIRTH, speed=speed)
    assert seen[0][1]["speed"] == speed


def test_no_controls_sends_none_of_them():
    with api() as (client, seen):
        client.ask_question("q", BIRTH)
        client.ask_question("q", BIRTH, speed=None, version=None, detail=None, max_tokens=None, stop=None, seed=None)
    for _, body in seen:
        assert body == {"question": "q", "birthDetails": BIRTH, "language": "en"}


def test_other_options_keep_going_out_beside_the_controls():
    with api() as (client, seen):
        client.ask_question(
            "q", BIRTH, system="kp", conversation_id="conv_1", include_remedies=False, category="career",
            response_format="json", speed="pro-ultra", max_tokens=800,
        )
    assert seen[0][1] == {
        "question": "q", "birthDetails": BIRTH, "language": "en", "system": "kp", "conversationId": "conv_1",
        "includeRemedies": False, "category": "career", "responseFormat": "json",
        "speed": "pro-ultra", "maxTokens": 800,
    }


def test_controls_are_keyword_only():
    with api() as (client, _):
        with pytest.raises(TypeError):
            client.ask_question("q", BIRTH, "en", "kp", "pro-ultra")  # type: ignore[misc]


def test_ask_vastu_report_sends_the_same_controls():
    report = {"method": "audit", "defects": []}
    with api() as (client, seen):
        client.ask_vastu_report("What first?", report, speed="pro-ultra", detail="brief", max_tokens=500, stop="END")
        client.ask_vastu_report("And then?", conversation_id="conv_1", speed="standard", version="2.5", seed=7)
        client.ask_vastu_report("Plain", report)
    assert seen[0][1] == {
        "question": "What first?", "language": "en", "vastuContext": {"report": report},
        "speed": "pro-ultra", "detail": "brief", "maxTokens": 500, "stop": "END",
    }
    assert seen[1][1] == {
        "question": "And then?", "language": "en", "conversationId": "conv_1",
        "speed": "standard", "version": "2.5", "seed": 7,
    }
    assert seen[2][1] == {"question": "Plain", "language": "en", "vastuContext": {"report": report}}


def test_ask_question_stream_sends_the_same_controls():
    with api(stream=True) as (client, seen):
        chunks = list(client.ask_question_stream(
            "q", BIRTH, speed="pro-ultra", detail="detailed", max_tokens=1200, stop=["END"],
        ))
        plain = list(client.ask_question_stream("q", BIRTH))
    assert chunks == ['{"success":true}'] and plain == ['{"success":true}']
    assert seen[0] == (
        "/api/v1/astrology/query/stream",
        {
            "question": "q", "birthDetails": BIRTH, "language": "en",
            "speed": "pro-ultra", "detail": "detailed", "maxTokens": 1200, "stop": ["END"],
        },
    )
    assert seen[1][1] == {"question": "q", "birthDetails": BIRTH, "language": "en"}
