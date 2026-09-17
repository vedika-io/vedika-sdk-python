"""`ask_vastu_report` sends the report as `vastuContext` on the AI query route."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from vedika.client import VedikaClient


def test_sends_the_report_and_reuses_it_by_conversation():
    bodies = []
    answer = {
        "success": True,
        "response": "Fix the toilet first [D1].",
        "conversationId": "conv_1",
        "vastuContext": {"itemIds": ["D1"], "citedItems": ["D1"], "verified": False},
    }

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            bodies.append((self.path, json.loads(self.rfile.read(length))))
            payload = json.dumps(answer).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    report = {"method": "audit", "defects": [{"room": "toilet", "zone": "NE"}]}
    try:
        client = VedikaClient(api_key="vk_test_x", base_url=f"http://127.0.0.1:{server.server_address[1]}")
        first = client.ask_vastu_report("What first?", report)
        client.ask_vastu_report("And then?", conversation_id="conv_1", speed="fast")
        with pytest.raises(ValueError):
            client.ask_vastu_report("No context")
    finally:
        server.shutdown()

    assert first.answer == "Fix the toilet first [D1]."
    assert first.conversation_id == "conv_1"
    assert first.vastu_context["citedItems"] == ["D1"]
    assert bodies[0] == ("/api/v1/astrology/query",
                         {"question": "What first?", "language": "en", "vastuContext": {"report": report}})
    assert bodies[1][1] == {"question": "And then?", "language": "en", "conversationId": "conv_1", "speed": "fast"}
    assert len(bodies) == 2
