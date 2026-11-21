"""Isolated real Codex client -> Linux proxy -> mock ChatGPT. No real credentials."""
import json, os, pathlib, subprocess, sys, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Real ChatGPT SSE sometimes omits Content-Type (see quota_fault_relay.py fix).
# This flag reproduces that upstream and proves the client still gets the reply.
OMIT_CONTENT_TYPE = '--omit-content-type' in sys.argv

ROOT = pathlib.Path(__file__).resolve().parent
RUN = ROOT / ('client-run-' + time.strftime('%Y%m%d-%H%M%S'))
RUN.mkdir()
HOME = RUN / 'codex-home'; HOME.mkdir()
WORK = RUN / 'empty-workspace'; WORK.mkdir()
DATA = RUN / 'mock-data'; DATA.mkdir()
CODEX = pathlib.Path(os.environ['USERPROFILE']) / '.vscode/extensions/openai.chatgpt-26.1021.22027-win32-x64/bin/windows-x86_64/codex.exe'
seen = []; results = []; fail_a = False

class Mock(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        data = json.dumps({'models':[{'slug':'gpt-5.6-sol','display_name':'Mock','context_window':128000}]}).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))
        token = self.headers.get('Authorization','')
        seen.append({'token':token, 'body':body})
        if fail_a and token == 'Bearer fake-a':
            data=json.dumps({'error':{'type':'usage_limit_reached','message':'mock quota exhausted'}}).encode()
            self.send_response(429); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(data); return
        text='MOCK_ACK_729'
        item={'id':'msg-mock','type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':text,'annotations':[]}]}
        response={'id':'resp-mock','object':'response','status':'completed','model':'gpt-5.6-sol','output':[item],'usage':{'input_tokens':1,'output_tokens':1,'total_tokens':2,'input_tokens_details':{'cached_tokens':0},'output_tokens_details':{'reasoning_tokens':0}}}
        events=[{'type':'response.created','response':{**response,'status':'in_progress','output':[]}}, {'type':'response.output_item.added','output_index':0,'item':{**item,'status':'in_progress','content':[]}}, {'type':'response.output_item.done','output_index':0,'item':item}, {'type':'response.completed','response':response}]
        data=''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode()
        self.send_response(200)
        if not OMIT_CONTENT_TYPE: self.send_header('Content-Type','text/event-stream')
        self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)

server=ThreadingHTTPServer(('0.0.0.0',14757),Mock)
threading.Thread(target=server.serve_forever,daemon=True).start()
(DATA/'accounts.json').write_text(json.dumps({'accounts':[{'id':n,'provider':'openai','accessToken':'fake-'+n,'enabled':True,'priority':i} for i,n in enumerate(['a','b'])]}))
(HOME/'config.toml').write_text('''model = "gpt-5.6-sol"
model_provider = "mock_multivibe"
approval_policy = "never"
sandbox_mode = "read-only"
[model_providers.mock_multivibe]
name = "Isolated mock MultiVibe"
base_url = "http://127.0.0.1:14755/v1"
wire_api = "responses"
experimental_bearer_token = "fake-local-key"
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
''',encoding='utf-8')
args=['docker','run','--rm','--name','multivibe-client-acceptance','--cpus','2','--memory','2g','-p','127.0.0.1:14755:14755','--mount','type=volume,source=multivibe-review-target,target=/target,readonly','--mount',f'type=bind,source={DATA},target=/data','-e','V1_EDGE_HOST=0.0.0.0','-e','V1_EDGE_PORT=14755','-e','CHATGPT_BASE_URL=http://host.docker.internal:14757','-e','STORE_PATH=/data/accounts.json','-e','PROXY_API_KEY=fake-local-key','-e','MAX_UPSTREAM_RETRIES=0','-e','CODEX_SESSION_AFFINITY=true','rust:bookworm','/target/debug/multivibe-v1-edge']
env=os.environ.copy()
for key in list(env):
    if key.startswith(('OPENAI_','CODEX_','OAUTH_')): env.pop(key)
env['CODEX_HOME']=str(HOME)
log=(RUN/'proxy.log').open('w')
proxy=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT)
try:
    for _ in range(60):
        try:
            req=urllib.request.Request('http://127.0.0.1:14755/v1/models',headers={'Authorization':'Bearer fake-local-key'})
            urllib.request.urlopen(req,timeout=1).close(); break
        except Exception:
            if proxy.poll() is not None: raise RuntimeError('proxy exited: '+(RUN/'proxy.log').read_text())
            time.sleep(.5)
    else: raise RuntimeError('proxy not ready')
    def client(label, extra):
        result=subprocess.run([str(CODEX),'exec','--json','--skip-git-repo-check',*extra],cwd=WORK,env=env,capture_output=True,text=True,timeout=60)
        (RUN/(label+'.stdout.jsonl')).write_text(result.stdout,encoding='utf-8')
        (RUN/(label+'.stderr.log')).write_text(result.stderr,encoding='utf-8')
        results.append({'turn':label,'exit':result.returncode})
        assert result.returncode==0, result.stderr[-2000:]
        assert 'MOCK_ACK_729' in result.stdout
        return [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    events=client('first',['Remember NONCE_CLIENT_729. Do not use tools.'])
    thread=next(e['thread_id'] for e in events if e.get('type')=='thread.started')
    fail_a=True
    client('second',['resume',thread,'Continue. What nonce did I provide? Do not use tools.'])
    assert len(seen)==3, f'unexpected request count {len(seen)}'
    assert [r['token'] for r in seen]==['Bearer fake-a','Bearer fake-a','Bearer fake-b']
    assert seen[1]['body']['input']==seen[2]['body']['input']
    assert 'NONCE_CLIENT_729' in json.dumps(seen[2]['body']['input'])
    assert 'MOCK_ACK_729' in json.dumps(seen[2]['body']['input'])
    results.append({'same_thread':True,'quota_failover':'a-to-b','prior_user_and_assistant_history_preserved':True,'mock_only':True,'upstream_content_type':'absent' if OMIT_CONTENT_TYPE else 'text/event-stream'})
except Exception as exc:
    results.append({'error':str(exc)})
    raise
finally:
    (RUN/'upstream-requests.json').write_text(json.dumps(seen,indent=2),encoding='utf-8')
    (RUN/'result.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    subprocess.run(['docker','stop','-t','3','multivibe-client-acceptance'],capture_output=True,timeout=20)
    try: proxy.wait(timeout=10)
    except subprocess.TimeoutExpired: proxy.terminate()
    server.shutdown(); log.close()
    print(RUN)
    print(json.dumps(results,indent=2))
