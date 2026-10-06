import unittest
from unittest.mock import MagicMock
from vedika.client import VedikaClient

class VastuRulesTransport(unittest.TestCase):
    def test_version_and_receipt_transport(self):
        client = VedikaClient(api_key="vk_test")
        client._request = MagicMock(return_value={"success": True})
        body = {"fromVersion": "vastu-rules-2026-09-23", "toVersion": "vastu-rules-2026-10-04", "input": {"rooms": [{"name": "bedroom", "zone": "SW"}]}}
        client.vastu_compare_versions(body, idempotency_key="comparison-retry")
        client._request.assert_called_with("POST", "/v2/astrology/vastu/plan/compare-versions", data=body, idempotency_key="comparison-retry")
        client.vastu_rule_versions()
        client._request.assert_called_with("GET", "/v2/astrology/vastu/rules/versions")
        token = {"token": "test.receipt.signature", "input": {"rooms": []}}
        client.vastu_verify_receipt(token)
        client._request.assert_called_with("POST", "/v2/astrology/vastu/receipt/verify", data=token)
