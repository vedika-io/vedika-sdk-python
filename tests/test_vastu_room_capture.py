import json
from pathlib import Path
from reference_fixtures import reference_path
from unittest.mock import MagicMock

import pytest

from vedika.client import VedikaClient
from vedika.exceptions import ValidationError
from vedika.vastu_room_capture import merge_room_captures, upload_room_capture

FIXTURE = reference_path("sdks/fixtures/room-scan-bridge/messages.json", "room-scan-messages.json")


@pytest.fixture(scope="module")
def fx():
    return json.loads(FIXTURE.read_text())


@pytest.fixture
def client():
    c = VedikaClient(api_key="vk_test")
    c._request = MagicMock(return_value={"success": True})
    return c


def test_upload_posts_to_room_capture_with_the_caller_key(client, fx):
    result = upload_room_capture(client, fx["validCapture"], zone_resolution=16, idempotency_key="room-key-0001")
    assert result == {"success": True}
    args, kwargs = client._request.call_args
    assert args == ("POST", "/v2/astrology/vastu/ar/room-capture")
    assert kwargs["data"] == {"capture": fx["validCapture"], "zoneResolution": 16}
    assert kwargs["idempotency_key"] == "room-key-0001"


def test_upload_without_a_key_sends_none(client, fx):
    upload_room_capture(client, fx["validCapture"])
    assert client._request.call_args.kwargs["idempotency_key"] is None


def test_upload_refuses_an_untagged_capture_without_a_request(client, fx):
    with pytest.raises(ValidationError, match="Tag at least one room"):
        upload_room_capture(client, fx["untaggedCapture"])
    client._request.assert_not_called()


@pytest.mark.parametrize("bad", [None, {}, {"schema": "vedika.roomCapture/2", "quality": {"roomsTagged": 1}}, "x"])
def test_upload_refuses_a_non_capture(client, bad):
    with pytest.raises(ValidationError, match=r"vedika\.roomCapture/1"):
        upload_room_capture(client, bad)
    client._request.assert_not_called()


def test_upload_refuses_a_bad_zone_resolution(client, fx):
    with pytest.raises(ValidationError, match="zone_resolution"):
        upload_room_capture(client, fx["validCapture"], zone_resolution=9)
    client._request.assert_not_called()


def test_merge_posts_to_capture_merge_and_keeps_identity_across_retries(client, fx):
    merge_room_captures(client, fx["mergeBody"], idempotency_key="merge-key-0001")
    merge_room_captures(client, fx["mergeBody"], idempotency_key="merge-key-0001")
    calls = client._request.call_args_list
    assert [c.args for c in calls] == [("POST", "/v2/astrology/vastu/ar/capture-merge")] * 2
    assert [c.kwargs["idempotency_key"] for c in calls] == ["merge-key-0001"] * 2
    assert calls[0].kwargs["data"] == fx["mergeBody"]


@pytest.mark.parametrize("key", [None, "", "has space", "x" * 257, 7])
def test_merge_refuses_a_missing_or_bad_key_without_a_request(client, fx, key):
    with pytest.raises(ValidationError, match="idempotency_key"):
        merge_room_captures(client, fx["mergeBody"], idempotency_key=key)
    client._request.assert_not_called()
