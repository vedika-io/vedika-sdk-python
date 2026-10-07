"""Retry + idempotency tests.

The client attaches an idempotency key on its own only for the operations the
live API lists as accepting one (`vedika/_idempotency.py`). Every other operation
answers 422 IDEMPOTENCY_NOT_SUPPORTED to a key, so none is generated there, and a
POST without a key is never resent after a 5xx (the first attempt may already
have been charged). These tests pin both halves: certified calls are retried
under one stable key, uncertified ones carry no key and are not resent.
"""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from vedika.client import VastuOperation, VedikaClient


def _serve(handler_cls):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_certified_post_is_retried_on_503_with_a_stable_idempotency_key():
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
        result = client.vastu("properties/list", {"limit": 5})
    finally:
        server.shutdown()

    assert attempts["n"] == 3, "a keyed POST must be retried on 503"
    assert result == {"ok": True}
    assert len(set(seen_keys)) == 1, (
        f"Idempotency-Key must be IDENTICAL across every retry of one call, got {seen_keys}"
    )
    assert seen_keys[0], "Idempotency-Key must actually be set"


def test_billed_vastu_get_sends_no_key_and_is_retried_on_503():
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append({k.lower(): v for k, v in self.headers.items()})
            if len(seen) == 1:
                self.send_response(503)
                self.send_header("Content-Length", "0")
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
        assert client.vastu_reference("reference/directions/8") == {"ok": True}
    finally:
        server.shutdown()

    assert len(seen) == 2, "a GET is safe to resend"
    for headers in seen:
        assert not {"idempotency-key", "x-idempotency-key", "x-request-id"} & set(headers), headers


def test_billed_vastu_get_inventory_sends_no_generated_key_but_keeps_caller_headers():
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
                      # Rule versions and job status/results are free reads, not billed GETs.
                      if op != "rules/versions" and not op.startswith("jobs/") and contract["method"] in ("GET", "GET_OR_POST")]
        assert len(operations) == 12
        for prefix in ("/v2/vastu/", "/v2/astrology/vastu/"):
            for operation in operations:
                client._request("GET", prefix + operation, params={"lat": 18.5, "lon": 73.8})
        # The live API answers 422 IDEMPOTENCY_NOT_SUPPORTED to a key on these
        # reads, so none is generated.
        assert len(seen) == 24
        assert all(headers == {} for headers in seen)

        for header in ("Idempotency-Key", "x-IDEMPOTENCY-key", "X-Request-ID"):
            client.session.headers[header] = "caller-get-key"
            client.vastu_reference("reference/directions/8")
            assert seen[-1] == {header.lower(): "caller-get-key"}
            del client.session.headers[header]

        free_reads = [prefix + operation for prefix in ("/v2/vastu/", "/v2/astrology/vastu/")
                      for operation in ("rules/versions", "jobs/vjob_123", "jobs/vjob_123/results")]
        for path in ["/health", "/sandbox/vastu/reference/directions/8", "/v2/vastu/reference/unknown", "/v2/vastu/audit/floor-plan", *free_reads]:
            client._request("GET", path)
            assert seen[-1] == {}
    finally:
        server.shutdown()


def test_two_separate_certified_calls_get_two_different_idempotency_keys():
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
        client.vastu("properties/list", {"limit": 5})
        client.vastu("properties/list", {"limit": 5})
    finally:
        server.shutdown()

    assert len(seen_keys) == 2
    assert seen_keys[0] != seen_keys[1], "two distinct logical calls must NOT share a key"


def test_scan_operations_send_no_retry_header_and_still_retry():
    """Scan save/retrieve/list/delete/timelapse identify a retry by scanId or
    the body's requestId; the server answers 422 to any retry header."""
    seen = []
    attempts = {"n": 0}

    class FlakyThenOK(BaseHTTPRequestHandler):
        def do_POST(self):
            attempts["n"] += 1
            seen.append({k.lower(): v for k, v in self.headers.items()})
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if attempts["n"] < 2:
                self.send_response(503)
                self.end_headers()
                return
            payload = b'{"success": true, "data": {"scans": [], "nextCursor": null}}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = _serve(FlakyThenOK)
    try:
        client = VedikaClient(api_key="vk_test_x", base_url=f"http://127.0.0.1:{server.server_address[1]}", max_retries=3)
        client.session.headers["X-Request-Id"] = "session-level-id"
        client.vastu_operation(VastuOperation.SCANS_LIST, {"requestId": "request-00000001", "limit": 1})
    finally:
        server.shutdown()

    assert attempts["n"] == 2, "a scan read is still retried: its identity is in the body"
    for headers in seen:
        assert not {"idempotency-key", "x-idempotency-key", "x-request-id"} & set(headers), headers


def test_scan_operations_refuse_a_caller_idempotency_key():
    import pytest

    client = VedikaClient(api_key="vk_test_x", base_url="http://127.0.0.1:9")
    with pytest.raises(ValueError, match="requestId"):
        client.vastu_operation(VastuOperation.SCANS_LIST, {"requestId": "request-00000001", "limit": 1}, idempotency_key="k")
