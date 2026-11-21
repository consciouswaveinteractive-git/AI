"""Offline check for the relay Content-Type fix. Fake tokens only, no upstream.

Reproduces the previous failure mode: the real ChatGPT SSE response omits
Content-Type. The relay must forward the absence (not invent application/json)
so the Rust edge treats the bytes as a native stream.
"""
import json, threading, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MOCK_PORT = 14758
SSE = (
    'data: {"type":"response.created","response":{"id":"resp-mock","status":"in_progress","output":[]}}\n\n'
    'data: {"type":"response.output_text.delta","delta":"MOCK_ACK"}\n\n'
    'data: {"type":"response.output_item.done","output_index":0,"item":{"id":"msg-mock","type":"message","role":"assistant","status":"completed","content":[{"type":"output_text","text":"MOCK_ACK"}]}}\n\n'
    'data: {"type":"response.completed","response":{"id":"resp-mock","status":"completed","output":[{"type":"message","role":"assistant","content":[{"type":"output_text","text":"MOCK_ACK"}]}]}}\n\n'
).encode()


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.send_response(200)
        # Deliberately no Content-Type on the normal path: this is the bug gate.
        if 'typed' in self.path:
            self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Content-Length', str(len(SSE)))
        self.end_headers()
        self.wfile.write(SSE)


mock = ThreadingHTTPServer(('127.0.0.1', MOCK_PORT), Mock)
threading.Thread(target=mock.serve_forever, daemon=True).start()

import quota_fault_relay as qfr  # noqa: E402  (after env-independent mock is up)
qfr.UPSTREAM = f'http://127.0.0.1:{MOCK_PORT}'
relay = qfr.Relay([{'accessToken': 'fake-a'}, {'accessToken': 'fake-b'}])
base = 'http://127.0.0.1:14757/backend-api/codex/responses'


def call(token, path=base, body=b'{"stream":true}'):
    req = urllib.request.Request(path, data=body,
                                 headers={'Authorization': 'Bearer ' + token,
                                          'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.headers.get('Content-Type'), response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get('Content-Type'), error.read()


report = {}
try:
    status, content_type, body = call('fake-a')
    assert status == 200 and content_type is None, (status, content_type)
    assert b'response.completed' in body and b'MOCK_ACK' in body
    first = relay.events[0]
    assert first['content_type'] is None and first['upstream_status'] == 200
    assert first['event_types'].get('response.output_text.delta') == 1
    assert first['event_types'].get('response.completed') == 1
    assert first['output_item_types'] == [
        {'type': 'message', 'role': 'assistant', 'content_types': ['output_text']}
    ]
    report['absent_content_type_preserved'] = True

    relay.enable_fault()
    status, _, _ = call('fake-a')
    assert status == 429, status
    assert relay.events[1] == {'account_index': 0, 'injected_quota': True}
    report['injected_quota_429'] = True

    status, content_type, body = call('fake-b')
    assert status == 200 and content_type is None and b'MOCK_ACK' in body
    report['failover_to_second_account'] = True

    status, content_type, body = call('fake-b', path=base.replace('/responses', '/typed/responses'))
    assert status == 200 and content_type == 'text/event-stream'
    report['present_content_type_forwarded'] = True

    status, _, _ = call('not-authorised')
    assert status == 403
    report['unknown_bearer_rejected'] = True
finally:
    relay.close()
    mock.shutdown()

report['passed'] = True
print(json.dumps(report, indent=2))
