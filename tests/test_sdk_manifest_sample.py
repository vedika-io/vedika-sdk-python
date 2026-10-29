"""Mocked-contract sample test for the Python Vastu SDK.

The script-side ``scripts/sdk/sdk_manifest_validator.py`` proves every
JS / Python / OpenAPI vastu operation aligns by string identity. This
file proves a representative sample of them actually compiles into the
right HTTP method, URL path, body, and idempotency header on the wire
when the SDK dispatches them.

The fixture is a small cross-section kept under
``tests/fixtures/sdk_mock_vastu_contracts.json``. We stub
``VedikaClient._request`` (the same pattern the existing
``test_vastu_rules.py`` uses) and assert the dispatch arguments match
the contract. No network calls, no real API keys, no secret material.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from reference_fixtures import reference_path


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = reference_path("tests/fixtures/sdk_mock_vastu_contracts.json", "sdk-vastu-contracts.json")


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _sdk_modules():
    """Lazy import of the in-tree Python SDK.

    Done inside a function so the import order does not need a lint
    suppression and so the test never holds onto a stale module copy
    between runs.
    """
    repo_path = str(Path(__file__).resolve().parents[1])
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)
    import vedika.client as _client
    return _client.VastuOperation, _client.VedikaClient


class MockedContractSampleTests(unittest.TestCase):
    """One test per fixture entry keeps failures granular and readable."""

    def setUp(self) -> None:
        fixture = _load_fixture()
        self.entries = fixture["entries"]
        self.assertTrue(self.entries, "fixture has no entries")

    def _invoke(self, entry: dict) -> tuple[str, str, dict, object]:
        """Build a VedikaClient, stub _request, run the fixture's call,
        and return the dispatched (method, path, body-or-params, header)
        tuple as captured by the stub. ``header`` is the idempotency_key
        value (or None).
        """
        VastuOperation, VedikaClient = _sdk_modules()
        client = VedikaClient(api_key="vk_test_sample")
        captured = MagicMock(return_value={"success": True})
        setattr(client, "_request", captured)

        method_name = entry["call"]["method_name"]
        kwargs = entry["call"]["kwargs"]
        getattr(client, method_name)(**kwargs)

        # The stub captures positional then keyword args. The SDK's
        # typed methods call ``_request(method, path, data=..., ...)``
        # or ``_request(method, path, params=..., ...)``.
        self.assertTrue(captured.call_args, msg=f"no _request call for {method_name}")
        call = captured.call_args
        return call.args[0], call.args[1], call.kwargs, captured

    def test_fixture_entries_have_unique_labels(self) -> None:
        labels = [e["label"] for e in self.entries]
        self.assertEqual(len(labels), len(set(labels)), msg="fixture labels collide")

    def test_every_entry_references_a_registered_operation(self) -> None:
        VastuOperation, _VedikaClient = _sdk_modules()
        registered = {v.value for v in VastuOperation}
        for entry in self.entries:
            with self.subTest(entry=entry["label"]):
                self.assertIn(entry["operation"], registered,
                              msg=f"unknown operation {entry['operation']!r}")

    def test_every_entry_method_matches_contract(self) -> None:
        VastuOperation, VedikaClient = _sdk_modules()
        import vedika.client as _client
        contracts = _client._VASTU_OPERATION_CONTRACTS
        for entry in self.entries:
            contract = contracts.get(entry["operation"])
            self.assertIsNotNone(contract, msg=f"no contract for {entry['operation']}")
            with self.subTest(entry=entry["label"]):
                self.assertEqual(contract["method"], entry["method"],
                                 msg="fixture method does not match contract method")

    def _run_entry(self, entry: dict) -> None:
        method, path, kwargs, captured = self._invoke(entry)
        with self.subTest(entry=entry["label"]):
            self.assertEqual(method, entry["method"])
            self.assertEqual(path, entry["expected_path"])
            self.assertEqual(
                kwargs.get("idempotency_key"),
                entry["expected_idempotency_key"],
            )
            # Body delivery: POST uses ``data=``; GET may pass ``params=`` or
            # omit them entirely when the call carries no body.
            if entry["method"] == "POST":
                self.assertIn("data", kwargs, msg="POST should pass data=")
                self.assertNotIn("params", kwargs, msg="POST should not pass params=")
            else:
                self.assertNotIn("data", kwargs, msg="GET should not pass data=")

    def test_rules_versions_get(self) -> None:
        e = next(e for e in self.entries if e["label"] == "rules_versions_get_no_body")
        self._run_entry(e)

    def test_compare_versions_post_idempotent(self) -> None:
        e = next(e for e in self.entries if e["label"] == "compare_versions_post_with_idempotency")
        self._run_entry(e)

    def test_reference_directions_8_get(self) -> None:
        e = next(e for e in self.entries if e["label"] == "reference_directions_8_get")
        self._run_entry(e)

    def test_reference_mandala_9_zone_get(self) -> None:
        e = next(e for e in self.entries if e["label"] == "reference_mandala_9_zone_get")
        self._run_entry(e)

    def test_mandala_project_81_pada_post(self) -> None:
        e = next(e for e in self.entries if e["label"] == "mandala_project_81_pada_post")
        self._run_entry(e)

    def test_receipt_verify_post_no_idempotency(self) -> None:
        e = next(e for e in self.entries if e["label"] == "receipt_verify_post_no_idempotency")
        self._run_entry(e)


if __name__ == "__main__":
    unittest.main()