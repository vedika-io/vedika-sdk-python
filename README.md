# Vedika Python SDK

Requires Python 3.10 or later, Requests 2.33.0 or later within 2.x, and urllib3 2.7.0 or later within 2.x. Upgrade Python 3.8 and 3.9 before installing this release. These dependency floors include the current credential, redirect, and decompression security fixes.

Official Python SDK for the Vedika Astrology API - The **only B2B astrology API with AI-powered chatbot queries**.

[![PyPI version](https://badge.fury.io/py/vedika-sdk.svg)](https://badge.fury.io/py/vedika-sdk)
[![Python Versions](https://img.shields.io/pypi/pyversions/vedika-sdk.svg)](https://pypi.org/project/vedika-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 What Makes Vedika Unique?

Vedika is the **ONLY B2B astrology API** that offers:
- ✅ **AI-Powered Chatbot Queries** (conversational astrology questions)
- ✅ **Voice AI** (spoken answers in Indian languages and English; see `/api/v1/voice/pricing` for the current tiers and their languages)
- ✅ **Fast, Standard & Eco Delivery Tiers** (1.5-3s fast vs 12-18s comprehensive; eco is the lower-cost engine)
- ✅ **Multi-Turn Conversations** (maintain context via conversationId)
- ✅ **Traditional Vedic Coverage** (birth charts, dashas, yogas, doshas, compatibility)
- ✅ **Multi-Language Answers** (14 Indian languages plus English, and major world languages)

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
client = VedikaClient(api_key="vk_live_...")

# Ask a conversational astrology question (UNIQUE to Vedika!)
response = client.ask_question(
    question="What are my career prospects for this year?",
    birth_details={
        "datetime": "1990-06-15T14:30:00+05:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "+05:30"
    },
    language="en",  # 29 languages; see the language list below
    speed="standard"  # 'fast' (1.5-3s), 'standard' (12-18s, default), or 'eco' (lower cost)
)

print(response.answer)
print(f"Conversation ID: {response.conversation_id}")  # Use for multi-turn
# confidence/credits_used are legacy fields the live engine may not populate;
# response.raw has the full server payload (metadata.cost, metadata.wallet, ...)
print(f"Full metadata: {response.raw.get('metadata')}")

# Continue conversation — re-send the SAME birth_details you used originally;
# the server does not echo them back on the response.
follow_up = client.ask_question(
    question="Tell me about my marriage prospects",
    birth_details=birth_info,
    conversation_id=response.conversation_id  # Maintains context
)
```

### Output Example

```
Answer: Based on your birth chart analysis, this year shows strong career potential...
[Detailed astrological insights across the relevant chart factors]

Conversation ID: conv_8f3a21
Full metadata: {'model': 'Vedika AI', 'processing_time_ms': 18420, 'cost': {'costUsd': 0.0142, 'currency': 'USD'}, ...}
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

### 🏠 Vastu Shastra (98 operation paths)

Vastu takes a building: a plot polygon, room list, and compass zone. All 98 operation paths use `/v2/astrology/vastu/`. Python returns the full API envelope; read its `data` field for the result.

```python
from vedika.client import VastuOperation

rooms = [
    {"name": "Kitchen", "roomType": "kitchen", "zone": "SE"},
    {"name": "Pooja", "roomType": "pooja", "zone": "NE"},
]
score = client.vastu_operation(VastuOperation.SCORE_OVERALL, {"rooms": rooms})
print(score["data"]["score"], score["data"]["scoring"]["version"])

# Retain this ID with this exact batch before sending. Reuse it after a
# lost response or client restart; use a new ID for a different batch.
batch_key = "property-import-001"
batch = client.vastu_operation(
    VastuOperation.ASSESSMENTS_BATCH,
    {"items": [{"id": "property-1", "assessment": {
        "inputSource": "plan-derived",
        "rooms": [{"roomType": "kitchen", "zone": "SE"}],
    }}]},
    idempotency_key=batch_key,
)
for item in batch["data"]["results"]:
    print(item["id"], item["status"], item["response"])

plan = client.vastu_operation(VastuOperation.PLAN_FROM_REQUIREMENTS, {
    "plot": {"width": 40, "length": 60, "facing": "east"},
    "requirements": {
        "bedrooms": 2, "toilets": 2, "floors": 1,
        "hasKitchen": True, "hasLiving": True, "hasDining": True, "hasPooja": True,
        "hasStudy": True, "hasGuest": False, "hasStore": False, "hasStaircase": False,
    },
    "includeSvg": False,
})
print(plan["data"]["rooms"])  # Geometry remains; SVG drawings are omitted.

report = client.vastu_operation(VastuOperation.PLAN_REPORT, {
    "rooms": [{"name": "Kitchen", "zone": "SE"}, {"name": "Pooja", "zone": "NE"}],
    "format": "html",
    "brand": {"reportTitle": "Property Vastu Report", "generatedFor": "Buyer"},
})
artifact = report["data"]["artifact"]
print(artifact["filename"], artifact["content"])
```

Large jobs and report questions:

```python
# Queue 1-1,000 assessments. The key is mandatory: store it with this exact
# body and reuse it after a lost response to get the original job back
# (data["replayed"] is True) instead of paying twice. Each item is charged
# after it succeeds.
submitted = client.vastu_job_submit(
    {"operation": "assessments", "items": [{"id": "p1", "input": {"inputSource": "plan-derived", "rooms": rooms}}]},
    idempotency_key="import-2026-10-01",
)
job_id = submitted["data"]["jobId"]
print(client.vastu_job_status(job_id)["data"]["counts"])
for item in client.vastu_job_result_items(job_id):  # follows nextCursor
    print(item["id"], item["status"])
client.vastu_job_cancel(job_id)  # stops the items that have not run

# Ask about a report PDF. The upload is paid; its key names this one file.
upload = client.upload_vastu_report(pdf_bytes, idempotency_key="plan-upload-001", filename="plan.pdf")
answer = client.ask_vastu_report(
    "What should I fix first?",
    report_ref={"type": "upload", "id": upload["uploadId"]},
)
```

The named helpers (`vastu_listing_assessment`, `vastu_score`, `vastu_audit`, `vastu_room`, `vastu_placement` and the rest) take `idempotency_key=`. Pass a key you saved when a retry may come from a new call.

A batch contains 1–20 properties. Missing or blank caller keys fail before network. Each item uses the existing assessment price; there is no batch fee. Inspect every item status even when the batch succeeds. The HTML artifact opens offline and can be printed to PDF. Scores are versioned conventions; compare the same version and equivalent room coverage. Detailed audits report missing input and do not certify physical survey completeness.

## 🌍 Multi-Language Support

Vedika answers in 29 languages:

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
- 🇮🇳 South Asian: Hindi (`hi`), Bengali (`bn`), Tamil (`ta`), Telugu (`te`), Marathi (`mr`),
  Gujarati (`gu`), Kannada (`kn`), Malayalam (`ml`), Punjabi (`pa`), Odia (`od`), Assamese (`as`),
  Urdu (`ur`), Nepali (`ne`), Sinhala (`si`)
- 🌍 Other: English (`en`), Spanish (`es`), French (`fr`), German (`de`), Italian (`it`),
  Portuguese (`pt`), Russian (`ru`), Arabic (`ar`), Persian (`fa`), Chinese (`zh`),
  Japanese (`ja`), Korean (`ko`), Vietnamese (`vi`), Indonesian (`id`), Malay (`ms`)

Pass one of the codes above. An unrecognised code is not rejected, and the language of the
answer is then not guaranteed, so validate the code on your side.
Voice answers cover a smaller set than text; read `/api/v1/voice/pricing` for the current
per-tier voice languages.

## 🎨 Advanced Features

### Voice AI

`ask_voice()` uploads recorded audio and returns a `VoiceResponse`. Supply the
voice tier identifier from the current API catalog. Check current availability,
languages, access and pricing before calling it.

```python
import os

with open("question.wav", "rb") as audio:
    voice = client.ask_voice(
        audio=audio,
        birth_details=birth_info,
        tier=os.environ["VEDIKA_VOICE_TIER"],
        language="hi",
    )

if voice.audio is not None:
    with open("answer.mp3", "wb") as output:
        output.write(voice.audio)
else:
    print(voice.response_text)
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

# Events: 'started', 'progress', 'stage_completed', 'data_sources', 'billing_completed', 'billing_error', 'completed', 'error'
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
- **Examples:** https://github.com/vedika-io/vedika-sdk-python/tree/main/examples (not shipped in `pip install` — see the Examples section below)
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
export VEDIKA_API_KEY="vk_live_..."
export VEDIKA_API_URL="https://api.vedika.io"  # Optional
```

### Client Options

```python
client = VedikaClient(
    api_key="vk_live_...",
    timeout=60,  # Request timeout in seconds
    max_retries=3,  # Retries for 429 rate limits and for calls that are safe to resend
    max_retry_wait=60,  # Longest pause between retries, in seconds
    cache_enabled=True,  # Enable prompt caching for cost savings
    language="en",  # Default language for responses
    allow_insecure_http=False  # Legacy option; cannot enable custom origins or remote HTTP
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

`examples/` is **not included in a `pip install`** (only the `vedika` package
is — `examples/` has no `__init__.py` and isn't declared as `package_data`) —
clone the repo or browse it on GitHub to run these:
https://github.com/vedika-io/vedika-sdk-python/tree/main/examples

- `basic_chatbot.py` - Simple conversational astrology bot
- `birth_chart_analysis.py` - Complete birth chart generation
- `compatibility_checker.py` - Marriage compatibility analysis
- `dosha_detector.py` - Comprehensive dosha analysis
- `streaming_example.py` - Real-time streaming responses
- `vastu_audit.py` - Vastu mandala projection, room placement, audit and scoring

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

### Development Setup

```bash
# Clone repository
git clone https://github.com/vedika-io/vedika-sdk-python.git
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
- `vk_live_` for production
- `vk_ent_` for enterprise accounts

Keys that start with `vk_test_` are rejected. To test without a key, use the free sandbox at `https://api.vedika.io/sandbox/...`. From the SDK, reach it with `client.request("POST", "/sandbox/v2/astrology/kundli", json={...})`; the client's `base_url` stays the bare production origin.

### "Insufficient Credits"

Add credits to your account: https://vedika.io/dashboard.html

A 402 is never retried. The exception carries the wallet figures from the response, in USD:

```python
from vedika import InsufficientCreditsError

try:
    client.ask_question(question="...", birth_details={...})
except InsufficientCreditsError as e:
    print(e.required, e.available, e.deficit, e.purchase_url)
```

### "Request Timeout"

For complex queries, increase timeout:

```python
client = VedikaClient(api_key="...", timeout=120)  # 2 minutes
```

### "Rate Limit Exceeded"

The client reads the response `code`, not the `x-ratelimit-*` headers. A per-minute limit (`RATE_LIMIT_EXCEEDED`) is retried after the `retryAfter` the API gives, up to `max_retries`; a wait longer than `max_retry_wait` is raised instead of slept on. A daily allowance that is used up (`DAILY_LIMIT_EXCEEDED`) is never retried and raises `DailyLimitError`, a subclass of `RateLimitError`:

```python
from vedika import DailyLimitError, RateLimitError

try:
    client.get_usage()
except DailyLimitError:
    ...  # allowance used up: upgrade your plan or wait for the reset
except RateLimitError as e:
    print(e.code, e.retry_after)
```

### Retries and idempotency

A call is resent after a 5xx or a timeout only when that cannot charge you twice: GET and DELETE calls, and calls that carry an idempotency key. The client generates a key by itself only for the operations the API documents as accepting one (for example `ask_question` and the property, archive, quote and job Vastu operations); it never sends one elsewhere, because the API refuses a key on the other billed routes. To make any other call safe to repeat yourself, pass `idempotency_key=` where a method offers it. For an operation without a named method, use the generic call:

```python
data = client.request("POST", "/v2/astrology/kundli", json={"datetime": "1990-06-15T14:30:00", "latitude": 28.6139, "longitude": 77.209, "timezone": "+05:30"})
```

## 📊 Performance

- **Average response time:** 2.14 seconds (simple queries)
- **Complex queries:** 28-36 seconds (advanced AI processing)

## 🔒 Security

- ✅ API keys encrypted in transit (HTTPS)
- ✅ **Credential-routing policy:** credentials may use only `https://api.vedika.io` on its default HTTPS port, or literal loopback HTTP (`localhost`, `127.x.x.x`, `::1`) for local development. Custom HTTPS origins and remote HTTP are rejected, even with the legacy insecure-HTTP flag. Redirects are never followed (a 3xx raises an error and no second request is sent), so keys and request bodies stay on the approved origin. Browser applications must keep the real key on their server and use their own app-session transport.

## 📜 License

MIT License - see [LICENSE](LICENSE) file

## 🌐 Links

- **Website:** https://vedika.io
- **Documentation:** https://vedika.io/docs.html
- **API Reference:** https://vedika.io/api-reference.html
- **Dashboard:** https://vedika.io/dashboard.html
- **Support:** support@vedika.io
- **GitHub:** https://github.com/vedika-io

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
| **Unique Value** | **Traditional + AI** | Traditional only |

**Bottom line:** Vedika provides everything other astrology APIs offer, **PLUS** the only conversational AI chatbot capability in the market.

---

**Built with ❤️ by Vedika Intelligence**

**The only B2B astrology API with AI-powered chatbot queries.**

Get started: https://vedika.io
