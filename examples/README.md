# Vedika Python SDK Examples

This directory contains example scripts demonstrating how to use the Vedika Python SDK.

## Setup

1. Install the SDK:
```bash
pip install vedika-sdk
```

2. Set your API key:
```bash
export VEDIKA_API_KEY="vk_test_your_api_key_here"
```

Or create a `.env` file:
```
VEDIKA_API_KEY=vk_test_your_api_key_here
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

- **`multi_language.py`** - Multi-language support
  - Ask questions in 14 Indian languages plus English
  - Get responses in Hindi, Tamil, etc.
  - Best for: Multilingual applications

### Web Framework Examples

- **`flask_app.py`** - Flask web application
  - Complete web app with REST API
  - Production-ready example
  - Best for: Web applications

- **`django_integration.py`** - Django integration
  - Django view and model integration
  - Async support
  - Best for: Django projects

## Running Examples

```bash
# Basic chatbot
python examples/basic_chatbot.py

# Birth chart analysis
python examples/birth_chart_analysis.py

# Flask web app
python examples/flask_app.py
```

## Get Your API Key

Sign up for free at https://vedika.io/dashboard.html to get your API key.

## Need Help?

- Documentation: https://vedika.io/docs.html
- Support: support@vedika.io
- GitHub Issues: https://github.com/vedika-io/vedika-sdk-python/issues
