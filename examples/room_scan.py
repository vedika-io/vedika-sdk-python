#!/usr/bin/env python3
"""Room scan example: upload a finished room scan, then show the merge rule.

A room scan runs in a page (WebXR) or a native scanner (RoomPlan, ARCore) and ends as
a ``vedika.roomCapture/1`` object. ``upload_room_capture`` sends it to
POST /v2/astrology/vastu/ar/room-capture and ``merge_room_captures`` joins floors through
POST /v2/astrology/vastu/ar/capture-merge.

Run it with no key to see exactly what would be sent. Nothing leaves the machine:

    python room_scan.py

``--live`` sends the upload and the two-floor merge for real. Both calls are billed, so it needs your API key:

    VEDIKA_API_KEY=vk_live_... python room_scan.py --live
"""

import json
import os
import sys

from vedika import VedikaClient, ValidationError, merge_room_captures, upload_room_capture

# A 3 m x 4 m kitchen in a traced 9 m x 12 m house. Replace it with the capture your scanner produced.
CAPTURE = json.loads("""
{
  "attestation": "caller-reported",
  "captureId": "fx-room-3x4-yaw0",
  "capturedAtEpoch": 1789000000,
  "device": {
    "depth": "none",
    "method": "webxr-hit",
    "platform": "web"
  },
  "frame": {
    "axes": "+X east,+Y true north",
    "north": {
      "compassConfidence": 0.939,
      "declinationDeg": 1.2,
      "declinationProvenance": "fixture",
      "headingSource": "deviceorientationabsolute",
      "referenceFrame": "true",
      "yawSamples": 17,
      "yawSpreadDeg": 1.22
    },
    "planToWorld": {
      "origin": [
        0.7,
        -1.4,
        2.3
      ],
      "units": "metres",
      "xAxis": [
        1.0,
        0,
        -5.12e-07
      ],
      "yAxis": [
        -5.12e-07,
        0,
        -1.0
      ]
    },
    "units": "metres"
  },
  "outline": {
    "polygon": [
      [
        0.0,
        0.0
      ],
      [
        9.0,
        0.0
      ],
      [
        9.0,
        12.0
      ],
      [
        0.0,
        12.0
      ]
    ],
    "source": "traced"
  },
  "quality": {
    "closureGapM": 0.0,
    "coveragePercent": null,
    "expectedRoomCount": 1,
    "gpsConfidence": null,
    "pointCloudDensity": null,
    "pointCloudDensityBasis": "none",
    "polygonClosure": true,
    "roomCount": 1,
    "roomsTagged": 1,
    "scanDurationSec": 160,
    "scannedAreaM2": 108
  },
  "rooms": [
    {
      "areaM2": 12.0,
      "floorIndex": 0,
      "heightM": 2.8,
      "id": "r1",
      "label": "kitchen",
      "labelSource": "user",
      "openings": [
        {
          "centerXY": [
            9.0,
            1.0
          ],
          "confidence": "high",
          "heightM": 2.1,
          "kind": "door",
          "widthM": 0.9
        }
      ],
      "polygon": [
        [
          6.0,
          0.0
        ],
        [
          9.0,
          0.0
        ],
        [
          9.0,
          4.0
        ],
        [
          6.0,
          4.0
        ]
      ]
    }
  ],
  "schema": "vedika.roomCapture/1"
}
""")


def upstairs(base):
    """The same house's upstairs scan: a merge needs 2 to 32 captures, each on a floor with its own frame."""
    return {**base, "captureId": base["captureId"] + "-upstairs",
            "rooms": [{**room, "floorIndex": 1} for room in base["rooms"]]}


def merge_body(base):
    """Two floors, one capture each, no links: the smallest merge the API accepts."""
    return {
        "captures": [
            {"id": "ground", "floorIndex": 0, "payload": base},
            {"id": "upstairs", "floorIndex": 1, "payload": upstairs(base)},
        ],
        "floors": [
            {"floorIndex": 0, "originXY": [0, 0], "bearingDeg": 0, "elevationM": 0},
            {"floorIndex": 1, "originXY": [0, 0], "bearingDeg": 0, "elevationM": 3},
        ],
        "links": [],
        "toleranceM": 0.05,
    }


class DryRunClient:
    """The one method the helpers use, printed instead of sent."""

    def vastu_operation(self, operation, request, idempotency_key=None):
        name = getattr(operation, "value", operation)
        print("REQUEST " + json.dumps({"operation": name, "idempotencyKey": idempotency_key, "keys": sorted(request), "captures": len(request.get("captures", []))}))
        return {"dryRun": True, "operation": name}


def main(argv):
    client = DryRunClient()
    if "--live" in argv:
        api_key = os.environ.get("VEDIKA_API_KEY")
        if not api_key:
            print("Set VEDIKA_API_KEY to use --live")
            return 1
        client = VedikaClient(api_key=api_key, base_url=os.environ.get("VEDIKA_BASE_URL", "https://api.vedika.io"))

    # One key per capture. Keep it for every retry: the API replays the first answer
    # instead of charging again.
    key = "room-" + CAPTURE["captureId"]
    first = upload_room_capture(client, CAPTURE, zone_resolution=16, idempotency_key=key)
    print("Uploaded:", json.dumps(first)[:200])
    upload_room_capture(client, CAPTURE, zone_resolution=16, idempotency_key=key)

    # A capture with no tagged room is refused before any request.
    untagged = {**CAPTURE, "quality": {**CAPTURE["quality"], "roomsTagged": 0}}
    try:
        upload_room_capture(client, untagged)
    except ValidationError as error:
        print("REFUSED untagged capture:", error)

    # A merge is billed, so it never goes out without the key you keep for it.
    body = merge_body(CAPTURE)
    try:
        merge_room_captures(client, body, idempotency_key="")
    except ValidationError as error:
        print("REFUSED merge without a key:", error)
    merge_room_captures(client, body, idempotency_key="merge-" + CAPTURE["captureId"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
