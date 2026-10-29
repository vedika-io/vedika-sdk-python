"""Package-boundary proof: the named room-scan helpers are importable
from the ``vedika`` package root (and by wildcard) and reach the real client
transport. The private-module refusals stay in test_vastu_room_capture.py."""

import json
from pathlib import Path
from reference_fixtures import reference_path

import pytest
import requests

import vedika

FIXTURE = reference_path("sdks/fixtures/room-scan-bridge/messages.json", "room-scan-messages.json")
NAMES = ("upload_room_capture", "merge_room_captures")


@pytest.fixture(scope="module")
def fx():
    return json.loads(FIXTURE.read_text())


class _Recorder(requests.adapters.BaseAdapter):
    """Sits under the client's real requests.Session; no socket is opened."""

    def __init__(self):
        super().__init__()
        self.sent = []

    def send(self, request, **kwargs):
        self.sent.append(request)
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"success": true, "data": {"ok": true}}'
        response.headers["Content-Type"] = "application/json"
        response.url = request.url
        response.request = request
        return response

    def close(self):
        pass


@pytest.fixture
def wired():
    client = vedika.VedikaClient(api_key="vk_test")
    recorder = _Recorder()
    client.session.mount("https://", recorder)
    client.session.mount("http://", recorder)
    return client, recorder


def test_package_root_exports_the_named_helpers():
    for name in NAMES:
        assert callable(getattr(vedika, name)), name
        assert name in vedika.__all__, name


def test_wildcard_import_includes_the_named_helpers():
    namespace = {}
    exec("from vedika import *", namespace)
    for name in NAMES:
        assert callable(namespace.get(name)), name


def test_upload_through_the_package_root_posts_room_capture_with_the_caller_key(wired, fx):
    client, recorder = wired
    result = vedika.upload_room_capture(client, fx["validCapture"], zone_resolution=16, idempotency_key="pkg-room-key-0001")
    assert result == {"success": True, "data": {"ok": True}}
    (request,) = recorder.sent
    assert request.method == "POST"
    assert request.url.endswith("/v2/astrology/vastu/ar/room-capture")
    assert json.loads(request.body) == {"capture": fx["validCapture"], "zoneResolution": 16}
    assert request.headers["Idempotency-Key"] == "pkg-room-key-0001"


def test_merge_through_the_package_root_posts_capture_merge_with_the_retained_key(wired, fx):
    client, recorder = wired
    vedika.merge_room_captures(client, fx["mergeBody"], idempotency_key="pkg-merge-key-0001")
    (request,) = recorder.sent
    assert request.method == "POST"
    assert request.url.endswith("/v2/astrology/vastu/ar/capture-merge")
    assert json.loads(request.body) == fx["mergeBody"]
    assert request.headers["Idempotency-Key"] == "pkg-merge-key-0001"
