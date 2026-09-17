"""Retry + idempotency tests.

urllib3's Retry() defaults `allowed_methods` to the idempotent-by-definition
set (GET/HEAD/PUT/DELETE/OPTIONS/TRACE), which EXCLUDES POST — paid
Vastu POST operations ignored `max_retries` regardless of
what the caller passed. Enabling POST retry is only safe because `_request`
now attaches a client `Idempotency-Key` header per logical call, which the
server dedupes a retried charge on. These tests assert both halves: POST is
now actually retried, AND the key stays identical across every attempt of one
call (the property that prevents a double charge).
"""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from vedika.client import VedikaClient


def _serve(handler_cls):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_post_is_retried_on_503_with_a_stable_idempotency_key():
    seen_keys = []
    attempts = {"n": 0}

    class FlakyThenOK(BaseHTTPRequestHandler):
        def do_POST(self):
            attempts["n"] += 1
            seen_keys.append(self.headers.get("Idempotency-Key"))
            content_length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(content_length)
            if attempts["n"] < 3:
                self.send_response(503)
                self.end_headers()
                return
            payload = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = _serve(FlakyThenOK)
    port = server.server_address[1]
    try:
        client = VedikaClient(
            api_key="vk_test_x",
            base_url=f"http://127.0.0.1:{port}",
            max_retries=3,
        )
        result = client.vastu("score/overall", {"zone": "north"})
    finally:
        server.shutdown()

    assert attempts["n"] == 3, "POST must be retried (urllib3 default excludes POST)"
    assert result == {"ok": True}
    assert len(set(seen_keys)) == 1, (
        f"Idempotency-Key must be IDENTICAL across every retry of one call, got {seen_keys}"
    )
    assert seen_keys[0], "Idempotency-Key must actually be set"


def test_paid_get_retries_share_a_key_and_separate_calls_get_new_keys():
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.headers.get("Idempotency-Key"))
            if len(seen) == 1:
                self.send_response(503)
                self.end_headers()
                return
            payload = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = _serve(Handler)
    port = server.server_address[1]
    try:
        client = VedikaClient(api_key="vk_test_x", base_url=f"http://127.0.0.1:{port}")
        client.vastu_reference("reference/directions/8")
        client.vastu_reference("reference/directions/8")
    finally:
        server.shutdown()

    assert len(seen) == 3
    assert seen[0], "Paid GETs need a client key even though they do not mutate the reading"
    assert seen[0] == seen[1], "The retry must reuse the charged request's identity"
    assert seen[2] and seen[2] != seen[0], "Separate calls must not reuse a charge"


def test_paid_get_inventory_and_caller_headers():
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append({name.lower(): value for name, value in self.headers.items()
                         if name.lower() in ("idempotency-key", "x-idempotency-key", "x-request-id")})
            payload = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = _serve(Handler)
    try:
        client = VedikaClient(api_key="vk_test_x", base_url=f"http://127.0.0.1:{server.server_address[1]}")
        operations = [op for op, contract in client.VASTU_OPERATION_CONTRACTS.items()
                      if contract["method"] in ("GET", "GET_OR_POST")]
        assert len(operations) == 12
        for prefix in ("/v2/vastu/", "/v2/astrology/vastu/"):
            for operation in operations:
                client._request("GET", prefix + operation, params={"lat": 18.5, "lon": 73.8})
        keys = [headers.get("idempotency-key") for headers in seen]
        assert all(keys)
        assert len(set(keys)) == len(keys)

        for header in ("Idempotency-Key", "x-IDEMPOTENCY-key", "X-Request-ID"):
            client.session.headers[header] = "caller-get-key"
            client.vastu_reference("reference/directions/8")
            assert seen[-1] == {header.lower(): "caller-get-key"}
            del client.session.headers[header]

        for path in ("/health", "/sandbox/vastu/reference/directions/8", "/v2/vastu/reference/unknown", "/v2/vastu/audit/floor-plan"):
            client._request("GET", path)
            assert seen[-1] == {}
    finally:
        server.shutdown()


def test_two_separate_calls_get_two_different_idempotency_keys():
    seen_keys = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen_keys.append(self.headers.get("Idempotency-Key"))
            content_length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(content_length)
            payload = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = _serve(Handler)
    port = server.server_address[1]
    try:
        client = VedikaClient(api_key="vk_test_x", base_url=f"http://127.0.0.1:{port}")
        client.vastu("score/overall", {"zone": "north"})
        client.vastu("score/overall", {"zone": "north"})
    finally:
        server.shutdown()

    assert len(seen_keys) == 2
    assert seen_keys[0] != seen_keys[1], "two distinct logical calls must NOT share a key"
