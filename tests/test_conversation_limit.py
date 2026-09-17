"""Bounded conversation lists use the real HTTP transport without invented pages."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from unittest.mock import Mock

import pytest
from vedika.client import VedikaClient


def test_conversation_limit_reaches_the_route_without_extra_pages():
    paths = []
    items = [{'conversationId': f'conv_{i}'} for i in range(120)]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            paths.append(self.path)
            limit = int(parse_qs(urlparse(self.path).query).get('limit', [10])[0])
            conversations = items[:limit]
            body = json.dumps({'success': True, 'data': {'conversations': conversations, 'count': len(conversations)}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = VedikaClient(api_key='vk_test_local', base_url=f'http://127.0.0.1:{server.server_port}')
        assert client.get_conversations()['data']['count'] == 10
        assert client.get_conversations(limit=100)['data']['count'] == 100
        assert client.get_conversations(limit=1)['data']['conversations'] == items[:1]
        assert paths == ['/api/v1/conversations', '/api/v1/conversations?limit=100', '/api/v1/conversations?limit=1']
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_invalid_limits_fail_before_transport():
    client = VedikaClient(api_key='vk_test_local')
    client._request = Mock(return_value={})
    for limit in [0, -1, 101, 1.5, float('nan'), float('inf'), True, '10']:
        with pytest.raises(ValueError, match='limit must be an integer between 1 and 100'):
            client.get_conversations(limit=limit)
    client._request.assert_not_called()
