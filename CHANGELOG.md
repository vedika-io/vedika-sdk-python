# Changelog

All notable changes to the Vedika Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2026-04-17

### Added
- `response_format="json"` option on `ask_question()` — server returns a `structured_response` object with parsed sections (title, preamble, sections with paragraphs/bullets/numbered). Original markdown `answer` still present. No pricing change.
- New dataclasses: `StructuredResponse`, `StructuredResponseSection`.

## [2.2.2] - 2026-04-17

### Fixed
- **`get_birth_chart()` and `check_compatibility()` were calling 404 endpoints.** Wrong paths shipped in v2.2.0 + v2.2.1. Both methods now hit the correct `/api/v1/chart` and `/api/v1/compatibility` endpoints. **Anyone on v2.2.0 or v2.2.1 should upgrade immediately.**

### Changed
- README cleaned up — removed internal architecture descriptions and provider-name mentions for clearer enterprise positioning.

## [2.2.1] - 2026-04-16 [DEPRECATED — use 2.2.2+]

### Note
- v2.2.1 was bumped briefly during release process; functionally identical to 2.2.0.

## [2.2.0] - 2026-04-16 [DEPRECATED — use 2.2.2+]

### Added
- **Voice AI** — 3 tiers via `ask_voice()`: `vedika-standard` ($0.072/query, ~1s), `vedika-native` ($0.040, ~800ms, audio-native), `vedika-jarvis` ($0.080, <500ms streaming voice-to-voice). Business + Enterprise plans only.
- **Speed modes** — `speed='fast'` (1.5–3s, English only, ~700-word cap) or `speed='standard'` (12–18s, all 30 languages, default).
- **Multi-turn conversations** — pass back `conversation_id` from any 200 response to continue the conversation. Default 10 messages per conversation.
- **Voice rate limits documented** — Business: 30 calls/min, 2,000/day. Enterprise: 100/min, 10,000/day.

### Known Issues (fixed in 2.2.2)
- `get_birth_chart()` and `check_compatibility()` call wrong endpoint paths → 404. Fixed in 2.2.2.

## [2.1.0] - 2026-03-15

### Added
- **9 Convenience Methods** — Shorthand methods for the most common V2 operations:
  - `get_panchang_today()` — Today's Panchang with no arguments needed
  - `get_sade_sati()`, `get_chandrashtama()` — Quick dosha checks
  - `get_kundli()`, `get_navamsa()` — Common chart types
  - `get_guna_milan()` — Simplified compatibility matching
  - `get_vimshottari_dasha()` — Default dasha system
  - `get_daily_prediction()` — Daily prediction by rashi name
  - `get_shadbala()` — Planetary strength analysis

### Fixed
- **Timezone documentation** — All docstrings now correctly specify UTC offset format (`"+05:30"`) instead of IANA names (`"Asia/Kolkata"`). IANA names are NOT supported by the API
- **Example code** — `ask_question()` docstring example updated to use UTC offset timezone

---

## [2.0.0] - 2026-03-13

### Added
- **V2 Computation Endpoints** — 20+ new methods for direct access to V2 API (faster, cheaper)
  - `get_birth_chart_v2()`, `get_dasha_v2()`, `get_doshas_v2()`, `get_compatibility_v2()`
  - `get_panchang()`, `get_muhurta_v2()`, `get_divisional_chart()`
  - `get_prediction()`, `get_ashtakavarga()`, `get_varshaphal()`, `get_strength()`
  - `get_numerology_v2()` with 7 calculation types
- **Western Astrology** — 4 new methods
  - `get_western_transits()`, `get_western_progressions()`
  - `get_western_solar_return()`, `get_western_relationship()`
- **Horoscope** — `get_horoscope()` for daily/weekly/monthly, Vedic and Western
- **Conversations** — `get_conversations()`, `delete_conversation()`
- **Usage** — `get_usage()` for wallet balance
- **Enhanced AI Chat** — `ask_question()` now supports system, speed, conversationId, partner_birth_details, include_remedies, category, response_format

### Changed
- Updated User-Agent to `vedika-python-sdk/2.0.0`
- 30 language support (was 22)
- Updated pricing: Starter $12, Pro $60, Business $120, Enterprise $240

---

## [1.3.0] - 2026-01-02

### Added

#### Free Sandbox Environment
- **New sandbox endpoints** - Test all API features without an API key
- `get_sandbox_horoscope()` - Daily/weekly/monthly horoscopes (mock data)
- `get_sandbox_panchang()` - Today's panchang (mock data)
- `sandbox_chat()` - AI chat testing (mock responses)
- `get_sandbox_birth_chart()` - Birth chart generation (mock data)
- Zero cost testing for development and integration

#### New Computational Endpoints (15 new features)
- `get_sade_sati()` - Saturn 7.5 year transit analysis with phases
- `get_chandrashtama()` - Moon 8th house transit detection
- `get_ritu()` - 6 Hindu seasons calculation
- `get_solstice()` - Equinoxes and solstices
- `get_anandadi_yoga()` - Weekday + Nakshatra yoga combinations
- `get_auspicious_yoga()` - 27 yoga classifications
- `get_auspicious_period()` - Good timing recommendations
- `get_inauspicious_period()` - Bad periods to avoid
- `get_gowri_nalla_neram()` - South Indian Choghadiya
- `get_disha_shool()` - Inauspicious direction by weekday
- `get_chandra_bala()` - Moon strength analysis
- `get_tara_bala()` - Nakshatra compatibility scoring
- `get_upagraha_positions()` - Sub-planet positions (Dhuma, Vyatipata, etc.)
- `get_planet_relationships()` - Naisargika Maitri (natural friendships)

#### Enhanced Compatibility Matching
- `get_guna_milan()` - Full 36 Guna (Ashtakoota) matching
  - All 8 Kootas: Varna, Vasya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi
  - Individual scores + total + recommendation
  - Dosha detection with remedies

### Changed
- **5x faster response times** - Optimized parallel processing (12s vs 60s)
- Improved error messages with actionable suggestions
- Better rate limit handling with automatic retry

### Fixed
- Timezone handling for edge cases
- Connection pooling for high-volume usage

---

## [1.2.0] - 2025-12-26

### Added

#### GraphQL Support
- `graphql_query()` - Execute GraphQL queries against Vedika API
- Full schema introspection support
- Nested query optimization

#### Webhook Integration
- `register_webhook()` - Subscribe to real-time events
- `verify_webhook_signature()` - Validate webhook authenticity
- Supported events: `chart.generated`, `ai.response.complete`, `billing.threshold`

#### Postman Collection
- Official Postman collection published to API Network
- Pre-configured environments (Sandbox/Production)
- One-click import: https://www.postman.com/vedikaai/intelligence-platform

### Changed
- Updated base URL routing for better latency (geo-aware)
- Improved streaming response handling

---

## [1.1.0] - 2025-12-15

### Added

#### Enhanced Muhurta Features
- `get_choghadiya()` - Day/night Choghadiya periods
- `get_hora()` - Planetary hour calculations
- `get_rahu_kaal()` - Rahu Kaal timing
- `get_gulika_kaal()` - Gulika Kaal timing
- `get_yamaghanta()` - Yamaghanta periods
- `get_abhijit_muhurta()` - Most auspicious muhurta
- `get_brahma_muhurta()` - Pre-dawn auspicious time
- `get_durmuhurta()` - Inauspicious muhurta periods

#### Enhanced Dosha Analysis
- `get_mangal_dosha()` - Mars dosha with intensity levels
- `get_kaal_sarp_dosha()` - Kaal Sarp with type classification
- `get_pitru_dosha()` - Ancestral karma indicators
- `get_nadi_dosha()` - Nadi compatibility issues

### Changed
- Improved accuracy for planetary calculations (Vedika Ephemeris precision)
- Better handling of DST transitions

---

## [1.0.0] - 2025-11-08

### Added

#### Core Features
- Initial release of Vedika Python SDK
- `VedikaClient` class for interacting with Vedika Astrology API
- Support for AI-powered conversational astrology queries
- Advanced AI-powered query processing

#### API Methods
- `ask_question()` - Ask conversational astrology questions
- `ask_question_stream()` - Stream responses in real-time
- `get_birth_chart()` - Generate complete birth charts (Kundali)
- `get_dashas()` - Calculate Vimshottari Dasha periods
- `check_compatibility()` - Ashtakoota marriage compatibility matching
- `detect_yogas()` - Detect 300+ astrological yogas
- `analyze_doshas()` - Comprehensive dosha analysis
- `get_muhurtha()` - Find auspicious times for events
- `get_numerology()` - 37 numerology calculations
- `batch_process()` - Process multiple queries efficiently

#### Data Models
- `QuestionResponse` - AI chatbot response model
- `BirthChart` - Complete birth chart with planets and houses
- `DashaResponse` - Mahadasha, Antardasha, and Pratyantardasha periods
- `CompatibilityResponse` - Ashtakoota matching results
- `YogaResponse` - Detected yogas with descriptions
- `DoshaResponse` - Kaal Sarp, Mangal, Sade Sati, Pitra dosha analysis
- `MuhurthaResponse` - Auspicious timing analysis
- `NumerologyResponse` - Numerology calculation results

#### Exception Handling
- `VedikaAPIError` - Base exception for all API errors
- `AuthenticationError` - Invalid API key errors
- `RateLimitError` - Rate limit exceeded errors
- `InsufficientCreditsError` - Insufficient credits errors
- `ValidationError` - Input validation errors
- `TimeoutError` - Request timeout errors
- `ServerError` - Internal server errors
- `NetworkError` - Network connectivity errors

#### Features
- Automatic retry logic with exponential backoff
- Request timeout configuration
- HTTPS-only communication
- Environment variable support for API keys
- 22 language support (including 11 Indian languages)
- Prompt caching for cost savings on repeated queries

#### Documentation
- Comprehensive README with examples
- Detailed API reference documentation
- Google-style docstrings for all public APIs
- Security best practices guide
- Contributing guidelines

#### Development Tools
- Python 3.8+ support
- Type hints for all function signatures
- Black code formatting
- flake8 linting
- mypy type checking
- pytest testing framework

---

## Version History

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **Major version** (1.x.x): Breaking changes
- **Minor version** (x.1.x): New features, backward compatible
- **Patch version** (x.x.1): Bug fixes, backward compatible

### Support Policy

- **Latest major version**: Full support, security updates, bug fixes, new features
- **Previous major version**: Security updates and critical bug fixes for 6 months
- **Older versions**: No support

---

For the complete version history, see: https://github.com/vedika-io/vedika-sdk-python/releases

[2.1.0]: https://github.com/vedika-io/vedika-sdk-python/releases/tag/v2.1.0
[2.0.0]: https://github.com/vedika-io/vedika-sdk-python/releases/tag/v2.0.0
[1.3.0]: https://github.com/vedika-io/vedika-sdk-python/releases/tag/v1.3.0
[1.2.0]: https://github.com/vedika-io/vedika-sdk-python/releases/tag/v1.2.0
[1.1.0]: https://github.com/vedika-io/vedika-sdk-python/releases/tag/v1.1.0
[1.0.0]: https://github.com/vedika-io/vedika-sdk-python/releases/tag/v1.0.0
