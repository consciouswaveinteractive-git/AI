"""One bounded real model request, isolated proxy; never print credentials."""
import os,pathlib,json,subprocess,time,urllib.request,urllib.error,sys
p=pathlib.Path(os.environ['LOCALAPPDATA'])/'MultiVibe-Codex-Pilot'
root=pathlib.Path(__file__).resolve().parent
keys=json.loads((p/'local-keys.json').read_text())
store=json.loads((p/'accounts.json').read_text())
accounts=store.get('accounts',[])
failover='--failover' in sys.argv
# Keep all account snapshots, route only to accounts that have verified headroom.
for a in accounts:
    a['enabled']=bool(a.get('enabled',True) and (a.get('usage') or {}).get('primary',{}).get('usedPercent',100)<(100 if failover else 95))
if not any(a['enabled'] for a in accounts): raise RuntimeError('No account with >=5% headroom')
relay=None
if failover:
    if sum(a['enabled'] for a in accounts)<2: raise RuntimeError('Need two real accounts with available quota')
    from quota_fault_relay import Relay
    relay=Relay(accounts)
env=os.environ.copy()
env.update({'PROXY_API_KEY':keys['proxy'],'ADMIN_TOKEN':keys['admin']})
args=['docker','run','--rm','-i','--name','multivibe-real-smoke','--cpus','2','--memory','2g',
    '-p','127.0.0.1:14755:14755','--mount','type=volume,source=multivibe-review-target,target=/target,readonly',
    '--tmpfs','/data:rw,noexec,nosuid,size=32m','-e','PROXY_API_KEY','-e','ADMIN_TOKEN',
    '-e','STORE_PATH=/data/accounts.json','-e','V1_EDGE_HOST=0.0.0.0','-e','V1_EDGE_PORT=14755',
    '-e','MAX_UPSTREAM_RETRIES=0','-e','V1_EDGE_UPSTREAM_TIMEOUT_MS=45000',
    '-e','CODEX_SESSION_AFFINITY=true',
    'rust:bookworm','bash','-c','umask 077; cat > /data/accounts.json; exec /target/debug/multivibe-v1-edge']
log=(p/'real-smoke-proxy.log').open('w')
if relay:
    args[args.index('rust:bookworm'):args.index('rust:bookworm')]=['-e','CHATGPT_BASE_URL=http://host.docker.internal:14757']
proc=subprocess.Popen(args,env=env,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT)
report={}
try:
    proc.stdin.write(json.dumps({'accounts':accounts}).encode()); proc.stdin.close()
    for _ in range(40):
        try:
            req=urllib.request.Request('http://127.0.0.1:14755/v1/models',headers={'Authorization':'Bearer '+keys['proxy']})
            with urllib.request.urlopen(req,timeout=3) as r: models=json.load(r)
            break
        except Exception:
            if proc.poll() is not None: raise RuntimeError('proxy exited; private log retained')
            time.sleep(.5)
    else: raise RuntimeError('proxy did not become ready')
    ids=[m['id'] for m in models.get('data',[]) if isinstance(m,dict) and 'id' in m]
    preferred=['gpt-6.1-sol','gpt-6-sol','gpt-5.6-sol','gpt-5.3-codex']
    model=next((m for m in preferred if m in ids),None)
    if not model: raise RuntimeError('No approved model found; available model names: '+', '.join(ids[:20]))
    if '--client' in sys.argv:
        from real_client_probe import probe
        report=probe(p,model,keys['proxy'],relay.enable_fault if relay else None)
        if relay:
            report['controlled_fault_events']=relay.events
            report['natural_quota_exhaustion']=False
            good=[e for e in relay.events if e.get('upstream_status')==200]
            assert len(good)==2 and good[0]['account_index']!=good[1]['account_index'], 'Two successful turns did not use different accounts'
            assert any(e.get('injected_quota') for e in relay.events), 'Quota fault was not observed'
        raise SystemExit(0)
    payload={'model':model,'instructions':'This is a connectivity test. Do not use tools. Reply with exactly PILOT_OK_729.',
        'input':[{'role':'user','content':'Reply with exactly PILOT_OK_729.'}],'stream':True,'reasoning':{'effort':'low'}}
    req=urllib.request.Request('http://127.0.0.1:14755/v1/responses',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+keys['proxy'],'Content-Type':'application/json'})
    completed=False; text=''; failed=False
    with urllib.request.urlopen(req,timeout=60) as r:
        for line in r:
            if not line.startswith(b'data: '): continue
            data=line[6:].strip()
            if data==b'[DONE]': continue
            try: event=json.loads(data)
            except Exception: continue
            if event.get('type')=='response.output_text.delta': text+=event.get('delta','')
            if event.get('type')=='response.completed':
                completed=True
                response=event.get('response',{})
                if not text:
                    text=''.join(c.get('text','') for item in response.get('output',[]) for c in item.get('content',[]) if c.get('type')=='output_text')
            if event.get('type') in ('response.failed','error'): failed=True
    report={'model':model,'completed':completed,'failed_event':failed,'exact_expected_text':text.strip()=='PILOT_OK_729','response_text':text[:100],'real_request':True,'live_codex_config_changed':False}
    assert completed and not failed and report['exact_expected_text'], 'real model did not meet smoke criteria'
except urllib.error.HTTPError as exc:
    report={'http_status':exc.code,'passed':False,'error':'upstream HTTP error; no credential response logged'}
    raise
except Exception as exc:
    report={'passed':False,'error_type':type(exc).__name__,'controlled_fault_events':relay.events if relay else [],'natural_quota_exhaustion':False if relay else None,'live_codex_config_changed':False}
    raise
finally:
    result_name='real-failover-result.json' if failover else 'real-client-result.json' if '--client' in sys.argv else 'real-smoke-result.json'
    (root/result_name).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    subprocess.run(['docker','stop','-t','3','multivibe-real-smoke'],capture_output=True,timeout=20)
    try: proc.wait(timeout=10)
    except subprocess.TimeoutExpired: proc.terminate()
    log.close()
    if relay: relay.close()
