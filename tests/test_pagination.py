from unittest.mock import Mock

import pytest
from vedika.client import VedikaClient


def test_conversation_cursor_survives_sdk_boundary():
    client = VedikaClient(api_key='vk_test_local')
    response = {'success': True, 'data': {'nextCursor': 'c1.aabb'}}
    client._request = Mock(return_value=response)
    assert client.get_conversations(limit=25, cursor='c1.1122') == response
    client._request.assert_called_once_with('GET', '/api/v1/conversations', params={'limit': 25, 'cursor': 'c1.1122'})
    client._request.reset_mock()
    for cursor in ['', True, 42, 'x' * 2049]:
        with pytest.raises(ValueError, match='cursor'):
            client.get_conversations(cursor=cursor)
    client._request.assert_not_called()
