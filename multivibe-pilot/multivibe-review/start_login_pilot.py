"""Start isolated upstream MultiVibe control plane and Rust gateway for user OAuth."""
import json, os, pathlib, secrets, subprocess, urllib.request, time

root = pathlib.Path(__file__).resolve().parent
data = pathlib.Path(os.environ['LOCALAPPDATA']) / 'MultiVibe-Codex-Pilot'
data.mkdir(exist_ok=True)
sid = subprocess.check_output(['whoami','/user','/fo','csv','/nh'],text=True).strip().split(',')[-1].strip('"')
subprocess.run(['icacls',str(data),'/inheritance:r','/grant:r',f'*{sid}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F'],check=True,capture_output=True)
for port in (1455,1456):
    import socket
    sock=socket.socket()
    try: sock.bind(('127.0.0.1',port))
    finally: sock.close()
keys_path=data/'local-keys.json'
if not keys_path.exists():
    keys_path.write_text(json.dumps({k:secrets.token_urlsafe(32) for k in ['admin','proxy','internal']}))
keys=json.loads(keys_path.read_text())
(data/'admin-password.txt').write_text(keys['admin'])
store=data/'accounts.json'
if not store.exists():
    store.write_text(json.dumps({'accounts':[],'settings':{'anonymousUsageSharingEnabled':False}}))
home=data/'isolated-home'; home.mkdir(exist_ok=True)
app=root/'package/multivibe-host_0.2.138_windows_amd64/app'
node=app.parent/'bin/node.exe'
env=os.environ.copy()
for k in list(env):
    if k.startswith(('OAUTH_','OPENAI_','SENTRY_','CODEX_','MULTIVIBE_')): env.pop(k)
env.update({'HOST':'127.0.0.1','PORT':'1456','CONTROL_PLANE_PORT':'1456','V1_EDGE_PORT':'1455',
    'V1_EDGE_BASE_URL':'http://127.0.0.1:1455','V1_EDGE_INTERNAL_JOB_TOKEN':keys['internal'],
    'ADMIN_TOKEN':keys['admin'],'PROXY_API_KEY':keys['proxy'],
    'HOST_HARNESS_HOME_DIRECTORY':str(home),'COMMUNITY_BENCHMARKS_ENABLED':'false',
    'TRACE_INCLUDE_BODY':'false','TRACE_INCLUDE_HEADERS':'false','MODULES_PATH':str(data/'modules'),
    'BUNDLED_SECURITY_MODULE_PATH':str(app/'modules/security')})
paths={'STORE_PATH':'accounts.json','OAUTH_STATE_PATH':'oauth-state.json','TRACE_FILE_PATH':'requests.jsonl',
    'TRACE_STATS_HISTORY_PATH':'stats.jsonl','CODEX_PROJECTS_PATH':'projects.json','JOBS_DB_PATH':'jobs.sqlite',
    'ANONYMOUS_USAGE_STATE_PATH':'anonymous.json','COMMUNITY_BENCHMARKS_STATE_PATH':'community.json'}
env.update({k:str(data/v) for k,v in paths.items()})
out=(data/'control.stdout.log').open('a'); err=(data/'control.stderr.log').open('a')
p=subprocess.Popen([str(node),'dist/server.js'],cwd=app,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
(data/'control.pid').write_text(str(p.pid))
for _ in range(30):
    try:
        urllib.request.urlopen('http://127.0.0.1:1456/health',timeout=1).close(); break
    except Exception:
        if p.poll() is not None: raise RuntimeError('control plane exited; inspect private control.stderr.log')
        time.sleep(.5)
else: raise RuntimeError('control plane not ready')
# Tokens are passed in environment, never command-line arguments or tool output.
docker_env=os.environ.copy()
docker_env.update({'ADMIN_TOKEN':keys['admin'],'PROXY_API_KEY':keys['proxy'],'V1_EDGE_INTERNAL_JOB_TOKEN':keys['internal']})
args=['docker','run','-d','--name','multivibe-login-pilot','--restart','no','--cpus','2','--memory','2g',
    '-p','127.0.0.1:1455:1455','--mount','type=volume,source=multivibe-review-target,target=/target,readonly',
    '--mount',f'type=bind,source={data},target=/data','-e','STORE_PATH=/data/accounts.json',
    '-e','V1_EDGE_HOST=0.0.0.0','-e','V1_EDGE_PORT=1455','-e','NODE_CONTROL_PLANE_URL=http://host.docker.internal:1456',
    '-e','ADMIN_TOKEN','-e','PROXY_API_KEY','-e','V1_EDGE_INTERNAL_JOB_TOKEN','-e','CODEX_SESSION_AFFINITY=true',
    'rust:bookworm','/target/debug/multivibe-v1-edge']
subprocess.run(args,env=docker_env,check=True,capture_output=True,text=True,timeout=30)
for _ in range(30):
    try:
        req=urllib.request.Request('http://127.0.0.1:1455/admin/accounts',headers={'x-admin-token':keys['admin']})
        r=urllib.request.urlopen(req,timeout=3)
        body=json.loads(r.read())
        print('LOGIN_PILOT_READY http://localhost:1455')
        print('PRIVATE_PASSWORD_FILE',data/'admin-password.txt')
        print('Control PID',p.pid)
        print('Accounts API status',r.status)
        break
    except Exception:
        time.sleep(.5)
else: raise RuntimeError('gateway/admin API not ready; services retained for diagnosis')
