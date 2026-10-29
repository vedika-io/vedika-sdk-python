"""Resolve current public references or their reviewed standalone test copies."""
from pathlib import Path


def reference_path(source_relative, fixture_relative):
    source = Path(__file__).resolve().parents[3] / source_relative
    if source.is_file():
        return source
    fixture = Path(__file__).resolve().parent / "fixtures" / "reference" / fixture_relative
    if not fixture.is_file():
        raise FileNotFoundError(f"Required reference fixture is missing: {fixture_relative}")
    return fixture
