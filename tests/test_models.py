"""QuestionResponse.from_dict shape tests.

The live server (verified against web/vedika-public/openapi.json
`/api/v1/astrology/query`) returns `response` + `metadata` + `conversationId`,
not the legacy `answer` / `confidence` / `creditsUsed` / `processingTime` /
`conversation_id` shape the README and this model previously assumed. These
tests pin that BOTH shapes parse without raising and that the live shape's
real fields make it onto the model.
"""

from vedika.models import QuestionResponse


LIVE_SHAPE = {
    "success": True,
    "response": "Your 10th house of career is governed by Saturn...",
    "metadata": {
        "model": "Vedika AI",
        "engine": "vedika-intelligence",
        "processing_time_ms": 18420,
        "cost": {"costUsd": 0.0142, "currency": "USD"},
        "language": "en",
    },
    "conversationId": "conv_8f3a21",
}

LEGACY_SHAPE = {
    "answer": "Legacy answer text",
    "confidence": 0.97,
    "creditsUsed": 450,
    "processingTime": 28.7,
    "language": "en",
}


def test_parses_the_live_wire_shape():
    r = QuestionResponse.from_dict(LIVE_SHAPE)
    assert r.answer == LIVE_SHAPE["response"]
    assert r.conversation_id == "conv_8f3a21"
    assert r.processing_time == 18.42  # ms -> s
    assert r.language == "en"
    assert r.raw == LIVE_SHAPE
    # Fields the live engine doesn't send fall back to safe defaults, not a KeyError.
    assert r.confidence == 0.0
    assert r.credits_used == 0


def test_parses_the_legacy_shape_unchanged():
    r = QuestionResponse.from_dict(LEGACY_SHAPE)
    assert r.answer == "Legacy answer text"
    assert r.confidence == 0.97
    assert r.credits_used == 450
    assert r.processing_time == 28.7
    assert r.conversation_id is None


def test_current_openapi_query_example_retains_all_public_fields():
    import json
    from pathlib import Path
    import pytest
    root=Path(__file__).resolve().parents[3]
    spec_path=root/"web/vedika-public/openapi.json"
    if not spec_path.is_file():
        pytest.skip("needs the monorepo's web/vedika-public/openapi.json (not in the standalone SDK repo)")
    spec=json.loads(spec_path.read_text())
    example=spec["paths"]["/api/v1/astrology/query"]["post"]["responses"]["200"]["content"]["application/json"]["example"]
    result=QuestionResponse.from_dict(example)
    assert result.answer==example["response"]
    assert result.conversation_id==example["conversationId"]
    assert result.processing_time==example["metadata"]["processing_time_ms"]/1000
    assert result.language==example["metadata"]["language"]
    assert result.raw==example
    assert result.raw["metadata"]["cost"]==example["metadata"]["cost"]
    assert result.raw["birthChart"]==example["birthChart"]
    assert result.raw["followUps"]==example["followUps"]


def test_zero_legacy_values_and_structured_sections_remain_exact():
    result=QuestionResponse.from_dict({
        "answer":"", "confidence":0, "creditsUsed":0, "processingTime":0,
        "structuredResponse":{"title":"Reading", "sections":[{"heading":"Room", "level":2,"paragraphs":["Result"]}]},
        "citations":None,
    })
    assert result.answer=="" and result.confidence==0 and result.processing_time==0
    assert result.structured_response.sections[0].paragraphs==["Result"]
    assert result.citations==[]


def test_parses_vastu_report_context():
    r = QuestionResponse.from_dict({
        **LIVE_SHAPE,
        "vastuContext": {"itemIds": ["D1"], "citedItems": ["D1"], "verified": False},
    })
    assert r.vastu_context == {"itemIds": ["D1"], "citedItems": ["D1"], "verified": False}
    assert QuestionResponse.from_dict(LIVE_SHAPE).vastu_context is None
