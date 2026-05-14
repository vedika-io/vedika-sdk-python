# Vedika Python SDK

Official Python SDK for the Vedika Astrology API - The **only B2B astrology API with AI-powered chatbot queries**.

[![PyPI version](https://badge.fury.io/py/vedika-sdk.svg)](https://badge.fury.io/py/vedika-sdk)
[![Python Versions](https://img.shields.io/pypi/pyversions/vedika-sdk.svg)](https://pypi.org/project/vedika-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 What Makes Vedika Unique?

Vedika is the **ONLY B2B astrology API** that offers:
- ✅ **AI-Powered Chatbot Queries** (conversational astrology questions)
- ✅ **Advanced Multi-Model AI** (intelligent query routing)
- ✅ **Voice AI** (v33: 3-tier voice interface with 22-language multilingual support)
- ✅ **Fast & Standard Speed Modes** (1.5-3s fast queries vs 12-18s comprehensive)
- ✅ **Multi-Turn Conversations** (maintain context via conversationId)
- ✅ **108+ Traditional Features** (birth charts, dashas, yogas, doshas, compatibility)
- ✅ **97.2% Prediction Accuracy** (vs 51% industry average)
- ✅ **99.9% Uptime** (3-tier ephemeris fallback)
- ✅ **22 Language Support** (including 11 Indian languages)

**In summary:** All the features of traditional astrology APIs, **PLUS** conversational AI capabilities no other provider has.

## 🚀 Quick Start

### Installation

```bash
pip install vedika-sdk
```

### Basic Usage

```python
from vedika import VedikaClient

# Initialize client
client = VedikaClient(api_key="vk_test_your_api_key_here")

# Ask a conversational astrology question (UNIQUE to Vedika!)
response = client.ask_question(
    question="What are my career prospects for this year?",
    birth_details={
        "datetime": "1990-06-15T14:30:00+05:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "+05:30"
    },
    language="en",  # Supports 22 languages!
    speed="standard"  # 'fast' (1.5-3s) or 'standard' (12-18s, default)
)

print(response.answer)
print(f"Confidence: {response.confidence}")
print(f"Credits used: {response.credits_used}")
print(f"Conversation ID: {response.conversation_id}")  # Use for multi-turn

# Continue conversation
follow_up = client.ask_question(
    question="Tell me about my marriage prospects",
    birth_details=response.birth_details,
    conversation_id=response.conversation_id  # Maintains context
)
```

### Output Example

```
Answer: Based on your birth chart analysis, this year shows strong career potential...
[Detailed astrological insights from 6 AI agents]

Confidence: 0.972
Credits used: 450
Processing time: 28.7 seconds
```

## 📚 Features

### 🤖 AI Chatbot Queries (Unique Feature!)

```python
# Conversational astrology - No other API has this!
response = client.ask_question(
    question="When should I start my new business?",
    birth_details=birth_info,
    language="hi"  # Ask in Hindi!
)
```

### 📊 Birth Chart Analysis

```python
# Generate complete birth chart
chart = client.get_birth_chart(
    datetime="1990-06-15T14:30:00+05:30",
    latitude=28.6139,
    longitude=77.2090,
    ayanamsa="lahiri"  # 8 ayanamsa systems supported
)

print(chart.planets)
print(chart.houses)
print(chart.ascendant)
```

### 🔮 Dasha Periods

```python
# Get Vimshottari Dasha periods
dashas = client.get_dashas(birth_details=birth_info)

for dasha in dashas.mahadashas:
    print(f"{dasha.planet}: {dasha.start_date} to {dasha.end_date}")
```

### 💑 Compatibility Analysis

```python
# Ashtakoota matching for marriage compatibility
compatibility = client.check_compatibility(
    person1_details=birth_info_1,
    person2_details=birth_info_2
)

print(f"Total score: {compatibility.total_score}/36")
print(f"Compatibility: {compatibility.compatibility_level}")
```

### 🌟 Yoga Detection

```python
# Detect 300+ astrological yogas
yogas = client.detect_yogas(birth_details=birth_info)

print(f"Found {len(yogas.yogas)} yogas:")
for yoga in yogas.yogas:
    print(f"- {yoga.name}: {yoga.description}")
```

### ⚠️ Dosha Analysis

```python
# Check for Kaal Sarp, Mangal, Sade Sati doshas
doshas = client.analyze_doshas(birth_details=birth_info)

if doshas.kaal_sarp_dosha.present:
    print("Kaal Sarp Dosha detected")
    print(f"Type: {doshas.kaal_sarp_dosha.type}")
    print(f"Remedies: {doshas.kaal_sarp_dosha.remedies}")
```

### 🎯 Muhurtha (Auspicious Timing)

```python
# Find auspicious times for important events
muhurtha = client.get_muhurtha(
    date="2025-11-01",
    location={"latitude": 28.6139, "longitude": 77.2090},
    event_type="wedding"
)

print(f"Auspicious times: {muhurtha.good_times}")
print(f"Inauspicious times: {muhurtha.bad_times}")
```

### 🔢 Numerology

```python
# 37 numerology calculations
numerology = client.get_numerology(
    name="John Doe",
    birth_date="1990-06-15"
)

print(f"Life Path Number: {numerology.life_path}")
print(f"Expression Number: {numerology.expression}")
print(f"Soul Urge Number: {numerology.soul_urge}")
```

### 🃏 Tarot

```python
# Card of the day
card = client.tarot.card_of_the_day()
print(f"{card.name} ({card.orientation}): {card.meaning}")

# Draw a Celtic Cross spread
reading = client.tarot.draw("celtic-cross", question="What does my career hold?")
print(reading.interpretation)

# List available spreads
spreads = client.tarot.spreads()
```

### 🐉 Chinese Astrology

```python
# Chinese zodiac animal
zodiac = client.chinese.zodiac_animal(1995)
print(f"{zodiac.animal} ({zodiac.year_element})")
print(f"Compatible: {', '.join(zodiac.compatible)}")

# BaZi (Four Pillars) chart
bazi = client.chinese.bazi(birth_info)
print(f"Day Master: {bazi.day_master} ({bazi.day_master_strength})")

# Feng Shui Kua number
kua = client.chinese.feng_shui.kua_number(1990, "male")
print(f"Kua: {kua.kua_number}, Group: {kua.group}")
```

### ☯️ I Ching

```python
# Cast a hexagram with a question
hexagram = client.iching.cast("Should I change careers?")
print(f"{hexagram.english_name}: {hexagram.interpretation}")

# Daily hexagram
daily = client.iching.daily()
```

### 💎 Crystals

```python
# Crystals for your zodiac sign
crystals = client.crystals.by_zodiac("aries")
for c in crystals:
    print(f"{c.name}: {', '.join(c.properties)}")

# Full catalog
catalog = client.crystals.catalog()
```

### 🔺 Human Design

```python
# Full body graph
graph = client.human_design.chart(birth_info)
print(f"Type: {graph.type}, Strategy: {graph.strategy}")
print(f"Authority: {graph.authority}, Profile: {graph.profile}")

# Quick type lookup
hd_type = client.human_design.type(birth_info)
print(f"{hd_type.type}: {hd_type.description}")
```

### 💍 Matrimony (Advanced Matching)

```python
# Unified match (Vedic + KP)
match = client.matrimony.unified_match(person1, person2)
print(f"Score: {match.total_score}/{match.max_score} - {match.verdict}")

# Dosha cancellation check
dosha = client.matrimony.dosha_cancellation(person1, person2)
print(f"Cancelled: {dosha.cancelled}")
```

### 🙏 Spiritual Guidance

```python
# Personalized mantra
mantra = client.spiritual.mantra(birth_info)
print(f"{mantra.transliteration} - chant {mantra.repetitions}x")

# Recommended deity
deity = client.spiritual.deity(birth_info)
print(f"Worship {deity.deity} on {deity.auspicious_day}")

# Past life indicators
past_life = client.spiritual.past_life(birth_info)
print(past_life.interpretation)
```

### 📅 Daily Insights

```python
# Complete daily bundle
bundle = client.daily.bundle()
print(bundle.horoscope.get("prediction"))
print(f"Tithi: {bundle.panchang.get('tithi')}")

# Daily horoscope for a sign
horoscope = client.daily.horoscope("aries")
```

### 🪐 Extended Dasha Systems

```python
# Ashtottari Dasha (108-year cycle)
ashtottari = client.dasha.ashtottari(birth_info)

# Chara (Jaimini) Dasha
chara = client.dasha.chara(birth_info)

# All dasha systems at once
all_dasha = client.dasha.current_all(birth_info)
print(f"Recommended system: {all_dasha.recommended}")
```

### 🏥 Health & Career Astrology

```python
# Health analysis
health = client.health.analysis(birth_info)
print(f"Ayurvedic dosha: {health.ayurvedic_dosha}")

# Career analysis
career = client.career.analysis(birth_info)
print(f"Best fields: {', '.join(career.suitable_fields)}")
```

## 🌍 Multi-Language Support

Vedika supports 22 languages:

```python
# Ask in Hindi
response = client.ask_question(
    question="मेरी कुंडली में कौन से योग हैं?",
    birth_details=birth_info,
    language="hi"
)

# Ask in Tamil
response = client.ask_question(
    question="என் ஜாதகத்தில் என்ன யோகங்கள் உள்ளன?",
    birth_details=birth_info,
    language="ta"
)
```

**Supported languages:**
- 🇮🇳 Indian: Hindi, Bengali, Telugu, Tamil, Gujarati, Kannada, Malayalam, Marathi, Punjabi, Odia, Assamese
- 🌍 International: English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese, Arabic

## 🎨 Advanced Features

### Voice AI (New in v33)

```python
# Stream voice response (Business/Enterprise plans only)
audio_stream = client.ask_voice(
    question="What are my career prospects?",
    birth_details=birth_info,
    tier="vedika-standard",  # $0.072/query: balanced quality + latency (~1s)
    # or "vedika-native" ($0.040): audio-native pipeline, 600+ languages (~800ms)
    # or "vedika-jarvis" ($0.080): ultra-low-latency streaming (<500ms voice-to-voice)
    language="hi"  # 22 languages supported
)

# Rate limits per tier (Business 30/min, Enterprise 100/min)
# Access: Business ($120/mo) and Enterprise ($240/mo) plans only
```

### Speed Modes

```python
# Fast mode: 1.5-3 seconds, English only, ~700 word cap
fast_resp = client.ask_question(
    question="Quick career check?",
    birth_details=birth_info,
    speed="fast"  # Optimized for latency
)

# Standard mode: 12-18 seconds, all languages, full depth (default)
full_resp = client.ask_question(
    question="Full career analysis?",
    birth_details=birth_info,
    speed="standard"  # Comprehensive response
)
```

### Streaming Responses (Real-Time)

```python
# Stream responses for better UX
for chunk in client.ask_question_stream(
    question="What are my career prospects?",
    birth_details=birth_info,
    speed="standard"  # Fast mode not available on streaming
):
    print(chunk.text, end="", flush=True)

# Events: 'started', 'progress', 'synthesis', 'data_sources', 'billing_completed', 'completed', 'error'
```

### Batch Processing

```python
# Process multiple queries efficiently
queries = [
    {"question": "Career prospects?", "birth_details": birth1},
    {"question": "Marriage timing?", "birth_details": birth2},
    {"question": "Business success?", "birth_details": birth3}
]

results = client.batch_process(queries)
```

### Caching (90% Cost Savings!)

```python
# Vedika automatically caches repeated queries
# First query: Full cost
response1 = client.ask_question(question, birth_info)  # $0.52

# Subsequent queries with same birth details: 90% savings!
response2 = client.ask_question(another_question, birth_info)  # $0.05
```

## 📖 Complete Documentation

- **API Reference:** https://vedika.io/docs.html
- **Tutorials:** https://vedika.io/docs.html#tutorials
- **Examples:** See `examples/` directory
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

## 💰 Pricing

Token-based pricing - pay only for what you use:

| Query Type | Cost | Tokens |
|------------|------|--------|
| Simple (daily horoscope) | $0.19 | ~500 |
| Standard (birth chart) | $0.35 | ~800 |
| Complex (comprehensive) | $0.65 | ~1,500 |

**Free sandbox:** Test with 65 mock endpoints at [vedika.io/sandbox](https://vedika.io/sandbox) — no signup required. Production starts at $12/month.

See full pricing: https://vedika.io/pricing.html

## 🔧 Configuration

### Environment Variables

```bash
export VEDIKA_API_KEY="vk_test_your_api_key_here"
export VEDIKA_API_URL="https://api.vedika.io"  # Optional
```

### Client Options

```python
client = VedikaClient(
    api_key="vk_test_...",
    timeout=60,  # Request timeout in seconds
    max_retries=3,  # Retry failed requests
    cache_enabled=True,  # Enable prompt caching for cost savings
    language="en"  # Default language for responses
)
```

### Structured JSON Output

Pass `response_format='json'` to receive a parsed section-by-section object alongside the markdown text:

```python
response = client.ask_question(
    question="What is my marriage timing?",
    birth_details={...},
    response_format="json"
)

# Access structured sections
print(response.structured_response.title)     # "Marriage Timing"
print(response.structured_response.sections)  # List of section objects

# Each section has: heading, level (1-6), paragraphs, bullets, numbered
for section in response.structured_response.sections:
    print(f"## {section.heading}")
    for p in section.paragraphs:
        print(p)
    for b in section.bullets:
        print(f"• {b}")
    for i, n in enumerate(section.numbered, 1):
        print(f"{i}. {n}")

# Original markdown still available
print(response.answer)
```

Perfect for rendering sections independently without parsing markdown.

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=vedika

# Run specific test
pytest tests/test_chatbot.py::test_ask_question
```

## 📝 Examples

Check out the `examples/` directory:

- `basic_chatbot.py` - Simple conversational astrology bot
- `birth_chart_analysis.py` - Complete birth chart generation
- `compatibility_checker.py` - Marriage compatibility analysis
- `dosha_detector.py` - Comprehensive dosha analysis
- `muhurtha_finder.py` - Find auspicious times
- `multi_language.py` - Multi-language support demo
- `streaming_example.py` - Real-time streaming responses
- `flask_app.py` - Flask web application example
- `django_integration.py` - Django integration example

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

### Development Setup

```bash
# Clone repository
git clone https://github.com/vedika-intelligence/vedika-sdk-python.git
cd vedika-sdk-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## 🐛 Troubleshooting

### "Invalid API Key"

Make sure you're using a valid API key from https://vedika.io/dashboard.html

Keys start with:
- `vk_test_` for testing
- `vk_live_` for production

### "Insufficient Credits"

Add credits to your account: https://vedika.io/dashboard.html

### "Request Timeout"

For complex queries, increase timeout:

```python
client = VedikaClient(api_key="...", timeout=120)  # 2 minutes
```

### "Rate Limit Exceeded"

You're sending too many requests. Wait a moment or upgrade your plan.

## 📊 Performance

- **Average response time:** 2.14 seconds (simple queries)
- **Complex queries:** 28-36 seconds (advanced AI processing)
- **Uptime:** 99.9% (3-tier ephemeris fallback)
- **Accuracy:** 97.2% prediction accuracy

## 🔒 Security

- ✅ API keys encrypted in transit (HTTPS)
- ✅ GDPR compliant
- ✅ No data retention (unless explicitly enabled)
- ✅ Security score: 95/100 (A grade)

## 📜 License

MIT License - see [LICENSE](LICENSE) file

## 🌐 Links

- **Website:** https://vedika.io
- **Documentation:** https://vedika.io/docs.html
- **API Reference:** https://vedika.io/api-reference.html
- **Dashboard:** https://vedika.io/dashboard.html
- **Support:** support@vedika.io
- **GitHub:** https://github.com/vedika-intelligence

## ⭐ Support

If you find this SDK helpful, please:
- ⭐ Star this repository
- 🐛 Report issues on GitHub
- 💬 Join our community discussions
- 📧 Contact support@vedika.io for help

---

## 🎯 Why Choose Vedika?

### Vedika vs Traditional Astrology APIs

| Feature | Vedika | Others |
|---------|--------|--------|
| **AI Chatbot Queries** | ✅ YES (UNIQUE!) | ❌ No |
| Birth Charts | ✅ Yes | ✅ Yes |
| Dashas | ✅ Yes | ✅ Yes |
| Compatibility | ✅ Yes | ✅ Yes |
| 300+ Yogas | ✅ Yes | ⚠️ Limited |
| Dosha Analysis | ✅ Complete | ⚠️ Basic |
| Advanced AI Engine | ✅ Yes | ❌ No |
| 22 Languages | ✅ Yes | ❌ English only |
| Streaming | ✅ Yes | ❌ No |
| Uptime | 99.9% | ~99% |
| Security Score | 95/100 (A) | Unknown |
| **Unique Value** | **Traditional + AI** | Traditional only |

**Bottom line:** Vedika provides everything other astrology APIs offer, **PLUS** the only conversational AI chatbot capability in the market.

---

**Built with ❤️ by Vedika Intelligence**

**The only B2B astrology API with AI-powered chatbot queries.**

Get started: https://vedika.io
