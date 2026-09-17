"""HTTP response decoding, independent of retry and paid request behavior."""
import json
from unittest.mock import Mock

import pytest
import requests
from vedika import VedikaClient
from vedika.exceptions import VedikaAPIError, SubscriptionExpiredError, InsufficientCreditsError, ValidationError


@pytest.mark.parametrize("status,body,kind,message", [
    (400, {"error":"requirements.floors is required"}, VedikaAPIError, "requirements.floors is required"),
    (422, {"error":{"message":"Invalid room zone"}}, ValidationError, "Invalid room zone"),
    (402, {"code":"SUBSCRIPTION_EXPIRED","error":"Renew subscription"}, SubscriptionExpiredError, "Renew subscription"),
    (402, [], InsufficientCreditsError, "Payment required"),
    (500, {"error":{"privateDiagnostic":"DO_NOT_EXPOSE"}}, VedikaAPIError, "API request failed"),
    (503, "proxy returned nonobject JSON", VedikaAPIError, "API request failed"),
])
def test_http_error_shapes_keep_sdk_exception_and_public_message(status,body,kind,message):
    client=VedikaClient(api_key="vk_test_LOCAL_SECRET",max_retries=0)
    response=requests.Response();response.status_code=status;response._content=json.dumps(body).encode()
    client.session.request=Mock(return_value=response)
    with pytest.raises(kind) as error:client._request("POST","/v2/astrology/vastu/plan/from-requirements",{})
    assert error.value.status_code==status
    assert message in str(error.value)
    assert "DO_NOT_EXPOSE" not in str(error.value)


def test_html_http_error_keeps_status_without_raw_body():
    client=VedikaClient(api_key="vk_test_LOCAL_SECRET",max_retries=0)
    response=requests.Response();response.status_code=502;response._content=b"<html>PRIVATE_PROXY_DIAGNOSTIC</html>"
    client.session.request=Mock(return_value=response)
    with pytest.raises(VedikaAPIError) as error:client._request("GET","/health")
    assert error.value.status_code==502
    assert "PRIVATE_PROXY_DIAGNOSTIC" not in str(error.value)


def test_server_error_redacts_the_callers_key():
    client=VedikaClient(api_key="vk_test_LOCAL_SECRET",max_retries=0)
    response=requests.Response();response.status_code=400;response._content=b'{"error":"Invalid vk_test_LOCAL_SECRET"}'
    client.session.request=Mock(return_value=response)
    with pytest.raises(VedikaAPIError) as error:client._request("GET","/health")
    assert "vk_test_LOCAL_SECRET" not in str(error.value)
    assert "[REDACTED]" in str(error.value)


def test_transport_errors_do_not_echo_request_secrets():
    client=VedikaClient(api_key="vk_test_LOCAL_SECRET",max_retries=0)
    client.session.request=Mock(side_effect=requests.ConnectionError("url?key=vk_test_LOCAL_SECRET"))
    with pytest.raises(VedikaAPIError) as error:client._request("GET","/health")
    assert "vk_test_LOCAL_SECRET" not in str(error.value)
