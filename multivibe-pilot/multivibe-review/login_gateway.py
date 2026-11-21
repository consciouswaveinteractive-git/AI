"""Login-only loopback gateway. Inference deliberately unavailable."""
import hashlib,hmac,json,os,pathlib,secrets,urllib.request,urllib.error
from urllib.parse import urlsplit
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from http.cookies import SimpleCookie

DATA=pathlib.Path(os.environ['LOCALAPPDATA'])/'MultiVibe-Codex-Pilot'
KEY=json.loads((DATA/'local-keys.json').read_text())['admin']
SESSION=hmac.new(KEY.encode(),b'login-pilot-session',hashlib.sha256).hexdigest()
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,status,body,headers=None):
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store')
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(json.dumps(body).encode())
    def authenticated(self):
        cookie=SimpleCookie()
        try: cookie.load(self.headers.get('Cookie',''))
        except Exception: return False
        value=cookie.get('mv_pilot_session')
        return bool(value and secrets.compare_digest(value.value,SESSION))
    def dispatch(self):
        if self.headers.get('Host','') not in ('localhost:1455','127.0.0.1:1455'):
            return self.reply(403,{'error':'invalid local host'})
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://localhost:1455','http://127.0.0.1:1455'):
            return self.reply(403,{'error':'invalid origin'})
        body=self.rfile.read(int(self.headers.get('Content-Length',0)))
        if self.command=='GET' and urlsplit(self.path).path in ('/','/auth/callback'):
            page=pathlib.Path(__file__).with_name('login.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.end_headers(); self.wfile.write(page); return
        if self.path=='/admin/session':
            if self.command=='GET': return self.reply(200,{'authenticated':self.authenticated()})
            if self.command=='DELETE': return self.reply(200,{'ok':True},{'Set-Cookie':'mv_pilot_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0'})
            try: token=json.loads(body).get('token','')
            except Exception: token=''
            if not isinstance(token,str) or not secrets.compare_digest(token,KEY):
                return self.reply(401,{'error':'unauthorized'})
            return self.reply(200,{'ok':True,'authenticated':True},{'Set-Cookie':f'mv_pilot_session={SESSION}; Path=/; HttpOnly; SameSite=Strict'})
        if self.path.startswith(('/v1','/responses','/chat/completions','/models','/internal')):
            return self.reply(503,{'error':'Login pilot only; inference is not enabled.'})
        if self.path.startswith('/admin') and not self.authenticated():
            return self.reply(401,{'error':'unauthorized'})
        headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length','cookie','authorization','x-admin-token')}
        if self.path.startswith('/admin'): headers['x-admin-token']=KEY
        request=urllib.request.Request('http://127.0.0.1:1456'+self.path,data=body if self.command not in ('GET','HEAD') else None,headers=headers,method=self.command)
        try: response=urllib.request.urlopen(request,timeout=30)
        except urllib.error.HTTPError as error: response=error
        except Exception: return self.reply(502,{'error':'Local control plane unavailable'})
        self.send_response(response.status)
        for k,v in response.headers.items():
            if k.lower() not in ('transfer-encoding','connection','content-length','set-cookie'): self.send_header(k,v)
        self.end_headers()
        if self.command!='HEAD': self.wfile.write(response.read())
    do_GET=dispatch; do_POST=dispatch; do_DELETE=dispatch; do_PUT=dispatch; do_PATCH=dispatch; do_HEAD=dispatch
(DATA/'login-gateway.pid').write_text(str(os.getpid()))
ThreadingHTTPServer(('127.0.0.1',1455),Handler).serve_forever()
