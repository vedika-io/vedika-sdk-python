"""Async jobs, multipart report upload, reportRef and retained keys on the named helpers."""

import json
import re
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from vedika.client import VedikaClient, VastuOperation

JOB = "vjob_0123456789abcdef0123456789abcdef"
UPLOAD = "vup_0123456789abcdef0123456789abcdef"
JOB_BODY = {
    "operation": "assessments",
    "items": [{"id": "p1", "input": {"inputSource": "plan-derived", "rooms": [{"roomType": "kitchen", "zone": "SE"}]}}],
}
STATUS = {
    "jobId": JOB, "status": "running", "operation": "assessments", "itemCount": 1,
    "counts": {"succeeded": 0, "failed": 0, "pending": 1, "cancelled": 0},
    "billing": {"currency": "USD", "pricePerItem": 0.1, "maxCharge": 0.1, "charged": 0, "basis": "per item"},
    "cancelRequested": False, "createdAt": 1, "updatedAt": 1, "expiresAt": 9,
    "resultsUrl": f"https://api.vedika.io/v2/vastu/jobs/{JOB}/results",
}


@contextmanager
def serve(answer):
    """Local server recording every request; `answer(method, path, index)` returns (status, body)."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def _handle(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
            seen.append({"method": self.command, "path": self.path, "headers": dict(self.headers), "raw": raw})
            status, body = answer(self.command, self.path, len(seen) - 1)
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_GET = do_POST = _handle

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def client(**kwargs):
        return VedikaClient(api_key="vk_test", base_url=f"http://127.0.0.1:{server.server_address[1]}", **kwargs)

    try:
        yield seen, client
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def header(request, name):
    return next((v for k, v in request["headers"].items() if k.lower() == name.lower()), None)


def test_inventory_has_all_147_paths_with_right_verbs():
    assert len(VedikaClient.VASTU_OPERATIONS) == 147
    assert len(set(VedikaClient.VASTU_OPERATIONS)) == 147
    contracts = VedikaClient.VASTU_OPERATION_CONTRACTS
    assert len(contracts) == 147
    assert [contracts[k]["method"] for k in ("jobs", "jobs/{id}", "jobs/{id}/results", "jobs/{id}/cancel")] == [
        "POST", "GET", "GET", "POST"]
    assert VastuOperation.JOBS.value == "jobs"


def test_generic_escape_hatch_sends_get_for_status_and_results_and_post_for_cancel():
    client = VedikaClient(api_key="vk_test")
    with patch.object(client, "_request", return_value={}) as request:
        client.vastu(f"jobs/{JOB}", {})
        client.vastu(f"jobs/{JOB}/results", {"cursor": "c1"})
        client.vastu(f"jobs/{JOB}/cancel", {})
        client.vastu("jobs", JOB_BODY, idempotency_key="k1")
    assert [c.args[:2] for c in request.call_args_list] == [
        ("GET", f"/v2/astrology/vastu/jobs/{JOB}"),
        ("GET", f"/v2/astrology/vastu/jobs/{JOB}/results"),
        ("POST", f"/v2/astrology/vastu/jobs/{JOB}/cancel"),
        ("POST", "/v2/astrology/vastu/jobs"),
    ]
    with pytest.raises(ValueError, match="job_id"):
        client.vastu("jobs/vjob_x/results", {})
    with pytest.raises(ValueError, match="Job paths"):
        client.vastu("jobs/../../x", {})
    with pytest.raises(ValueError, match="vastu_job_status"):
        client.vastu_operation(VastuOperation.JOBS_ID)


@pytest.mark.parametrize("key", [None, "", "   "])
def test_submit_requires_a_retained_key_before_transport(key):
    client = VedikaClient(api_key="vk_test")
    with patch.object(client.session, "request") as transport:
        with pytest.raises(ValueError, match="Idempotency-Key"):
            client.vastu_job_submit(JOB_BODY, idempotency_key=key)
        with pytest.raises(ValueError, match="Idempotency-Key"):
            client.vastu("jobs", JOB_BODY, idempotency_key=key)
        transport.assert_not_called()


def test_submit_keeps_its_key_across_a_retry_and_a_new_client():
    ok = {"success": True, "data": {"jobId": JOB, "status": "queued", "itemCount": 1, "maxCharge": 0.1, "replayed": False}}
    with serve(lambda m, p, i: (503, {"error": "retry"}) if i == 0 else (202, ok)) as (seen, client):
        assert client(max_retries=1).vastu_job_submit(JOB_BODY, idempotency_key="saved-job-7") == ok
        client(max_retries=1).vastu_job_submit(JOB_BODY, idempotency_key="saved-job-7")
    assert len(seen) == 3
    for request in seen:
        assert (request["method"], request["path"]) == ("POST", "/v2/astrology/vastu/jobs")
        assert header(request, "Idempotency-Key") == "saved-job-7"
        assert json.loads(request["raw"]) == JOB_BODY


def test_status_results_and_cancel_use_the_right_verbs_and_paths():
    def answer(method, path, index):
        if method == "GET" and path.endswith(JOB):
            return 200, {"success": True, "data": STATUS}
        if method == "GET":
            return 200, {"success": True, "data": {"jobId": JOB, "jobStatus": "running", "results": [], "nextCursor": None}}
        return 200, {"success": True, "data": {**STATUS, "status": "cancelled", "cancelRequested": True}}

    with serve(answer) as (seen, client):
        c = client()
        assert c.vastu_job_status(JOB)["data"]["jobId"] == JOB
        c.vastu_job_results(JOB, cursor="abc")
        assert c.vastu_job_cancel(JOB)["data"]["cancelRequested"] is True
    assert [(r["method"], r["path"]) for r in seen] == [
        ("GET", f"/v2/astrology/vastu/jobs/{JOB}"),
        ("GET", f"/v2/astrology/vastu/jobs/{JOB}/results?cursor=abc"),
        ("POST", f"/v2/astrology/vastu/jobs/{JOB}/cancel"),
    ]


def test_job_ids_and_cursors_are_checked_before_any_request():
    client = VedikaClient(api_key="vk_test")
    with patch.object(client.session, "request") as transport:
        for bad in ("", "vjob_x", "../keys", f"{JOB}/../x", None):
            with pytest.raises(ValueError, match="job_id"):
                client.vastu_job_status(bad)
            with pytest.raises(ValueError, match="job_id"):
                client.vastu_job_cancel(bad)
        with pytest.raises(ValueError, match="cursor"):
            client.vastu_job_results(JOB, cursor="x" * 33)
        transport.assert_not_called()


def test_result_items_follow_next_cursor_to_the_end():
    def item(i):
        return {"id": f"p{i}", "index": i, "status": 200, "response": {"success": True}}

    def answer(method, path, index):
        cursor = parse_qs(urlparse(path).query).get("cursor")
        if not cursor:
            return 200, {"success": True, "data": {"jobId": JOB, "jobStatus": "running", "results": [item(0), item(1)], "nextCursor": "c2"}}
        return 200, {"success": True, "data": {"jobId": JOB, "jobStatus": "completed", "results": [item(2)], "nextCursor": None}}

    with serve(answer) as (seen, client):
        indexes = [i["index"] for i in client().vastu_job_result_items(JOB)]
    assert indexes == [0, 1, 2]
    assert [r["path"] for r in seen] == [
        f"/v2/astrology/vastu/jobs/{JOB}/results", f"/v2/astrology/vastu/jobs/{JOB}/results?cursor=c2"]


PDF = b"%PDF-1.4\n" + bytes([0, 255, 13, 10, 7]) + b"\n%%EOF"


def test_upload_sends_one_multipart_file_under_a_retained_key_and_retries_the_same_body():
    ok = {"success": True, "uploadId": UPLOAD, "pages": 1, "charsExtracted": 10, "expiresAt": "x",
          "digestSha256": "a", "fileSha256": "b"}
    with serve(lambda m, p, i: (503, {"error": "retry"}) if i == 0 else (200, ok)) as (seen, client):
        result = client(max_retries=1).upload_vastu_report(PDF, idempotency_key="upload-1", filename="plan.pdf")
    assert result == ok
    assert len(seen) == 2
    for request in seen:
        assert (request["method"], request["path"]) == ("POST", "/api/v1/vastu/chat/uploads")
        assert header(request, "Idempotency-Key") == "upload-1"
        content_type = header(request, "Content-Type")
        boundary = re.search(r"^multipart/form-data; boundary=(.+)$", content_type).group(1)
        raw = request["raw"]
        assert b'name="file"; filename="plan.pdf"' in raw
        assert b"Content-Type: application/pdf\r\n\r\n" in raw
        assert PDF in raw
        assert raw.rstrip().endswith(f"--{boundary}--".encode())
    assert seen[0]["raw"] == seen[1]["raw"]


def test_upload_refuses_a_bad_key_or_empty_bytes_before_sending():
    client = VedikaClient(api_key="vk_test")
    with patch.object(client.session, "request") as transport:
        for key in (None, "", "has space", "x" * 257):
            with pytest.raises(ValueError, match="Idempotency-Key"):
                client.upload_vastu_report(PDF, idempotency_key=key)
        with pytest.raises(ValueError, match="bytes"):
            client.upload_vastu_report(b"", idempotency_key="k")
        transport.assert_not_called()


def test_ask_vastu_report_accepts_an_upload_reference_alone():
    answer = {"success": True, "response": "Fix the toilet first.", "conversationId": "c1"}
    with serve(lambda m, p, i: (200, answer)) as (seen, client):
        client().ask_vastu_report("What first?", report_ref={"type": "upload", "id": UPLOAD})
    body = json.loads(seen[0]["raw"])
    assert body["vastuContext"] == {"reportRef": {"type": "upload", "id": UPLOAD}}


def test_ask_vastu_report_refuses_report_plus_reference_and_a_malformed_reference():
    client = VedikaClient(api_key="vk_test")
    with patch.object(client.session, "request") as transport:
        with pytest.raises(ValueError, match="exactly one"):
            client.ask_vastu_report("q", {"method": "audit"}, report_ref={"type": "upload", "id": UPLOAD})
        with pytest.raises(ValueError, match="report_ref"):
            client.ask_vastu_report("q", report_ref={"type": "scan", "id": UPLOAD})
        with pytest.raises(ValueError, match="report_ref"):
            client.ask_vastu_report("q", report_ref={"type": "upload", "id": "x"})
        transport.assert_not_called()


NAMED = [
    ("vastu_listing_assessment", lambda c, k: c.vastu_listing_assessment({"inputSource": "plan-derived"}, idempotency_key=k), "/v2/astrology/vastu/assessments"),
    ("vastu_score", lambda c, k: c.vastu_score("overall", {"rooms": []}, idempotency_key=k), "/v2/astrology/vastu/score/overall"),
    ("vastu_audit", lambda c, k: c.vastu_audit("floor-plan", {"rooms": []}, idempotency_key=k), "/v2/astrology/vastu/audit/floor-plan"),
    ("vastu_room", lambda c, k: c.vastu_room("kitchen", {"zone": "SE"}, idempotency_key=k), "/v2/astrology/vastu/room/kitchen"),
    ("vastu_placement", lambda c, k: c.vastu_placement("borewell", {"zone": "NE"}, idempotency_key=k), "/v2/astrology/vastu/placement/borewell"),
    ("vastu_mandala_project", lambda c, k: c.vastu_mandala_project("9-zone", {"plotPolygon": []}, idempotency_key=k), "/v2/astrology/vastu/mandala/project/9-zone"),
    ("vastu_entrance_pada", lambda c, k: c.vastu_entrance_pada({"plotPolygon": [], "doorXY": [0, 0]}, idempotency_key=k), "/v2/astrology/vastu/entrance/pada"),
]


@pytest.mark.parametrize("name,call,path", NAMED, ids=[n[0] for n in NAMED])
def test_named_helper_reuses_a_retained_key_on_a_new_invocation(name, call, path):
    with serve(lambda m, p, i: (200, {"success": True, "data": {"ok": True}})) as (seen, client):
        call(client(), "lost-1")
        call(client(), "lost-1")
    assert len(seen) == 2
    for request in seen:
        assert request["path"] == path
        assert header(request, "Idempotency-Key") == "lost-1"


def test_named_helper_sends_no_key_unless_the_caller_passes_one():
    # score/overall is not an idempotency-certified operation: a generated key
    # would be answered with 422, so none is sent. A caller key is passed through.
    with serve(lambda m, p, i: (200, {"success": True, "data": {}})) as (seen, client):
        client().vastu_score("overall", {})
        client().vastu_score("overall", {}, idempotency_key="caller-key-1")
    assert header(seen[0], "Idempotency-Key") is None
    assert header(seen[1], "Idempotency-Key") == "caller-key-1"


def test_named_helper_refuses_a_blank_retained_key_before_transport():
    client = VedikaClient(api_key="vk_test")
    with patch.object(client.session, "request") as transport:
        with pytest.raises(ValueError, match="Idempotency-Key"):
            client.vastu_score("overall", {}, idempotency_key=" ")
        transport.assert_not_called()
