#!/usr/bin/env python3
"""
Vastu Audit Example

This example demonstrates the Vastu surface (93 operation paths).

Vastu takes a BUILDING (plot polygon, room list, compass zone) — NEVER a
birth chart. There is no `birth_details` anywhere in this example.
"""

import os
from vedika import VedikaClient
from vedika.exceptions import VedikaAPIError


def main():
    # Initialize client
    api_key = os.getenv("VEDIKA_API_KEY")
    if not api_key:
        print("❌ Please set VEDIKA_API_KEY environment variable")
        return 1

    client = VedikaClient(api_key=api_key, base_url=os.getenv("VEDIKA_BASE_URL", "https://api.vedika.io"))

    # A simple rectangular plot, north-facing, with a small room programme.
    # Coordinates use [x, y] pairs here. The API also accepts {x, y} points.
    plot = {
        "plotPolygon": [
            [0, 0],
            [40, 0],
            [40, 60],
            [0, 60],
        ],
        "bearingDeg": 0,
    }
    rooms = [
        {"roomType": "kitchen", "zone": "southeast"},
        {"roomType": "pooja", "zone": "northeast"},
        {"roomType": "toilet", "zone": "northwest"},
    ]

    try:
        print("🧭 Vastu Audit")
        print("=" * 60)

        # 1. Reference table — no building input required.
        print("\n📖 Reference: 9-zone mandala")
        mandala_ref = client.vastu_reference("reference/mandala/9-zone")
        print(f"  {mandala_ref}")

        # 2. Project a mandala onto the plot.
        print("\n🗺️  Mandala projection (9-zone)")
        mandala = client.vastu_mandala_project("9-zone", plot)
        print(f"  {mandala}")

        # 3. Classify the entrance door position (dedicated method).
        print("\n🚪 Entrance pada classification")
        entrance = client.vastu_entrance_pada({**plot, "doorXY": [20, 0]})
        print(f"  {entrance}")

        # 4. Single-room placement check (dedicated method).
        print("\n🍳 Kitchen placement check")
        kitchen = client.vastu_room("kitchen", {"zone": "southeast", "plot": plot})
        print(f"  {kitchen}")

        # 5. Full floor-plan compliance audit (dedicated method).
        print("\n📋 Floor-plan audit")
        audit = client.vastu_audit("floor-plan", {"rooms": rooms, "plot": plot})
        print(f"  {audit}")

        # 6. Overall Vastu score (dedicated method).
        print("\n🏆 Overall score")
        score = client.vastu_score("overall", {"rooms": rooms, "plot": plot})
        print(f"  {score}")

        # 7. Magnetic declination for true-north correction (GET + query params).
        print("\n🧲 Magnetic declination (Delhi)")
        declination = client.vastu_declination(lat=28.6139, lon=77.2090)
        print(f"  {declination}")

        # 8. Long-tail operation via the generic escape hatch — every one of the
        #    93 paths in vastu-inventory.json is reachable this way even before
        #    a dedicated method exists for it.
        print("\n🏭 Specialized building type (via generic vastu() escape hatch)")
        specialized = client.vastu("specialized/residential", {"rooms": rooms, "plot": plot})
        print(f"  {specialized}")

        print("\n✅ Vastu audit complete!")

    except VedikaAPIError as e:
        print(f"\n❌ API Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
