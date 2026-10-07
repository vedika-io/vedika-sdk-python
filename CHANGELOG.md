# Changelog

## [3.1.1] - 2026-10-06

### Fixed
- The client no longer attaches an `Idempotency-Key` to every POST. The live API accepts a key only on the operations that list one, and answers `422 IDEMPOTENCY_NOT_SUPPORTED` to a key on any other billed route (and treats a caller-sent `X-Request-Id` as a key). A key is now generated only for those operations (with the header each one documents, `X-Idempotency-Key` for `/api/v1/astrology/query`), or sent unchanged when you pass `idempotency_key=`. If you pass a key to an operation that does not support one, the call is resent once without it. The voice call no longer sends a key either.
- A POST without a key is no longer resent after a 5xx or a timeout, because the first attempt may already have been charged. Calls that carry a key, and GET and DELETE calls, are still retried with exponential backoff.
- 402 raises `InsufficientCreditsError` with `required`, `available`, `deficit` (USD) and `purchase_url` read from the response, and is never retried. Previously the 402 body was reduced to a message.
- 429 is read by its body `code`. `DAILY_LIMIT_EXCEEDED` (and `PLAN_LIMIT_EXCEEDED`) raise the new `DailyLimitError` (a `RateLimitError`) and are never retried. `RATE_LIMIT_EXCEEDED` waits the body `retryAfter` (or `Retry-After`), and any 429 asking for more than `max_retry_wait` (default 60 seconds, new constructor argument) is raised at once instead of slept on. The `x-ratelimit-*` headers are not used. Before, urllib3 retried every 429, slept on an uncapped `Retry-After`, and after the last attempt turned the 429 and 402 responses into a generic "Request failed" error.
- Every exception now carries the API's `code`, and `RateLimitError` carries `retry_after`. The streaming and voice calls raise the same typed errors as the other calls.
- A retried multipart upload sends byte-identical bytes, so the same `Idempotency-Key` is never paired with a different multipart boundary.
- `get_divisional_chart("hora")` and `"D2"` called `/v2/astrology/hora-chart`, which the API does not serve. They now use `/v2/astrology/divisional-chart` with the division number in the body, and accept `"D9"`, `9` and the other supported divisions the same way.
- The API key is sent once, as `Authorization: Bearer`, instead of also in `X-API-Key`.

### Added
- `VedikaClient.request(method, path, json=, params=, idempotency_key=)` calls any API operation with the client's auth, retry and error handling. It accepts only a path on the API origin, never a full URL.
- Remediation, merchant catalog, portfolio, plan compare-versions, receipt verification and rule-version Vastu operations that are in this release's operation inventory. Some of these are not on the live API yet and answer 404 until it serves them.

## [3.1.0] - 2026-10-01

### Added
- Async Vastu jobs: `vastu_job_submit`, `vastu_job_status`, `vastu_job_results` (cursor pagination), `vastu_job_result_items` and `vastu_job_cancel`, with request and response types. Submit requires a caller-retained `idempotency_key`; status and results are GET, cancel is POST. The generic `vastu()` now sends GET for `jobs/{id}` and `jobs/{id}/results`. The operation inventory is 98 logical paths.
- `upload_vastu_report` sends a report PDF to `POST /api/v1/vastu/chat/uploads` as multipart under a required caller-retained key, and `ask_vastu_report` accepts `report_ref={"type": "upload", "id": ...}` alone.
- The named Vastu helpers (`vastu_listing_assessment`, `vastu_score`, `vastu_audit`, `vastu_room`, `vastu_placement`, `vastu_mandala_project`, `vastu_entrance_pada`, `vastu_entrance_recommend`, `vastu_ar_scan_quality`, `vastu_ar_true_north_calibrate`, `vastu_plan_generate`, `vastu_plan_from_requirements`, `vastu_declination`) accept `idempotency_key=`, so a new call after a lost response can reuse the key and never pays twice.

- Vastu `ar/attestation/challenge` operation and the optional `deviceAttestation` request field on `ar/room-capture`, `ar/scan-quality` and `scans/save`, with the `deviceAttestation` status now returned by those operations. The API reports `not_configured` until device attestation is enabled for a platform.

### Fixed
- Redirects are no longer followed. A 307 or 308 used to resend the private request body and the retained `Idempotency-Key` to the redirect target (only the auth headers were stripped). Every request path (ordinary, streaming and voice) now refuses any 3xx with `VedikaAPIError` and sends no second request, matching the Android and Swift SDKs.


## [3.0.11] - 2026-09-24

### Fixed
- Vastu scan calls (`scans/save`, `scans/retrieve`, `scans/list`, `scans/delete`, `scans/timelapse`) no longer send a retry header. The API identifies a scan retry by `scanId` or the body's `requestId` and rejected every scan call that carried an `Idempotency-Key` with `422 IDEMPOTENCY_CONTRACT_UNSUPPORTED`. Passing an idempotency key to a scan call now raises a clear error before anything is sent, and scan calls are still retried on transient failures.

## [3.0.10] - 2026-09-17

- The README no longer describes how the platform is built: removed an internal routing description, an internal build number, an agent count and a pipeline stage name from the documented streaming events.
- The documented streaming event list now matches what the API emits: `started`, `progress`, `stage_completed`, `data_sources`, `billing_completed`, `billing_error`, `completed`, `error`. The previously listed `synthesis` event is not emitted.
- The language section listed 22 languages and omitted six the API serves. It now lists all 29 with their codes. An unrecognised code is not rejected, so the README says to validate it client-side.
- Replaced a stale feature count in the feature list.

## [3.0.9] - 2026-09-17

- Vastu mandala responses changed in the API on 2026-09-17: heatmap and 64-pada devatas follow the numbered squares of Brihat Samhita 53.43-48, and 81-pada cells carry `verseSquare`, with `None` devata fields on the 28 squares the verse leaves unnamed.
- `entrance/pada` results type the devata labels the API now returns on `pada`: `deityRosterName`, `deityNameClassification`, `deityPlacementClassification` and `deityPlacementSource` (all optional).
- `SECURITY.md` lists the key types the API issues: `vk_live_`, `vk_ent_` and the sandbox-only `vk_sandbox_`. `vk_test_` keys are not issued and are rejected.
- The README and `examples/README.md` list only example scripts that exist, and repository links point to `github.com/vedika-io`.
- Removed internal tracking references from a source comment and this changelog.

## [3.0.8] - 2026-09-16

This is the first PyPI release since 3.0.5. It includes everything listed for 3.0.7 below, which was never published to PyPI.

- Added `ask_vastu_report` and `QuestionResponse.vastu_context`: ask questions about a Vastu report without sending birth details.
- Added multi-floor plan types and bounded conversation continuation.
- Public error classes keep their documented contracts.
- Package artifacts no longer carry internal service or provider names.
- Added the `ar/room-capture` Vastu operation (`VastuOperation.AR_ROOM_CAPTURE`) with typed `VastuRoomCapture` requests, `pointCloudDensityBasis` on scan-quality requests, and an optional `capture` on saved-scan snapshots.
- Credentials now use only the official HTTPS API origin or literal loopback HTTP. Custom HTTPS origins and remote HTTP are rejected; the legacy insecure-HTTP option cannot bypass this rule.
- Added typed assessment batches with retained caller idempotency keys, per-item results, HTML report options, and SVG opt-out. All 93 operation responses match recorded Rust fixtures, including versioned scoring and audit coverage metadata.

- **Compatibility change:** Python 3.10 or later is now required so the SDK can use urllib3 2.7.0 or later, which includes current redirect and decompression fixes. Requests 2.33.0 or later includes credential and archive-helper fixes. Python 3.8 and 3.9 are no longer supported. Both HTTP dependencies are capped below 3.0 pending major-version compatibility testing.
- Package preparation scripts build local artifacts without changing Git or publishing.
- **Behaviour change (Vastu API, 2026-09-17):** score `verdict` strings now describe agreement with the scored placement rules instead of giving building advice. The top-level `verified` field is now `false` on `room/*`, `placement/borewell`, `placement/well`, placement and specialized results when the guidance is later convention; use `placementVerified` and the per-field source labels for verse-backed parts. `reference/mandala/9-zone` labels every row `convention`, and remedies carry `remedyClassification` and `remedySource`. If your code shows `verdict` text or checks `verified`, review it for this change.


All notable changes to the Vedika Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.7] - 2026-09-07

### Security

- **`base_url` must now be a Vedika origin.** Until this release the constructor
  checked the *shape* of `base_url` - scheme, no embedded credentials, bare
  origin with no path or query - but never checked *where* it pointed. A
  perfectly well-formed `base_url="https://attacker.invalid"` satisfied every
  rule, and the first request carried a live `vk_live_*` key in both the
  `Authorization` and `X-API-Key` headers to a host Vedika does not operate.

  The client now refuses any host that is not `vedika.io`, a `*.vedika.io`
  subdomain, or loopback. Matching is on the registrable name, so `notvedika.io`
  and `api.vedika.io.attacker.com` are both rejected; a naive suffix test would
  have accepted the first. The JavaScript SDK already enforced this; Python
  now matches it.

  **If you set `base_url` to your own gateway, this is a breaking change.** It is
  deliberate: proxy Vedika server-side and keep the key on your server.

- **`allow_insecure_http` is now inert.** The only thing it could ever permit was
  a live API key travelling in cleartext to a remote host. Passing `True` with a
  non-loopback `base_url` now raises instead of silently doing nothing, so a
  caller who believes they opted in is told they did not. Loopback HTTP is
  unaffected and still works for local development.

### Note

3.0.6 was tagged in this repository but never published to PyPI. The last
release on PyPI is 3.0.5, which does **not** contain either of the fixes above.

## [3.0.6] - 2026-06-15

### Added (2026-08-11)
- **Full Vastu Shastra surface** — 76 operations across 17 families (mandala projection, entrance, rooms, site placements, compliance audits, scoring, floor-plan generation, reference tables, direction/declination), all under `/v2/astrology/vastu/`. Generic `vastu(op, params)` escape hatch plus named helpers: `vastu_reference()`, `vastu_mandala_project()`, `vastu_entrance_pada()`/`vastu_entrance_recommend()`, `vastu_room()`, `vastu_placement()`, `vastu_audit()`, `vastu_score()`, `vastu_plan_generate()`/`vastu_plan_from_requirements()`, `vastu_declination()`. Verb selection is automatic: `reference/*` and `direction/declination` dispatch GET, everything else POST. Vastu takes a building (plot polygon, rooms, compass zone) — never a birth chart.

### Security (2026-08-11)
- **Fixed cross-origin redirect credential forwarding.** The legacy `X-API-Key` header was still forwarded to a redirect destination even in cases where `requests` correctly strips `Authorization` on a cross-origin or HTTPS→HTTP-downgrade redirect, leaking the key off-origin. The client session now drops `X-API-Key` alongside `Authorization` on any such redirect.
- **Added a `base_url` origin policy.** The API key is now attached only to HTTPS origins by default; a non-loopback `http://` `base_url` is rejected unless the new `allow_insecure_http=True` client option opts in. Loopback (`localhost`, `127.0.0.1`, `::1`) is always allowed for local dev.

### Changed (transition-compat — no breaking changes)
- **Resilient v2-envelope unwrapping for the platform transition.** `_v2_payload()` previously returned any top-level `data` key unconditionally, which could mis-unwrap a bare reading that happened to nest a `data` block, and it only ran on the methods that called it. Two transition-sensitive families bypassed it entirely — `matrimony.unified_match` / `dosha_cancellation` (a verdict/money-sensitive family that, on an enveloped response, silently zeroed the score) and `dasha.current_all` — they now unwrap the envelope like every other v2 domain. Unwrapping is keyed on the canonical envelope markers (`success` / `billing` / `meta`) plus a dict `data`, so `billing` is no longer required.
- **`get_western_relationship()` is now transition-tolerant.** Synastry/composite prose (`interpretation`, per-aspect `orb_quality`/`signifies`) may be absent on some responses while the computed geometry stays parity-exact. The result is normalized so those keys are always present; code reading them never raises `KeyError` from either engine.

### Added
- `normalize_western_relationship()` helper (exported).
- `raw` field on `MatchResult`, `DoshaMatchResult`, and `AllDashaResult` so the full original payload is always retrievable (no field lost to the typed-model shape).

### Notes
- Fully backward-compatible. No breaking changes to existing consumers; method signatures unchanged, models gained only optional fields.

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
- **Voice AI** — Added `ask_voice()` for voice questions. Historical implementation labels and price estimates are omitted; use the current API catalog for availability and pricing.
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
