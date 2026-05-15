# Changelog

All notable changes to the Vedika Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-08

### Added

#### Core Features
- Initial release of Vedika Python SDK
- `VedikaClient` class for interacting with Vedika Astrology API
- Support for AI-powered conversational astrology queries (UNIQUE feature!)
- Advanced AI intelligence integration

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
- Comprehensive error messages
- 14 Indian language support plus English
- Prompt caching for 90% cost savings on repeated queries

#### Documentation
- Comprehensive README with examples
- Detailed API reference documentation
- Google-style docstrings for all public APIs
- Security best practices guide
- Contributing guidelines
- Code of Conduct (Contributor Covenant 2.0)

#### Development Tools
- Python 3.8+ support
- Type hints for all function signatures
- Black code formatting
- flake8 linting
- mypy type checking
- pytest testing framework
- Coverage reporting

#### Examples
- Basic chatbot example
- Birth chart analysis
- Compatibility checker
- Dosha detector
- Muhurtha finder
- Multi-language support demo
- Streaming responses
- Flask web application integration
- Django integration

### Security
- API keys encrypted in transit (HTTPS)
- GDPR compliant
- No data retention by default
- Security score: 95/100 (A grade)
- Comprehensive security documentation

### Performance
- Average response time: 2.14 seconds (simple queries)
- Complex queries: 28-36 seconds (deep analysis)
- 99.9% uptime with 3-tier ephemeris fallback
- High citation accuracy from classical texts

## [Unreleased]

### Planned Features
- Webhook support for real-time notifications
- GraphQL API support
- Additional ayanamsa systems
- Extended dosha remedies database
- Predictive transit analysis
- Enhanced caching strategies

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

### Release Cadence

- **Major releases**: As needed for breaking changes
- **Minor releases**: Monthly feature releases
- **Patch releases**: As needed for bug fixes

---

For the complete version history, see: https://github.com/vedika-io/vedika-sdk-python/releases

[1.0.0]: https://github.com/vedika-io/vedika-sdk-python/releases/tag/v1.0.0
