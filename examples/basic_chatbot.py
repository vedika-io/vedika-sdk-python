#!/usr/bin/env python3
"""
Basic AI Astrology Chatbot Example

This example demonstrates how to use Vedika's unique AI-powered chatbot
to ask conversational astrology questions.

UNIQUE FEATURE: Only Vedika offers AI chatbot queries for astrology!
"""

import os
from vedika import VedikaClient
from vedika.exceptions import VedikaAPIError


def main():
    # Initialize client with API key from environment
    api_key = os.getenv("VEDIKA_API_KEY")
    if not api_key:
        print("❌ Please set VEDIKA_API_KEY environment variable")
        print("   Get your key at: https://vedika.io/dashboard.html")
        return

    client = VedikaClient(api_key=api_key)

    # Sample birth details
    birth_details = {
        "datetime": "1990-06-15T14:30:00+05:30",
        "latitude": 28.6139,   # Delhi
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata"
    }

    # Example questions to ask
    questions = [
        "What are my career prospects for this year?",
        "When is the best time for me to start a new business?",
        "What are the major yogas in my birth chart?",
        "Do I have Kaal Sarp Dosha?",
        "What is my current Mahadasha period?"
    ]

    print("🌟 Vedika AI Astrology Chatbot")
    print("=" * 50)
    print()

    # Interactive mode
    while True:
        print("\nExample questions:")
        for i, q in enumerate(questions, 1):
            print(f"{i}. {q}")
        print("0. Enter custom question")
        print("q. Quit")

        choice = input("\nSelect a question (1-5, 0, q): ").strip()

        if choice.lower() == 'q':
            print("\n👋 Goodbye!")
            break

        if choice == '0':
            question = input("Enter your question: ").strip()
            if not question:
                continue
        elif choice.isdigit() and 1 <= int(choice) <= len(questions):
            question = questions[int(choice) - 1]
        else:
            print("❌ Invalid choice")
            continue

        try:
            print(f"\n🤔 Asking: {question}")
            print("⏳ Processing (this may take 20-40 seconds)...\n")

            # Ask the question
            response = client.ask_question(
                question=question,
                birth_details=birth_details,
                language="en"  # Try "hi" for Hindi!
            )

            # Display results
            print("=" * 50)
            print("✨ ANSWER:")
            print("=" * 50)
            print(response.answer)
            print()
            print(f"📊 Confidence: {response.confidence:.1%}")
            print(f"💰 Credits used: {response.credits_used}")
            print(f"⏱️  Processing time: {response.processing_time:.2f}s")
            print("=" * 50)

        except VedikaAPIError as e:
            print(f"\n❌ API Error: {e}")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
