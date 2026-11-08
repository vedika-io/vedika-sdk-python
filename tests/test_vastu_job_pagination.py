"""Bounded pagination through the public job-result iterator."""

from typing import Any
from unittest.mock import Mock

import pytest

from vedika import VedikaClient

JOB = "vjob_0123456789abcdef0123456789abcdef"
CYCLES = [("a", "a"), ("a", "b", "a"), ("a", "b", "c", "a"), ("prefix", "a", "b", "a")]


def client_for(
    next_cursors: tuple[str | None, ...], *, empty: bool = False
) -> tuple[VedikaClient, list[str | None]]:
    client = VedikaClient(api_key="vk_test_local")
    calls: list[str | None] = []

    def page(job_id: str, *, cursor: str | None = None) -> dict[str, Any]:
        assert job_id == JOB
        index = len(calls)
        calls.append(cursor)
        if index >= len(next_cursors):
            pytest.fail("iterator requested a page after a repeated cursor")
        item = {"id": f"p{index}", "index": index, "status": 200, "response": {}}
        return {
            "success": True,
            "data": {
                "jobId": JOB,
                "jobStatus": "running",
                "results": [] if empty else [item],
                "nextCursor": next_cursors[index],
            },
        }

    client.vastu_job_results = Mock(side_effect=page)
    return client, calls


@pytest.mark.parametrize("next_cursors", CYCLES)
@pytest.mark.parametrize("empty", [False, True])
def test_stops_before_requesting_any_cursor_again(
    next_cursors: tuple[str, ...], empty: bool
) -> None:
    client, calls = client_for(next_cursors, empty=empty)
    yielded = []
    with pytest.raises(ValueError, match="same results cursor twice"):
        for item in client.vastu_job_result_items(JOB):
            yielded.append(item["index"])
    assert calls == [None, *next_cursors[:-1]]
    assert yielded == ([] if empty else list(range(len(next_cursors))))


def test_follows_an_empty_page_and_preserves_duplicate_item_ids() -> None:
    client = VedikaClient(api_key="vk_test_local")
    item = {"id": "same-id", "index": 0, "status": 200, "response": {}}
    client.vastu_job_results = Mock(
        side_effect=[
            {"data": {"results": [item], "nextCursor": "a"}},
            {"data": {"results": [], "nextCursor": "b"}},
            {"data": {"results": [item], "nextCursor": None}},
        ]
    )
    assert list(client.vastu_job_result_items(JOB)) == [item, item]
    assert client.vastu_job_results.call_count == 3


def test_empty_terminal_page_stops_without_another_request() -> None:
    client, calls = client_for((None,), empty=True)
    assert list(client.vastu_job_result_items(JOB)) == []
    assert calls == [None]


def test_seen_cursors_are_local_to_each_iterator() -> None:
    client = VedikaClient(api_key="vk_test_local")
    pages = [
        {"data": {"results": [], "nextCursor": "a"}},
        {"data": {"results": [], "nextCursor": None}},
    ]
    client.vastu_job_results = Mock(side_effect=pages * 2)
    assert list(client.vastu_job_result_items(JOB)) == []
    assert list(client.vastu_job_result_items(JOB)) == []
    assert client.vastu_job_results.call_count == 4


def test_closing_iteration_does_not_fetch_the_next_page() -> None:
    client, calls = client_for(("a", None))
    stream = client.vastu_job_result_items(JOB)
    assert next(stream)["index"] == 0
    stream.close()
    assert calls == [None]


def test_page_failure_propagates_without_another_request() -> None:
    client = VedikaClient(api_key="vk_test_local")
    error = RuntimeError("page unavailable")
    client.vastu_job_results = Mock(side_effect=error)
    with pytest.raises(RuntimeError) as caught:
        list(client.vastu_job_result_items(JOB))
    assert caught.value is error
    assert client.vastu_job_results.call_count == 1
