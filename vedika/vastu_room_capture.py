"""Named helpers for the two room-scan operations.

``upload_room_capture`` sends ``ar/room-capture`` and ``merge_room_captures``
sends ``ar/capture-merge``. Both go through ``VedikaClient.vastu_operation``, so
auth, retries and error mapping are unchanged. They add the checks the Swift
``RoomCaptureUploader`` already makes before a round trip: an untagged capture is
refused, and a merge never goes out without the caller's retained idempotency key.
"""

import re
from typing import Any, Mapping, Optional, cast

from .client import (
    VastuArCaptureMergeRequest,
    VastuArCaptureMergeResponse,
    VastuArRoomCaptureRequest,
    VastuArRoomCaptureResponse,
    VastuDeviceAttestation,
    VastuOperation,
    VastuRoomCapture,
)
from .exceptions import ValidationError

ROOM_CAPTURE_SCHEMA = "vedika.roomCapture/1"
_KEY_RE = re.compile(r"^[\x21-\x7e]{1,256}$")


def upload_room_capture(
    client: Any,
    capture: VastuRoomCapture,
    *,
    zone_resolution: Optional[int] = None,
    device_attestation: Optional[VastuDeviceAttestation] = None,
    idempotency_key: Optional[str] = None,
) -> VastuArRoomCaptureResponse:
    """Upload a ``vedika.roomCapture/1`` to ``POST /v2/astrology/vastu/ar/room-capture``.

    Refuses before sending when the capture is not that schema or has no tagged
    room (the API would refuse it before any charge). Keep ``idempotency_key``
    across retries of the same capture.
    """
    if not isinstance(capture, Mapping) or capture.get("schema") != ROOM_CAPTURE_SCHEMA:
        raise ValidationError(f"capture must be a {ROOM_CAPTURE_SCHEMA} object from the room scan")
    quality = capture.get("quality")
    tagged = quality.get("roomsTagged") if isinstance(quality, Mapping) else None
    if not isinstance(tagged, int) or isinstance(tagged, bool) or tagged < 1:
        raise ValidationError("Tag at least one room before uploading: the API refuses a capture with no labelled room")
    request: dict = {"capture": capture}
    if zone_resolution is not None:
        if zone_resolution not in (8, 16, 32):
            raise ValidationError("zone_resolution must be 8, 16 or 32")
        request["zoneResolution"] = zone_resolution
    if device_attestation is not None:
        request["deviceAttestation"] = device_attestation
    return cast(
        VastuArRoomCaptureResponse,
        client.vastu_operation(
            VastuOperation.AR_ROOM_CAPTURE, cast(VastuArRoomCaptureRequest, request), idempotency_key=idempotency_key
        ),
    )


def merge_room_captures(
    client: Any,
    request: VastuArCaptureMergeRequest,
    *,
    idempotency_key: str,
) -> VastuArCaptureMergeResponse:
    """Merge floor captures through ``POST /v2/astrology/vastu/ar/capture-merge``.

    The merge is billed, so a caller-retained ``idempotency_key`` is mandatory: a
    retry with the same key replays the first result instead of charging again.
    """
    if not isinstance(idempotency_key, str) or not _KEY_RE.match(idempotency_key):
        raise ValidationError("A caller-retained idempotency_key (1-256 visible ASCII characters) is required to merge captures")
    return cast(
        VastuArCaptureMergeResponse,
        client.vastu_operation(VastuOperation.AR_CAPTURE_MERGE, request, idempotency_key=idempotency_key),
    )
