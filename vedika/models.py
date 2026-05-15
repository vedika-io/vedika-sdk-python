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
class QuestionResponse:
    """
    Response from AI chatbot query (UNIQUE to Vedika!).

    Attributes:
        answer: Detailed astrological answer
        confidence: Response metadata score
        credits_used: Credits consumed for this query
        processing_time: Time taken to process (seconds)
        language: Response language
        sources: Astrological factors considered
    """
    answer: str
    confidence: float
    credits_used: int
    processing_time: float
    language: str = "en"
    sources: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionResponse':
        """Create from API response dictionary."""
        return cls(
            answer=data.get("answer", ""),
            confidence=data.get("confidence", 0.0),
            credits_used=data.get("creditsUsed", 0),
            processing_time=data.get("processingTime", 0.0),
            language=data.get("language", "en"),
            sources=data.get("sources", [])
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

        return cls(
            mahadashas=mahadashas,
            current_dasha=data.get("currentDasha")
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
