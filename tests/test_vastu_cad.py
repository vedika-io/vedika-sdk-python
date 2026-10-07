import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from vedika.client import VedikaClient

@pytest.mark.parametrize('tail,method,body', [
    ('import-dxf', 'vastu_plan_import_dxf', {'dxf':'synthetic','maxChargeUsd':'0.01'}),
    ('export-ifc', 'vastu_plan_export_ifc', {'plan':{},'outputUnits':'mm','maxChargeUsd':'0.02'}),
    ('convert-units', 'vastu_plan_convert_units', {'plan':{},'inputUnits':'m','outputUnits':'ft'}),
    ('export-dxf', 'vastu_plan_export_dxf', {'plan':{},'maxChargeUsd':'0.02'}),
    ('import-ifc', 'vastu_plan_import_ifc', {'ifc':'synthetic','maxChargeUsd':'0.03'}),
])
def test_budget_and_real_rust_response(tail, method, body):
    root=Path(__file__).resolve().parents[3]
    corpus_path=root/'web/vedika-public/js/catalog/vastu-sandbox-demos.json'
    if not corpus_path.is_file():
        pytest.skip("needs the monorepo's recorded sandbox corpus (not in the standalone SDK repo)")
    corpus=json.loads(corpus_path.read_text())
    recorded=corpus['demos']['vastu__plan_'+tail.replace('-','_')]
    client=VedikaClient(api_key='vk_test')
    client._request=MagicMock(return_value=recorded)
    result=getattr(client,method)(body,idempotency_key='cad-retry')
    args,kwargs=client._request.call_args
    assert result==recorded
    assert body in args or body in kwargs.values()
    assert 'cad-retry' in str(args)+str(kwargs)
