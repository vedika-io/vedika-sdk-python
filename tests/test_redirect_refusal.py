"""Every 3xx is refused: no second request, so no private body or Idempotency-Key egress."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from vedika.client import VedikaClient, VastuOperation
from vedika.exceptions import VedikaAPIError


def _serve(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class _Pair:
    """An approved origin answering every request with a redirect, and the origin it points at."""

    def __init__(self, status, location_for):
        self.first, self.second = [], []
        outer = self

        class Target(BaseHTTPRequestHandler):
            def _record(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
                outer.second.append({"method": self.command, "path": self.path, "headers": dict(self.headers), "body": raw})
                payload = b'{"success": true, "data": {"fromTarget": true}}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = _record

            def log_message(self, *args):
                pass

        self.target = _serve(Target)

        class Origin(BaseHTTPRequestHandler):
            def _redirect(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
                outer.first.append({"method": self.command, "path": self.path, "body": raw})
                self.send_response(status)
                self.send_header("Location", location_for(outer.target.server_address[1]))
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = _redirect

            def log_message(self, *args):
                pass

        self.origin = _serve(Origin)

    def client(self, **kwargs):
        return VedikaClient(api_key="vk_test_secret", base_url=f"http://127.0.0.1:{self.origin.server_address[1]}", **kwargs)

    def close(self):
        for server in (self.target, self.origin):
            server.shutdown()
            server.server_close()


def cross_origin(port):
    return f"http://127.0.0.1:{port}/collect"


def same_origin(_port):
    return "/v2/astrology/vastu/score/overall"


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_a_private_post_answered_with_a_redirect_never_reaches_the_target(status):
    pair = _Pair(status, cross_origin)
    try:
        room = {"rooms": [{"roomType": "kitchen", "zone": "SE", "polygon": [[0, 0], [3, 0], [3, 4]]}]}
        with pytest.raises(VedikaAPIError, match="(?i)redirect"):
            pair.client(max_retries=2).vastu_operation(VastuOperation.SCORE_OVERALL, room, idempotency_key="private-key-1")
    finally:
        pair.close()
    assert pair.second == []
    # Refused, not retried: the approved origin saw the request exactly once.
    assert len(pair.first) == 1


def test_a_get_answered_with_a_redirect_never_reaches_the_target():
    pair = _Pair(302, cross_origin)
    try:
        with pytest.raises(VedikaAPIError, match="(?i)redirect"):
            pair.client().vastu_reference("reference/directions/8")
    finally:
        pair.close()
    assert pair.second == []
    assert len(pair.first) == 1


def test_a_same_origin_redirect_is_refused_too():
    pair = _Pair(307, same_origin)
    try:
        with pytest.raises(VedikaAPIError, match="(?i)redirect"):
            pair.client().vastu("score/overall", {"zone": "north"})
    finally:
        pair.close()
    assert len(pair.first) == 1
    assert pair.second == []


def test_the_streaming_path_refuses_a_redirect():
    pair = _Pair(307, cross_origin)
    try:
        with pytest.raises(VedikaAPIError, match="(?i)redirect"):
            list(pair.client().ask_question_stream("q", {"datetime": "2000-01-01T00:00:00Z"}))
    finally:
        pair.close()
    assert pair.second == []


def test_the_voice_path_refuses_a_redirect():
    pair = _Pair(307, cross_origin)
    try:
        with pytest.raises(VedikaAPIError, match="(?i)redirect"):
            pair.client().ask_voice(b"RIFF....WAVE")
    finally:
        pair.close()
    assert pair.second == []
