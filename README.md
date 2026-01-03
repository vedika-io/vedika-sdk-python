# vedika-sdk

[![PyPI version](https://img.shields.io/pypi/v/vedika-sdk.svg)](https://pypi.org/project/vedika-sdk/)
[![PyPI downloads](https://img.shields.io/pypi/dm/vedika-sdk.svg)](https://pypi.org/project/vedika-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/vedika-sdk.svg)](https://pypi.org/project/vedika-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The only B2B astrology API with AI-powered chatbot queries** - Official Python SDK

## Installation

```bash
pip install vedika-sdk
```

## Quick Start

```python
from vedika import VedikaClient

client = VedikaClient(api_key='vk_live_your_api_key')

# Ask an astrology question (AI-powered)
response = client.ask_question(
    question='What are my career prospects this year?',
    birth_details={
        'datetime': '1990-06-15T14:30:00+05:30',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'timezone': 'Asia/Kolkata'
    }
)

print(response['answer'])
```

## Features

- **AI Chat** - Natural language astrology queries (unique to Vedika!)
- **Birth Charts** - Complete Kundali generation
- **Compatibility** - 36 Guna (Ashtakoota) matching
- **Dasha Periods** - Vimshottari Dasha calculations
- **Doshas** - Mangal, Kaal Sarp, Sade Sati analysis
- **Muhurtha** - Auspicious timing finder
- **Numerology** - 37+ calculations
- **22 Languages** - Multilingual responses

## API Methods

| Method | Description |
|--------|-------------|
| `ask_question()` | AI-powered astrology chat |
| `ask_question_stream()` | Streaming responses |
| `get_birth_chart()` | Generate birth chart |
| `get_dashas()` | Vimshottari Dasha periods |
| `check_compatibility()` | Marriage compatibility |
| `detect_yogas()` | 300+ yoga detection |
| `analyze_doshas()` | Dosha analysis |
| `get_muhurtha()` | Auspicious timing |
| `get_numerology()` | Numerology analysis |

## CLI Tool (Node.js)

```bash
# Initialize a new project
npx @vedika-io/cli init --python

# Test your API connection
npx @vedika-io/cli test --key YOUR_API_KEY
```

## Documentation

- **API Docs**: https://vedika.io/docs.html
- **Quickstart**: https://vedika.io/quickstart.html
- **API Explorer**: https://vedika.io/api-explorer.html

## Get API Key

1. Sign up at https://vedika.io
2. Go to Dashboard
3. Create API key

**Free Sandbox** available for testing: `https://api.vedika.io/sandbox/*`

## Support

- Email: support@vedika.io
- Docs: https://vedika.io/docs.html

## License

MIT
