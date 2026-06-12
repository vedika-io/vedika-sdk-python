"""
Vedika API Data Models
Response models for the Vedika Astrology API.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BirthDetails:
    """
    Birth details for astrological calculations.

    Attributes:
        datetime: Birth datetime in ISO 8601 format (e.g., "1990-06-15T14:30:00+05:30")
        latitude: Birth location latitude (-90 to 90)
        longitude: Birth location longitude (-180 to 180)
        timezone: IANA timezone (e.g., "Asia/Kolkata")
    """
    datetime: str
    latitude: float
    longitude: float
    timezone: str = "UTC"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "datetime": self.datetime,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone
        }


@dataclass
class StructuredResponseSection:
    """
    Section within a structured response.

    Attributes:
        heading: Section heading text
        level: Heading level (1-6)
        paragraphs: List of paragraph strings
        bullets: List of bullet points
        numbered: List of numbered items
    """
    heading: str
    level: int
    paragraphs: List[str] = field(default_factory=list)
    bullets: List[str] = field(default_factory=list)
    numbered: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructuredResponseSection':
        """Create from API response dictionary."""
        return cls(
            heading=data.get("heading", ""),
            level=int(data.get("level", 2)),
            paragraphs=list(data.get("paragraphs", [])),
            bullets=list(data.get("bullets", [])),
            numbered=list(data.get("numbered", []))
        )


@dataclass
class StructuredResponse:
    """
    Structured JSON response object (when response_format='json').

    Attributes:
        title: Title of the response (from H1/H2)
        preamble: Content before first heading
        sections: List of parsed sections
        raw: Echo of the raw markdown
    """
    title: Optional[str] = None
    preamble: Optional[str] = None
    sections: List[StructuredResponseSection] = field(default_factory=list)
    raw: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructuredResponse':
        """Create from API response dictionary."""
        return cls(
            title=data.get("title"),
            preamble=data.get("preamble"),
            sections=[StructuredResponseSection.from_dict(s) for s in data.get("sections", [])],
            raw=data.get("raw", "")
        )


@dataclass
class Citation:
    """
    A single citation referencing a classical astrological source.

    SDK-1 (v2.3.1, Apr 21, 2026): Added to model forthcoming public-surface
    citation field. All fields are optional; only populated when the
    server-side citation gate is enabled (enterprise tier).

    Attributes:
        id: Short ID of the cited passage
        topic: Classical topic/rule reference (e.g. "Marriage — 7th house lord")
        source: Source text (e.g. "BPHS", "Saravali", "Phaladeepika")
        reference: Chapter and verse reference (e.g. "BPHS 7.1-7.5")
        text: The cited passage text, if provided
    """
    id: Optional[str] = None
    topic: Optional[str] = None
    source: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Citation':
        """Create from API response dictionary."""
        return cls(
            id=data.get("id"),
            topic=data.get("topic"),
            source=data.get("source"),
            reference=data.get("reference"),
            text=data.get("text"),
        )


@dataclass
class QuestionResponse:
    """
    Response from AI chatbot query (UNIQUE to Vedika!).

    Attributes:
        answer: Detailed astrological answer from 6 AI agents
        confidence: Prediction confidence score (0.0 to 1.0)
        credits_used: Credits consumed for this query
        processing_time: Time taken to process (seconds)
        language: Response language
        sources: Astrological factors considered
        citations: Classical-source citations (SDK-1 v2.3.1) — empty/None
            on non-enterprise tiers
        structured_response: Parsed sections when response_format='json'
    """
    answer: str
    confidence: float
    credits_used: int
    processing_time: float
    language: str = "en"
    sources: List[str] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    structured_response: Optional[StructuredResponse] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionResponse':
        """Create from API response dictionary."""
        structured = None
        if data.get("structuredResponse"):
            structured = StructuredResponse.from_dict(data["structuredResponse"])

        # SDK-1 (v2.3.1, Apr 21, 2026): Parse optional citations array.
        # Tolerant to both missing key and null/non-list values.
        raw_citations = data.get("citations") or []
        citations = [
            Citation.from_dict(c) if isinstance(c, dict) else Citation(text=str(c))
            for c in raw_citations
        ] if isinstance(raw_citations, list) else []

        return cls(
            answer=data.get("answer", ""),
            confidence=data.get("confidence", 0.0),
            credits_used=data.get("creditsUsed", 0),
            processing_time=data.get("processingTime", 0.0),
            language=data.get("language", "en"),
            sources=data.get("sources", []),
            citations=citations,
            structured_response=structured
        )


@dataclass
class Planet:
    """Planet position in birth chart."""
    name: str
    longitude: float
    latitude: float
    sign: str
    house: int
    nakshatra: str
    retrograde: bool = False


@dataclass
class House:
    """House cusp in birth chart."""
    number: int
    sign: str
    degree: float
    lord: str


@dataclass
class BirthChart:
    """
    Complete birth chart (Kundali/Horoscope).

    Attributes:
        ascendant: Rising sign
        planets: Planetary positions
        houses: House cusps
        ayanamsa: Ayanamsa system used
    """
    ascendant: str
    planets: List[Planet]
    houses: List[House]
    ayanamsa: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BirthChart':
        """Create from API response dictionary."""
        planets = [
            Planet(
                name=p.get("name", ""),
                longitude=p.get("longitude", 0.0),
                latitude=p.get("latitude", 0.0),
                sign=p.get("sign", ""),
                house=p.get("house", 1),
                nakshatra=p.get("nakshatra", ""),
                retrograde=p.get("retrograde", False)
            )
            for p in data.get("planets", [])
        ]

        houses = [
            House(
                number=h.get("number", 1),
                sign=h.get("sign", ""),
                degree=h.get("degree", 0.0),
                lord=h.get("lord", "")
            )
            for h in data.get("houses", [])
        ]

        return cls(
            ascendant=data.get("ascendant", ""),
            planets=planets,
            houses=houses,
            ayanamsa=data.get("ayanamsa", "lahiri")
        )


@dataclass
class Dasha:
    """Dasha (planetary period) information."""
    planet: str
    start_date: str
    end_date: str
    duration_years: float
    level: str  # "Mahadasha", "Antardasha", or "Pratyantardasha"


@dataclass
class DashaResponse:
    """
    Vimshottari Dasha periods.

    Attributes:
        mahadashas: Major planetary periods (120 years)
        antardashas: Sub-periods within current Mahadasha
        pratyantardashas: Sub-sub-periods within current Antardasha
        current_dasha: Currently active Mahadasha
    """
    mahadashas: List[Dasha]
    antardashas: List[Dasha] = field(default_factory=list)
    pratyantardashas: List[Dasha] = field(default_factory=list)
    current_dasha: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashaResponse':
        """Create from API response dictionary."""
        mahadashas = [
            Dasha(
                planet=d.get("planet", ""),
                start_date=d.get("startDate", ""),
                end_date=d.get("endDate", ""),
                duration_years=d.get("durationYears", 0.0),
                level="Mahadasha"
            )
            for d in data.get("mahadashas", [])
        ]

        def _periods(key):
            return [
                Dasha(
                    planet=d.get("planet", ""),
                    start_date=d.get("startDate", ""),
                    end_date=d.get("endDate", ""),
                    duration_years=d.get("durationYears", 0.0),
                    level=key,
                )
                for d in data.get(key, [])
            ]
        return cls(
            mahadashas=mahadashas,
            antardashas=_periods("antardashas"),
            pratyantardashas=_periods("pratyantardashas"),
            current_dasha=data.get("currentDasha"),
        )


@dataclass
class CompatibilityResponse:
    """
    Marriage compatibility analysis (Ashtakoota).

    Attributes:
        total_score: Total compatibility score (0-36)
        compatibility_level: Overall compatibility (Excellent/Good/Average/Poor)
        varna: Varna koota score (1)
        vashya: Vashya koota score (2)
        tara: Tara koota score (3)
        yoni: Yoni koota score (4)
        graha_maitri: Graha Maitri koota score (5)
        gana: Gana koota score (6)
        bhakoot: Bhakoot koota score (7)
        nadi: Nadi koota score (8)
        mangal_dosha_check: Mangal dosha compatibility
    """
    total_score: int
    compatibility_level: str
    varna: int = 0
    vashya: int = 0
    tara: int = 0
    yoni: int = 0
    graha_maitri: int = 0
    gana: int = 0
    bhakoot: int = 0
    nadi: int = 0
    mangal_dosha_check: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompatibilityResponse':
        """Create from API response dictionary."""
        return cls(
            total_score=data.get("totalScore", 0),
            compatibility_level=data.get("compatibilityLevel", "Unknown"),
            varna=data.get("varna", 0),
            vashya=data.get("vashya", 0),
            tara=data.get("tara", 0),
            yoni=data.get("yoni", 0),
            graha_maitri=data.get("grahaMaitri", 0),
            gana=data.get("gana", 0),
            bhakoot=data.get("bhakoot", 0),
            nadi=data.get("nadi", 0),
            mangal_dosha_check=data.get("mangalDoshaCheck", "")
        )


@dataclass
class Yoga:
    """Astrological Yoga (planetary combination)."""
    name: str
    description: str
    strength: str  # "Strong", "Moderate", "Weak"
    effects: List[str] = field(default_factory=list)


@dataclass
class YogaResponse:
    """
    Yoga detection results (300+ yogas).

    Attributes:
        yogas: List of detected yogas
        total_count: Total number of yogas found
        beneficial_count: Number of beneficial yogas
        malefic_count: Number of malefic yogas
    """
    yogas: List[Yoga]
    total_count: int = 0
    beneficial_count: int = 0
    malefic_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YogaResponse':
        """Create from API response dictionary."""
        yogas = [
            Yoga(
                name=y.get("name", ""),
                description=y.get("description", ""),
                strength=y.get("strength", "Moderate"),
                effects=y.get("effects", [])
            )
            for y in data.get("yogas", [])
        ]

        return cls(
            yogas=yogas,
            total_count=data.get("totalCount", len(yogas)),
            beneficial_count=data.get("beneficialCount", 0),
            malefic_count=data.get("maleficCount", 0)
        )


@dataclass
class DoshaInfo:
    """Information about a specific dosha."""
    present: bool
    type: str = ""
    severity: str = ""  # "High", "Medium", "Low"
    description: str = ""
    remedies: List[str] = field(default_factory=list)


@dataclass
class DoshaResponse:
    """
    Comprehensive dosha analysis.

    Attributes:
        kaal_sarp_dosha: Kaal Sarp Dosha details
        mangal_dosha: Mangal/Kuja Dosha details
        sade_sati: Sade Sati period details
        pitra_dosha: Pitra Dosha details
    """
    kaal_sarp_dosha: DoshaInfo
    mangal_dosha: DoshaInfo
    sade_sati: DoshaInfo
    pitra_dosha: DoshaInfo

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DoshaResponse':
        """Create from API response dictionary."""
        def parse_dosha(d: Dict[str, Any]) -> DoshaInfo:
            return DoshaInfo(
                present=d.get("present", False),
                type=d.get("type", ""),
                severity=d.get("severity", ""),
                description=d.get("description", ""),
                remedies=d.get("remedies", [])
            )

        return cls(
            kaal_sarp_dosha=parse_dosha(data.get("kaalSarpDosha", {})),
            mangal_dosha=parse_dosha(data.get("mangalDosha", {})),
            sade_sati=parse_dosha(data.get("sadeSati", {})),
            pitra_dosha=parse_dosha(data.get("pitraDosha", {}))
        )


@dataclass
class TimeWindow:
    """Auspicious or inauspicious time window."""
    start_time: str
    end_time: str
    quality: str  # "Excellent", "Good", "Average", "Avoid"
    reason: str = ""


@dataclass
class MuhurthaResponse:
    """
    Muhurtha (auspicious timing) analysis.

    Attributes:
        date: Date analyzed
        good_times: Auspicious time windows
        bad_times: Inauspicious time windows
        best_time: Most auspicious time
        event_type: Type of event
    """
    date: str
    good_times: List[TimeWindow]
    bad_times: List[TimeWindow]
    best_time: Optional[str] = None
    event_type: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MuhurthaResponse':
        """Create from API response dictionary."""
        good_times = [
            TimeWindow(
                start_time=t.get("startTime", ""),
                end_time=t.get("endTime", ""),
                quality=t.get("quality", "Good"),
                reason=t.get("reason", "")
            )
            for t in data.get("goodTimes", [])
        ]

        bad_times = [
            TimeWindow(
                start_time=t.get("startTime", ""),
                end_time=t.get("endTime", ""),
                quality=t.get("quality", "Avoid"),
                reason=t.get("reason", "")
            )
            for t in data.get("badTimes", [])
        ]

        return cls(
            date=data.get("date", ""),
            good_times=good_times,
            bad_times=bad_times,
            best_time=data.get("bestTime"),
            event_type=data.get("eventType", "")
        )


@dataclass
class NumerologyResponse:
    """
    Numerology analysis (37 calculations).

    Attributes:
        life_path: Life path number (1-9, 11, 22, 33)
        expression: Expression/Destiny number
        soul_urge: Soul urge/Heart's desire number
        personality: Personality number
        birth_day: Birth day number
        maturity: Maturity number
        lucky_numbers: Lucky numbers
        lucky_colors: Lucky colors
        lucky_days: Lucky days of the week
    """
    life_path: int
    expression: int
    soul_urge: int
    personality: int
    birth_day: int
    maturity: int
    lucky_numbers: List[int] = field(default_factory=list)
    lucky_colors: List[str] = field(default_factory=list)
    lucky_days: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NumerologyResponse':
        """Create from API response dictionary."""
        return cls(
            life_path=data.get("lifePath", 0),
            expression=data.get("expression", 0),
            soul_urge=data.get("soulUrge", 0),
            personality=data.get("personality", 0),
            birth_day=data.get("birthDay", 0),
            maturity=data.get("maturity", 0),
            lucky_numbers=data.get("luckyNumbers", []),
            lucky_colors=data.get("luckyColors", []),
            lucky_days=data.get("luckyDays", [])
        )


@dataclass
class VoiceBilling:
    """Customer-facing billing block on a voice response."""
    cost_usd: float = 0.0
    currency: str = "USD"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceBilling':
        return cls(
            cost_usd=float(data.get("costUsd", 0.0)),
            currency=data.get("currency", "USD"),
        )


@dataclass
class VoiceResponse:
    """
    Voice query result envelope.

    SDK-3 (v2.3.1, Apr 21, 2026): Types the response from ``/api/v1/voice``.

    The server returns binary ``audio/mpeg`` with metadata in the
    ``X-Vedika-Voice-Meta`` base64-JSON header. When TTS fails, it falls back
    to a JSON body with ``audio=None`` and the text answer in ``response``.

    This model normalizes both paths: ``audio`` holds the binary audio bytes
    (or None in fallback mode), ``response_text`` holds the narrated answer,
    and everything else is parsed from either the JSON body or the decoded
    header.

    Attributes:
        audio: Raw audio bytes (``audio/mpeg``) or None on TTS fallback
        response_text: AI-generated text answer (always present)
        language: Detected/output language (ISO 639-1)
        tier: Public voice-tier label
        billing: Customer-facing cost block
        duration_ms: End-to-end processing duration
        stt_duration_sec: Speech-to-text duration
        tts_duration_sec: Text-to-speech duration (None on fallback)
        conversation_id: Conversation ID for multi-turn threading
        is_fallback: True when TTS failed and audio is None
    """
    audio: Optional[bytes] = None
    response_text: str = ""
    language: Optional[str] = None
    tier: Optional[str] = None
    billing: Optional[VoiceBilling] = None
    duration_ms: Optional[int] = None
    stt_duration_sec: Optional[float] = None
    tts_duration_sec: Optional[float] = None
    conversation_id: Optional[str] = None
    is_fallback: bool = False

    @classmethod
    def from_binary(
        cls,
        audio_bytes: bytes,
        meta: Dict[str, Any],
    ) -> 'VoiceResponse':
        """Build from binary audio + parsed X-Vedika-Voice-Meta header."""
        billing_data = meta.get("billing")
        return cls(
            audio=audio_bytes,
            response_text="",  # text is spoken, not embedded
            language=meta.get("language"),
            tier=meta.get("tier"),
            billing=VoiceBilling.from_dict(billing_data) if isinstance(billing_data, dict) else None,
            duration_ms=meta.get("durationMs"),
            stt_duration_sec=meta.get("sttDurationSec"),
            tts_duration_sec=meta.get("ttsDurationSec"),
            conversation_id=meta.get("conversationId"),
            is_fallback=False,
        )

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'VoiceResponse':
        """Build from JSON fallback body (TTS failed)."""
        billing_data = data.get("billing")
        return cls(
            audio=None,
            response_text=data.get("response", ""),
            language=data.get("language"),
            tier=data.get("tier"),
            billing=VoiceBilling.from_dict(billing_data) if isinstance(billing_data, dict) else None,
            duration_ms=data.get("durationMs"),
            stt_duration_sec=data.get("sttDurationSec"),
            tts_duration_sec=data.get("ttsDurationSec"),
            conversation_id=data.get("conversationId"),
            is_fallback=True,
        )


# ═══════════════════════════════════════════
# Project Dominion — New Domain Models
# ═══════════════════════════════════════════


@dataclass
class TarotCard:
    """A single tarot card."""
    name: str = ""
    arcana: str = ""  # "major" or "minor"
    suit: Optional[str] = None
    number: Optional[int] = None
    orientation: str = "upright"  # "upright" or "reversed"
    meaning: str = ""
    keywords: List[str] = field(default_factory=list)
    image_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TarotCard':
        return cls(
            name=data.get("name", ""),
            arcana=data.get("arcana", ""),
            suit=data.get("suit"),
            number=data.get("number"),
            orientation=data.get("orientation", "upright"),
            meaning=data.get("meaning", ""),
            keywords=data.get("keywords", []),
            image_url=data.get("imageUrl"),
        )


@dataclass
class TarotReading:
    """Full tarot reading with spread."""
    spread: str = ""
    question: Optional[str] = None
    cards: List[TarotCard] = field(default_factory=list)
    interpretation: str = ""
    theme: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TarotReading':
        return cls(
            spread=data.get("spread", ""),
            question=data.get("question"),
            cards=[TarotCard.from_dict(c) for c in data.get("cards", [])],
            interpretation=data.get("interpretation", ""),
            theme=data.get("theme"),
        )


@dataclass
class SpreadInfo:
    """Tarot spread definition."""
    id: str = ""
    name: str = ""
    card_count: int = 0
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpreadInfo':
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            card_count=data.get("cardCount", 0),
            description=data.get("description", ""),
        )


@dataclass
class SpreadList:
    """List of available tarot spreads."""
    spreads: List[SpreadInfo] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpreadList':
        return cls(
            spreads=[SpreadInfo.from_dict(s) for s in data.get("spreads", [])],
        )


@dataclass
class ChineseZodiac:
    """Chinese zodiac animal result."""
    animal: str = ""
    polarity: str = ""
    fixed_element: str = ""
    year_element: str = ""
    traits: List[str] = field(default_factory=list)
    compatible: List[str] = field(default_factory=list)
    incompatible: List[str] = field(default_factory=list)
    year: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChineseZodiac':
        return cls(
            animal=data.get("animal", ""),
            polarity=data.get("polarity", ""),
            fixed_element=data.get("fixedElement", ""),
            year_element=data.get("yearElement", ""),
            traits=data.get("traits", []),
            compatible=data.get("compatible", []),
            incompatible=data.get("incompatible", []),
            year=data.get("year", 0),
        )


@dataclass
class BaZiChart:
    """BaZi (Four Pillars) chart."""
    year_pillar: Dict[str, str] = field(default_factory=dict)
    month_pillar: Dict[str, str] = field(default_factory=dict)
    day_pillar: Dict[str, str] = field(default_factory=dict)
    hour_pillar: Dict[str, str] = field(default_factory=dict)
    day_master: str = ""
    day_master_strength: str = ""
    favorable_elements: List[str] = field(default_factory=list)
    unfavorable_elements: List[str] = field(default_factory=list)
    luck_pillars: List[Dict[str, Any]] = field(default_factory=list)
    interpretation: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaZiChart':
        return cls(
            year_pillar=data.get("yearPillar", {}),
            month_pillar=data.get("monthPillar", {}),
            day_pillar=data.get("dayPillar", {}),
            hour_pillar=data.get("hourPillar", {}),
            day_master=data.get("dayMaster", ""),
            day_master_strength=data.get("dayMasterStrength", ""),
            favorable_elements=data.get("favorableElements", []),
            unfavorable_elements=data.get("unfavorableElements", []),
            luck_pillars=data.get("luckPillars", []),
            interpretation=data.get("interpretation", ""),
        )


@dataclass
class KuaResult:
    """Feng Shui Kua number result."""
    kua_number: int = 0
    group: str = ""
    auspicious_directions: List[str] = field(default_factory=list)
    inauspicious_directions: List[str] = field(default_factory=list)
    best_directions: Dict[str, str] = field(default_factory=dict)
    gender: str = ""
    birth_year: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KuaResult':
        return cls(
            kua_number=data.get("kuaNumber", 0),
            group=data.get("group", ""),
            auspicious_directions=data.get("auspiciousDirections", []),
            inauspicious_directions=data.get("inauspiciousDirections", []),
            best_directions=data.get("bestDirections", {}),
            gender=data.get("gender", ""),
            birth_year=data.get("birthYear", 0),
        )


@dataclass
class Hexagram:
    """I Ching hexagram result."""
    number: int = 0
    chinese_name: str = ""
    english_name: str = ""
    lines: List[Dict[str, Any]] = field(default_factory=list)
    upper_trigram: str = ""
    lower_trigram: str = ""
    judgment: str = ""
    image: str = ""
    moving_lines: List[str] = field(default_factory=list)
    relating_hexagram: Optional[Dict[str, Any]] = None
    interpretation: str = ""
    question: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Hexagram':
        return cls(
            number=data.get("number", 0),
            chinese_name=data.get("chineseName", ""),
            english_name=data.get("englishName", ""),
            lines=data.get("lines", []),
            upper_trigram=data.get("upperTrigram", ""),
            lower_trigram=data.get("lowerTrigram", ""),
            judgment=data.get("judgment", ""),
            image=data.get("image", ""),
            moving_lines=data.get("movingLines", []),
            relating_hexagram=data.get("relatingHexagram"),
            interpretation=data.get("interpretation", ""),
            question=data.get("question"),
        )


@dataclass
class Crystal:
    """Crystal recommendation."""
    name: str = ""
    properties: List[str] = field(default_factory=list)
    chakra: str = ""
    element: str = ""
    zodiac_affinity: List[str] = field(default_factory=list)
    color: str = ""
    usage: str = ""
    image_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Crystal':
        return cls(
            name=data.get("name", ""),
            properties=data.get("properties", []),
            chakra=data.get("chakra", ""),
            element=data.get("element", ""),
            zodiac_affinity=data.get("zodiacAffinity", []),
            color=data.get("color", ""),
            usage=data.get("usage", ""),
            image_url=data.get("imageUrl"),
        )


@dataclass
class BodyGraph:
    """Human Design body graph."""
    type: str = ""
    strategy: str = ""
    authority: str = ""
    profile: str = ""
    defined_centers: List[str] = field(default_factory=list)
    open_centers: List[str] = field(default_factory=list)
    channels: List[Dict[str, Any]] = field(default_factory=list)
    incarnation_cross: str = ""
    gates: List[Dict[str, Any]] = field(default_factory=list)
    interpretation: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BodyGraph':
        return cls(
            type=data.get("type", ""),
            strategy=data.get("strategy", ""),
            authority=data.get("authority", ""),
            profile=data.get("profile", ""),
            defined_centers=data.get("definedCenters", []),
            open_centers=data.get("openCenters", []),
            channels=data.get("channels", []),
            incarnation_cross=data.get("incarnationCross", ""),
            gates=data.get("gates", []),
            interpretation=data.get("interpretation", ""),
        )


@dataclass
class HDType:
    """Human Design type summary."""
    type: str = ""
    strategy: str = ""
    not_self_theme: str = ""
    signature: str = ""
    authority: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HDType':
        return cls(
            type=data.get("type", ""),
            strategy=data.get("strategy", ""),
            not_self_theme=data.get("notSelfTheme", ""),
            signature=data.get("signature", ""),
            authority=data.get("authority", ""),
            description=data.get("description", ""),
        )


@dataclass
class MatchResult:
    """Matrimony unified match result."""
    total_score: int = 0
    max_score: int = 36
    percentage: float = 0.0
    verdict: str = ""
    kootas: List[Dict[str, Any]] = field(default_factory=list)
    dosha_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchResult':
        return cls(
            total_score=data.get("totalScore", 0),
            max_score=data.get("maxScore", 36),
            percentage=data.get("percentage", 0.0),
            verdict=data.get("verdict", ""),
            kootas=data.get("kootas", []),
            dosha_analysis=data.get("doshaAnalysis", {}),
            recommendation=data.get("recommendation", ""),
        )


@dataclass
class DoshaMatchResult:
    """Dosha cancellation result for matrimony."""
    dosha_type: str = ""
    person1_has_dosha: bool = False
    person2_has_dosha: bool = False
    cancelled: bool = False
    cancellation_reasons: List[str] = field(default_factory=list)
    severity: Optional[str] = None
    remedies: List[str] = field(default_factory=list)
    explanation: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DoshaMatchResult':
        return cls(
            dosha_type=data.get("doshaType", ""),
            person1_has_dosha=data.get("person1HasDosha", False),
            person2_has_dosha=data.get("person2HasDosha", False),
            cancelled=data.get("cancelled", False),
            cancellation_reasons=data.get("cancellationReasons", []),
            severity=data.get("severity"),
            remedies=data.get("remedies", []),
            explanation=data.get("explanation", ""),
        )


@dataclass
class MantraResult:
    """Mantra recommendation."""
    mantra: str = ""
    transliteration: str = ""
    meaning: str = ""
    deity: str = ""
    planet: str = ""
    repetitions: int = 0
    best_time: str = ""
    additional_mantras: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MantraResult':
        return cls(
            mantra=data.get("mantra", ""),
            transliteration=data.get("transliteration", ""),
            meaning=data.get("meaning", ""),
            deity=data.get("deity", ""),
            planet=data.get("planet", ""),
            repetitions=data.get("repetitions", 0),
            best_time=data.get("bestTime", ""),
            additional_mantras=data.get("additionalMantras", []),
        )


@dataclass
class DeityResult:
    """Deity recommendation."""
    deity: str = ""
    reason: str = ""
    associated_planet: str = ""
    worship_method: str = ""
    auspicious_day: str = ""
    offerings: List[str] = field(default_factory=list)
    direction: str = ""
    additional_deities: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeityResult':
        return cls(
            deity=data.get("deity", ""),
            reason=data.get("reason", ""),
            associated_planet=data.get("associatedPlanet", ""),
            worship_method=data.get("worshipMethod", ""),
            auspicious_day=data.get("auspiciousDay", ""),
            offerings=data.get("offerings", []),
            direction=data.get("direction", ""),
            additional_deities=data.get("additionalDeities", []),
        )


@dataclass
class PastLifeResult:
    """Past life karmic indicators."""
    indicators: List[Dict[str, Any]] = field(default_factory=list)
    purva_punya: str = ""
    twelfth_house: str = ""
    karmic_debts: List[str] = field(default_factory=list)
    karmic_blessings: List[str] = field(default_factory=list)
    interpretation: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PastLifeResult':
        return cls(
            indicators=data.get("indicators", []),
            purva_punya=data.get("purvaPunya", ""),
            twelfth_house=data.get("twelfthHouse", ""),
            karmic_debts=data.get("karmicDebts", []),
            karmic_blessings=data.get("karmicBlessings", []),
            interpretation=data.get("interpretation", ""),
        )


@dataclass
class DailyBundle:
    """Daily bundle combining multiple daily insights."""
    horoscope: Dict[str, Any] = field(default_factory=dict)
    panchang: Dict[str, Any] = field(default_factory=dict)
    tarot_card: Optional[TarotCard] = None
    mantra: Optional[Dict[str, str]] = None
    crystal: Optional[Dict[str, Any]] = None
    date: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyBundle':
        tc = data.get("tarotCard")
        return cls(
            horoscope=data.get("horoscope", {}),
            panchang=data.get("panchang", {}),
            tarot_card=TarotCard.from_dict(tc) if isinstance(tc, dict) else None,
            mantra=data.get("mantra"),
            crystal=data.get("crystal"),
            date=data.get("date", ""),
        )


@dataclass
class AllDashaResult:
    """All dasha systems current periods."""
    vimshottari: Dict[str, Any] = field(default_factory=dict)
    ashtottari: Optional[Dict[str, Any]] = None
    chara: Optional[Dict[str, Any]] = None
    yogini: Optional[Dict[str, Any]] = None
    recommended: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AllDashaResult':
        return cls(
            vimshottari=data.get("vimshottari", {}),
            ashtottari=data.get("ashtottari"),
            chara=data.get("chara"),
            yogini=data.get("yogini"),
            recommended=data.get("recommended", ""),
        )


@dataclass
class HealthResult:
    """Health astrology result."""
    vulnerable_areas: List[Dict[str, Any]] = field(default_factory=list)
    current_transits: str = ""
    recommendations: List[str] = field(default_factory=list)
    ayurvedic_dosha: str = ""
    healing_modalities: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthResult':
        return cls(
            vulnerable_areas=data.get("vulnerableAreas", []),
            current_transits=data.get("currentTransits", ""),
            recommendations=data.get("recommendations", []),
            ayurvedic_dosha=data.get("ayurvedicDosha", ""),
            healing_modalities=data.get("healingModalities", []),
        )


@dataclass
class CareerResult:
    """Career astrology result."""
    suitable_fields: List[str] = field(default_factory=list)
    tenth_house: str = ""
    career_yogas: List[Dict[str, str]] = field(default_factory=list)
    transit_forecast: str = ""
    auspicious_periods: List[Dict[str, str]] = field(default_factory=list)
    guidance: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CareerResult':
        return cls(
            suitable_fields=data.get("suitableFields", []),
            tenth_house=data.get("tenthHouse", ""),
            career_yogas=data.get("careerYogas", []),
            transit_forecast=data.get("transitForecast", ""),
            auspicious_periods=data.get("auspiciousPeriods", []),
            guidance=data.get("guidance", ""),
        )
