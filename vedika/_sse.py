"""Internal SSE framing; the public API yields complete event data strings.

https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation
"""
from __future__ import annotations

import codecs
from collections.abc import Iterable, Iterator


def _event_lines(chunks: Iterable[bytes]) -> Iterator[str]:
    # Keep UTF-8 state across chunks and strip only the stream's leading BOM.
    decoder = codecs.getincrementaldecoder("utf-8-sig")(errors="replace")
    parts: list[str] = []
    after_cr = False

    def lines(text: str) -> Iterator[str]:
        nonlocal parts, after_cr
        start = 0
        for index, char in enumerate(text):
            if after_cr:
                after_cr = False
                if char == "\n":
                    start = index + 1
                    continue
            if char in ("\r", "\n"):
                parts.append(text[start:index])
                line = "".join(parts)
                parts = []
                start = index + 1
                after_cr = char == "\r"
                yield line
        if start < len(text):
            parts.append(text[start:])

    for chunk in chunks:
        yield from lines(decoder.decode(chunk))
    yield from lines(decoder.decode(b"", final=True))
    # An unterminated line at EOF does not complete an event.


def iter_sse_data(chunks: Iterable[bytes]) -> Iterator[str]:
    data: list[str] = []
    for line in _event_lines(chunks):
        if line == "":
            if data:
                value = "\n".join(data)
                data = []
                yield value
            continue
        field, _, value = line.partition(":")
        if field != "data":
            continue
        if value.startswith(" "):
            value = value[1:]
        data.append(value)
    # Dispatch requires a blank line, including for the last event.
