#!/usr/bin/env python3
"""
Marriage Compatibility Checker Example

This example demonstrates how to check marriage compatibility using
Ashtakoota matching (36-point system).
"""

import os
from vedika import VedikaClient
from vedika.exceptions import VedikaAPIError


def get_compatibility_emoji(score):
    """Return emoji based on compatibility score."""
    if score >= 30:
        return "💚"
    elif score >= 24:
        return "💛"
    elif score >= 18:
        return "🧡"
    else:
        return "❤️"


def print_koota_score(name, score, max_score):
    """Pretty print koota score with progress bar."""
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    bar_length = 20
    filled = int((score / max_score) * bar_length) if max_score > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)

    print(f"  {name:15s} [{bar}] {score}/{max_score} ({percentage:.0f}%)")


def main():
    # Initialize client
    api_key = os.getenv("VEDIKA_API_KEY")
    if not api_key:
        print("❌ Please set VEDIKA_API_KEY environment variable")
        return

    client = VedikaClient(api_key=api_key)

    # Person 1 details
    person1 = {
        "datetime": "1990-06-15T14:30:00+05:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata"
    }

    # Person 2 details
    person2 = {
        "datetime": "1992-08-20T10:15:00+05:30",
        "latitude": 19.0760,  # Mumbai
        "longitude": 72.8777,
        "timezone": "Asia/Kolkata"
    }

    print("💑 Marriage Compatibility Checker")
    print("=" * 60)
    print("\n👤 Person 1:")
    print("  Birth: June 15, 1990 at 2:30 PM, Delhi")
    print("\n👤 Person 2:")
    print("  Birth: August 20, 1992 at 10:15 AM, Mumbai")
    print()

    try:
        # Check compatibility
        print("🔮 Analyzing compatibility...")
        compatibility = client.check_compatibility(
            person1_details=person1,
            person2_details=person2
        )

        # Display results
        print("\n" + "=" * 60)
        print("✨ ASHTAKOOTA MATCHING RESULTS")
        print("=" * 60)

        # Overall score
        emoji = get_compatibility_emoji(compatibility.total_score)
        print(f"\n{emoji} Overall Compatibility: {compatibility.total_score}/36")
        print(f"   Rating: {compatibility.compatibility_level}")
        print()

        # Individual koota scores
        print("📊 Detailed Koota Breakdown:")
        print()
        print_koota_score("Varna", compatibility.varna, 1)
        print_koota_score("Vashya", compatibility.vashya, 2)
        print_koota_score("Tara", compatibility.tara, 3)
        print_koota_score("Yoni", compatibility.yoni, 4)
        print_koota_score("Graha Maitri", compatibility.graha_maitri, 5)
        print_koota_score("Gana", compatibility.gana, 6)
        print_koota_score("Bhakoot", compatibility.bhakoot, 7)
        print_koota_score("Nadi", compatibility.nadi, 8)

        # Interpretation
        print("\n💡 Interpretation:")
        if compatibility.total_score >= 30:
            print("  Excellent compatibility! This is a very promising match.")
            print("  The couple is likely to have a harmonious relationship.")
        elif compatibility.total_score >= 24:
            print("  Good compatibility. The match has strong potential.")
            print("  Some areas may need understanding and adjustment.")
        elif compatibility.total_score >= 18:
            print("  Average compatibility. The match can work with effort.")
            print("  Communication and mutual respect will be important.")
        else:
            print("  Low compatibility. This match may face challenges.")
            print("  Consider consulting an astrologer for remedies.")

        # Mangal Dosha check
        if compatibility.mangal_dosha_check:
            print(f"\n⚠️  Mangal Dosha: {compatibility.mangal_dosha_check}")

        print("\n" + "=" * 60)
        print("\n✅ Compatibility analysis complete!")

    except VedikaAPIError as e:
        print(f"\n❌ API Error: {e}")


if __name__ == "__main__":
    main()
