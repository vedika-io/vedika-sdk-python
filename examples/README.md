# Vedika Python SDK Examples

This directory contains example scripts demonstrating how to use the Vedika Python SDK.

## Setup

1. Install the SDK:
```bash
pip install vedika-sdk
```

2. Set your API key:
```bash
export VEDIKA_API_KEY="vk_live_..."
```

Or create a `.env` file:
```
VEDIKA_API_KEY=vk_live_...
```

## Examples

### Basic Examples

- **`basic_chatbot.py`** - Simple AI astrology chatbot
  - Ask conversational astrology questions
  - Get AI-powered insights
  - Best for: Getting started

- **`birth_chart_analysis.py`** - Complete birth chart generation
  - Generate full Kundali/Horoscope
  - Get planetary positions
  - Best for: Traditional astrology calculations

- **`compatibility_checker.py`** - Marriage compatibility analysis
  - Ashtakoota matching
  - 36-point compatibility scoring
  - Best for: Relationship analysis

### Advanced Examples

- **`dosha_detector.py`** - Comprehensive dosha analysis
  - Kaal Sarp Dosha
  - Mangal Dosha
  - Sade Sati
  - Best for: Identifying astrological doshas

- **`streaming_example.py`** - Real-time streaming responses
  - Stream AI responses as they're generated
  - Better user experience
  - Best for: Interactive applications

### Vastu Examples

- **`vastu_audit.py`** - Vastu compliance audit (93 operations)
  - Mandala projection, entrance classification, room placement, scoring
  - Vastu takes a BUILDING (plot polygon, rooms, compass zone), never a birth chart
  - Best for: Architectural / construction Vastu review

## Running Examples

```bash
# Basic chatbot
python examples/basic_chatbot.py

# Birth chart analysis
python examples/birth_chart_analysis.py

# Vastu compliance audit
python examples/vastu_audit.py
```

## Get Your API Key

Create an account at https://vedika.io/dashboard.html to get your API key.

## Need Help?

- Documentation: https://vedika.io/docs.html
- Support: support@vedika.io
- GitHub Issues: https://github.com/vedika-io/vedika-sdk-python/issues
