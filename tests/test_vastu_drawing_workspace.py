from unittest.mock import MagicMock
import pytest
from vedika import VedikaClient, VastuDrawingSheetRequest, VastuWorkspaceRequest

def test_drawing_path_idempotency_and_billing_envelope():
    client=VedikaClient(api_key="test-key")
    response={"success":True,"data":{"html":"<html>synthetic sheet</html>"},"billing":{"chargedCents":1}}
    client._request=MagicMock(return_value=response)
    body={"plan":{},"titleBlock":{"project":"Synthetic","architect":"Surveyor"}}
    assert client.vastu_drawing_sheet(body,idempotency_key="retained-drawing")==response
    client._request.assert_called_once_with("POST","/v2/vastu/report/drawing-sheet",data=body,idempotency_key="retained-drawing")

@pytest.mark.parametrize("op",["properties","jobs","get","list","reset","webhook","report"])
def test_workspace_isolated_root_and_zero_charge(op):
    client=VedikaClient(api_key="test-key")
    response={"success":True,"data":{},"mode":"sandbox","billing":{"chargedCents":0}}
    client._request=MagicMock(return_value=response)
    assert client.vastu_workspace(op,{})==response
    client._request.assert_called_once_with("POST",f"/sandbox/v2/vastu/workspace/{op}",data={})

def test_workspace_operation_cannot_escape_prefix():
    client=VedikaClient(api_key="test-key");client._request=MagicMock()
    with pytest.raises(ValueError):client.vastu_workspace("../../properties/get",{})
    client._request.assert_not_called()
