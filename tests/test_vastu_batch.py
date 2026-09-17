import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import pytest
from vedika.client import VedikaClient, VastuOperation

PAYLOAD = {"items": [{"id": "property-1", "assessment": {"inputSource": "plan-derived", "rooms": [{"roomType": "kitchen", "zone": "SE"}]}}]}
RESPONSE = {"success": True, "data": {"results": [{"id": "property-1", "status": 200, "response": {"success": True, "data": {"status": "assessed", "score": 100}}}], "summary": {"total": 1, "succeeded": 1, "failed": 0}, "billingBasis": "existing assessment price per item", "execution": "synchronous"}}


def test_batch_inventory_has_exact_request_and_response_contracts():
    assert VastuOperation.ASSESSMENTS_BATCH.value == "assessments/batch"
    contract = VedikaClient.VASTU_OPERATION_CONTRACTS["assessments/batch"]
    assert contract["method"] == "POST"
    assert contract["requestSchema"] == "VastuAssessmentsBatchRequest"
    assert contract["responseSchema"] == "VastuAssessmentsBatchResponse"


@pytest.mark.parametrize("key", [None, "", "   "])
def test_batch_requires_caller_identity_before_transport(key):
    client = VedikaClient(api_key="vk_test")
    with patch.object(client.session, "request") as transport:
        with pytest.raises(ValueError, match="Idempotency-Key"):
            client.vastu("assessments/batch", PAYLOAD, idempotency_key=key)
        with pytest.raises(ValueError, match="Idempotency-Key"):
            client.vastu_operation(VastuOperation.ASSESSMENTS_BATCH, PAYLOAD, idempotency_key=key)
        transport.assert_not_called()


def test_batch_wire_body_and_saved_key_survive_retry_and_client_recreation():
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            seen.append((self.path, body, self.headers.get("Idempotency-Key")))
            response = json.dumps({"error": "retry"} if len(seen) == 1 else RESPONSE).encode()
            self.send_response(503 if len(seen) == 1 else 200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for _ in range(2):
            client = VedikaClient(api_key="vk_test", base_url=f"http://127.0.0.1:{server.server_address[1]}", max_retries=1)
            result = client.vastu_operation(VastuOperation.ASSESSMENTS_BATCH, PAYLOAD, idempotency_key="saved-batch-42")
            assert result == RESPONSE
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    assert seen == [("/v2/astrology/vastu/assessments/batch", PAYLOAD, "saved-batch-42")] * 3


def test_report_and_drawing_request_options_match_public_contract():
    from typing import get_args, get_type_hints
    from vedika.client import VastuPlanGenerateRequest, VastuPlanFromRequirementsRequest, VastuPlanOptimizeRequest, VastuPlanReportRequest
    for cls in (VastuPlanGenerateRequest, VastuPlanFromRequirementsRequest, VastuPlanOptimizeRequest):
        assert get_type_hints(cls)["includeSvg"] is bool
        assert "includeSvg" not in cls.__required_keys__
    hints = get_type_hints(VastuPlanReportRequest)
    assert get_args(hints["format"]) == ("json", "html")
    assert {"brand", "reportTitle", "generatedFor", "tenantName"} <= hints.keys()
    assert VastuPlanReportRequest.__required_keys__ == frozenset({"rooms"})
