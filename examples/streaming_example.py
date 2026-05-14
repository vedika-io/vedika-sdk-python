#!/usr/bin/env python3
"""
Streaming Response Example

This example demonstrates how to stream AI responses in real-time
for better user experience.
"""

import os
import sys
from vedika import VedikaClient
from vedika.exceptions import VedikaAPIError


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
        "timezone": "+05:30"
    }

    # Question
    question = "What are my career prospects and what career path would be most suitable for me?"

    print("🌊 Streaming Response Example")
    print("=" * 60)
    print(f"\n❓ Question: {question}")
    print("\n⏳ Streaming response (this may take 20-40 seconds)...")
    print("\n" + "-" * 60)
    print()

    try:
        # Stream the response
        for chunk in client.ask_question_stream(
            question=question,
            birth_details=birth_details,
            language="en"
        ):
            # Print each chunk as it arrives (chunks are plain strings)
            print(chunk, end="", flush=True)

        print("\n" + "-" * 60)
        print(f"\n✅ Response complete!")

    except VedikaAPIError as e:
        print(f"\n\n❌ API Error: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Streaming interrupted by user")


if __name__ == "__main__":
    main()
