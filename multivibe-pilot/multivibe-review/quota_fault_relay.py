"""Authorized pilot requests only; inject one account quota error between turns."""
import json,os,threading,urllib.request,urllib.error
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

# Default is the real upstream; tests may point this at a local mock.
UPSTREAM=os.environ.get('CHATGPT_UPSTREAM','https://chatgpt.com')

class Relay:
    def __init__(self,accounts):
        self.tokens={'Bearer '+a['accessToken']:i for i,a in enumerate(accounts)}
        self.fault=False; self.first=None; self.events=[]
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def dispatch(self):
                index=owner.tokens.get(self.headers.get('Authorization',''))
                if index is None or not self.path.startswith('/backend-api/codex/'):
                    self.send_error(403); return
                body=self.rfile.read(int(self.headers.get('Content-Length',0)))
                inference=self.command=='POST' and self.path.endswith('/responses')
                if inference:
                    if owner.first is None: owner.first=index
                    if owner.fault and index==owner.first:
                        owner.events.append({'account_index':index,'injected_quota':True})
                        data=json.dumps({'error':{'type':'usage_limit_reached','message':'Controlled pilot quota fault'}}).encode()
                        self.send_response(429); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(data); return
                headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length','accept-encoding')}
                req=urllib.request.Request(UPSTREAM+self.path,data=body if self.command=='POST' else None,headers=headers,method=self.command)
                try: response=urllib.request.urlopen(req,timeout=60)
                except urllib.error.HTTPError as e: response=e
                except Exception:
                    self.send_error(502,'Upstream connection failed'); return
                event=None
                if inference:
                    event={'account_index':index,'injected_quota':False,'upstream_status':response.status,
                        'content_type':response.headers.get('Content-Type'),
                        'content_encoding':response.headers.get('Content-Encoding'), 'event_types':{},'output_item_types':[]}
                    owner.events.append(event)
                self.send_response(response.status)
                # Preserve absence too: native ChatGPT SSE can omit this header.
                # Inventing application/json makes the edge buffer SSE as JSON.
                if response.headers.get('Content-Type'):
                    self.send_header('Content-Type',response.headers['Content-Type'])
                # Same for Content-Encoding: relaying encoded bytes without the
                # header (or vice versa) corrupts the stream.
                if response.headers.get('Content-Encoding'):
                    self.send_header('Content-Encoding',response.headers['Content-Encoding'])
                self.end_headers()
                try:
                    pending=b''
                    while True:
                        chunk=response.read1(8192)
                        if not chunk: break
                        if event is not None:
                            pending+=chunk
                            while b'\n' in pending:
                                line,pending=pending.split(b'\n',1)
                                if line.startswith(b'data: '):
                                    try:
                                        parsed=json.loads(line[6:])
                                        kind=parsed.get('type','unknown')
                                        event['event_types'][kind]=event['event_types'].get(kind,0)+1
                                        if kind=='response.output_item.done':
                                            item=parsed.get('item',{})
                                            event['output_item_types'].append({'type':item.get('type'),'role':item.get('role'),'content_types':[c.get('type') for c in item.get('content',[])]})
                                    except (ValueError,AttributeError): pass
                        self.wfile.write(chunk); self.wfile.flush()
                except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
            do_GET=dispatch; do_POST=dispatch
        self.server=ThreadingHTTPServer(('0.0.0.0',14757),Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
    def enable_fault(self): self.fault=True
    def close(self): self.server.shutdown(); self.server.server_close()
