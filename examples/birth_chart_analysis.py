#!/usr/bin/env python3
"""
Birth Chart Analysis Example

This example demonstrates how to generate a complete birth chart (Kundali)
with planetary positions, houses, and ascendant.
"""

import os
from vedika import VedikaClient
from vedika.exceptions import VedikaAPIError


def print_planet(planet):
    """Pretty print planet information."""
    retrograde = " (R)" if planet.retrograde else ""
    print(f"  {planet.name:12s} → {planet.sign:12s} "
          f"| House {planet.house} | {planet.nakshatra}{retrograde}")


def print_house(house):
    """Pretty print house information."""
    print(f"  House {house.number:2d} → {house.sign:12s} "
          f"| {house.degree:.2f}° | Lord: {house.lord}")


def main():
    # Initialize client
    api_key = os.getenv("VEDIKA_API_KEY")
    if not api_key:
        print("❌ Please set VEDIKA_API_KEY environment variable")
        return

    client = VedikaClient(api_key=api_key)

    # Birth details
    print("📅 Birth Details:")
    print("  Date/Time: June 15, 1990 at 2:30 PM")
    print("  Location: Delhi, India")
    print()

    try:
        # Generate birth chart
        print("🔮 Generating birth chart...")
        chart = client.get_birth_chart(
            datetime="1990-06-15T14:30:00+05:30",
            latitude=28.6139,
            longitude=77.2090,
            timezone="Asia/Kolkata",
            ayanamsa="lahiri"  # Try: lahiri, raman, krishnamurti
        )

        # Display results
        print("\n" + "=" * 60)
        print("✨ BIRTH CHART (KUNDALI)")
        print("=" * 60)

        # Ascendant
        print(f"\n🌅 Ascendant (Lagna): {chart.ascendant}")
        print(f"   Ayanamsa: {chart.ayanamsa.title()}")

        # Planets
        print("\n🪐 Planetary Positions:")
        print("  " + "-" * 56)
        print(f"  {'Planet':<12s}   {'Sign':<12s}   House   Nakshatra")
        print("  " + "-" * 56)
        for planet in chart.planets:
            print_planet(planet)

        # Houses
        print("\n🏠 House Cusps:")
        print("  " + "-" * 56)
        for house in chart.houses:
            print_house(house)

        print("\n" + "=" * 60)

        # Additional analysis
        print("\n💡 Quick Analysis:")

        # Count retrograde planets
        retrograde_planets = [p for p in chart.planets if p.retrograde]
        if retrograde_planets:
            print(f"  • Retrograde planets: {', '.join(p.name for p in retrograde_planets)}")
        else:
            print("  • No retrograde planets")

        # Find planets in own sign
        own_sign_planets = [p for p in chart.planets
                          if p.name.lower() in p.sign.lower()]
        if own_sign_planets:
            print(f"  • Planets in own sign: {', '.join(p.name for p in own_sign_planets)}")

        print("\n✅ Birth chart generated successfully!")

    except VedikaAPIError as e:
        print(f"\n❌ API Error: {e}")


if __name__ == "__main__":
    main()
