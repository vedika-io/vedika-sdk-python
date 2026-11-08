"""SSE wire conformance through the public streaming API, without live API calls."""

import io
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import requests

from vedika import VedikaClient

CASES = json.loads(
    (Path(__file__).parent / "fixtures/sse-events.json").read_text(encoding="utf-8")
)
BIRTH = {"datetime": "2000-01-01T00:00:00Z", "latitude": 0, "longitude": 0}


class ChunkedBody:
    def __init__(self, chunks: Iterable[bytes]) -> None:
        self.chunks = chunks
        self.closed = False

    def stream(self, amount: int, decode_content: bool = True) -> Iterator[bytes]:
        yield from self.chunks

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        pass


def client_for(chunks: Iterable[bytes]) -> tuple[VedikaClient, ChunkedBody]:
    raw = ChunkedBody(chunks)
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "text/event-stream"
    response.raw = raw
    client = VedikaClient(api_key="vk_test_local", max_retries=3)
    client.session.post = Mock(return_value=response)
    return client, raw


def consume(chunks: Iterable[bytes]) -> list[str]:
    client, _ = client_for(chunks)
    values = list(client.ask_question_stream("test", BIRTH))
    assert client.session.post.call_count == 1
    return values


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_every_byte_boundary(case: dict[str, Any]) -> None:
    wire = case["wire"].encode("utf-8")
    assert consume([wire]) == case["expected"]
    for split in range(len(wire) + 1):
        assert consume([wire[:split], wire[split:]]) == case["expected"]
    assert consume([bytes([byte]) for byte in wire]) == case["expected"]


def test_invalid_utf8_uses_replacement_decoding() -> None:
    assert consume([b"data: ", b"\xff", b"\n\n"]) == ["\ufffd"]


def test_yields_before_eof_and_closes_response_on_cancellation() -> None:
    def chunks() -> Iterator[bytes]:
        yield b"data: first\n\n"
        raise AssertionError("read past cancellation")

    client, raw = client_for(chunks())
    stream = client.ask_question_stream("test", BIRTH)
    assert next(stream) == "first"
    stream.close()
    assert raw.closed


def test_stream_failure_is_not_retried_or_delivered_as_partial_data() -> None:
    def chunks() -> Iterator[bytes]:
        yield b"data: first\n\ndata: partial"
        raise requests.exceptions.ChunkedEncodingError("connection lost")

    client, raw = client_for(chunks())
    stream = client.ask_question_stream("test", BIRTH)
    assert next(stream) == "first"
    with pytest.raises(requests.exceptions.ChunkedEncodingError):
        next(stream)
    assert raw.closed
    assert client.session.post.call_count == 1


def test_requests_response_line_endings() -> None:
    client, _ = client_for([])
    response = client.session.post.return_value
    response.raw = io.BytesIO(b"data:first\r\ndata:second\r\n\r\n")
    assert list(client.ask_question_stream("test", BIRTH)) == ["first\nsecond"]
