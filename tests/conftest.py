"""Shared fixtures: retries never really sleep, and the waits are recorded."""

import pytest

import vedika.client as client_module


class _FakeTime:
    def __init__(self):
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(seconds)


@pytest.fixture(autouse=True)
def sleeps(monkeypatch):
    """The waits `VedikaClient` asked for, in order. Nothing actually sleeps."""
    fake = _FakeTime()
    monkeypatch.setattr(client_module, "time", fake)
    return fake.sleeps
