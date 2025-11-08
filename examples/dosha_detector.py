#!/usr/bin/env python3
"""
Dosha Detector Example

This example demonstrates how to detect and analyze various doshas:
- Kaal Sarp Dosha
- Mangal Dosha
- Sade Sati
- Pitra Dosha
"""

import os
from vedika import VedikaClient
from vedika.exceptions import VedikaAPIError


def print_dosha_info(name, dosha_info):
    """Pretty print dosha information."""
    print(f"\n{name}:")
    print("  " + "-" * 56)

    if dosha_info.present:
        severity_emoji = {
            "High": "🔴",
            "Medium": "🟡",
            "Low": "🟢"
        }.get(dosha_info.severity, "⚪")

        print(f"  Status: ❌ PRESENT {severity_emoji}")
        if dosha_info.type:
            print(f"  Type: {dosha_info.type}")
        if dosha_info.severity:
            print(f"  Severity: {dosha_info.severity}")
        if dosha_info.description:
            print(f"  Description: {dosha_info.description}")

        if dosha_info.remedies:
            print(f"\n  🙏 Remedies:")
            for i, remedy in enumerate(dosha_info.remedies, 1):
                print(f"     {i}. {remedy}")
    else:
        print(f"  Status: ✅ NOT PRESENT")


def main():
    # Initialize client
    api_key = os.getenv("VEDIKA_API_KEY")
    if not api_key:
        print("❌ Please set VEDIKA_API_KEY environment variable")
        return

    client = VedikaClient(api_key=api_key)

    # Birth details
    birth_details = {
        "datetime": "1990-06-15T14:30:00+05:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata"
    }

    print("🔍 Dosha Detector")
    print("=" * 60)
    print("\n📅 Birth Details:")
    print("  Date/Time: June 15, 1990 at 2:30 PM")
    print("  Location: Delhi, India")
    print()

    try:
        # Analyze doshas
        print("🔮 Analyzing doshas...")
        doshas = client.analyze_doshas(birth_details=birth_details)

        # Display results
        print("\n" + "=" * 60)
        print("✨ DOSHA ANALYSIS RESULTS")
        print("=" * 60)

        # Kaal Sarp Dosha
        print_dosha_info("🐍 Kaal Sarp Dosha", doshas.kaal_sarp_dosha)

        # Mangal Dosha
        print_dosha_info("🔥 Mangal Dosha (Kuja Dosha)", doshas.mangal_dosha)

        # Sade Sati
        print_dosha_info("🪐 Sade Sati", doshas.sade_sati)

        # Pitra Dosha
        print_dosha_info("👴 Pitra Dosha", doshas.pitra_dosha)

        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)

        doshas_present = []
        if doshas.kaal_sarp_dosha.present:
            doshas_present.append("Kaal Sarp Dosha")
        if doshas.mangal_dosha.present:
            doshas_present.append("Mangal Dosha")
        if doshas.sade_sati.present:
            doshas_present.append("Sade Sati")
        if doshas.pitra_dosha.present:
            doshas_present.append("Pitra Dosha")

        if doshas_present:
            print(f"\n⚠️  Doshas found: {', '.join(doshas_present)}")
            print("\n💡 Recommendation:")
            print("  Consult with an experienced astrologer for remedies")
            print("  and personalized guidance.")
        else:
            print("\n✅ No major doshas detected!")
            print("  This is a favorable astrological indication.")

        print("\n" + "=" * 60)
        print("\n✅ Dosha analysis complete!")

    except VedikaAPIError as e:
        print(f"\n❌ API Error: {e}")


if __name__ == "__main__":
    main()
