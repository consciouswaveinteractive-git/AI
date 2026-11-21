"""Long-lived isolated proxy for the VS Code Codex extension pilot.

Starts the Rust edge in Docker (port 14755) plus the quota-fault relay (14757),
and keeps running until a stop file appears or the timeout expires. The relay
only injects a simulated 429 after an "arm" file is created, so the operator
can arm it exactly before the second prompt. Never prints credentials.
"""
import json, os, pathlib, subprocess, sys, threading, time, urllib.request

DATA = pathlib.Path(os.environ['LOCALAPPDATA']) / 'MultiVibe-Codex-Pilot'
ROOT = pathlib.Path(__file__).resolve().parent
KEYS = json.loads((DATA / 'local-keys.json').read_text())
STORE = json.loads((DATA / 'accounts.json').read_text())
FAILOVER = '--failover' in sys.argv
TIMEOUT_MIN = 60
for index, arg in enumerate(sys.argv):
    if arg == '--timeout-min' and index + 1 < len(sys.argv):
        TIMEOUT_MIN = int(sys.argv[index + 1])

accounts = STORE.get('accounts', [])
for account in accounts:
    usage = account.get('usage') or {}
    primary = (usage.get('primary') or {}).get('usedPercent', 100)
    account['enabled'] = bool(account.get('enabled', True) and primary < (100 if FAILOVER else 95))

state_dir = DATA / ('vscode-pilot-' + time.strftime('%Y%m%d-%H%M%S'))
state_dir.mkdir()
arm_file = state_dir / 'arm-failover'
stop_file = state_dir / 'stop'
events_file = state_dir / 'events.json'
meta_file = state_dir / 'meta.json'
log = (state_dir / 'proxy.log').open('w')

relay = None
proc = None
stop = threading.Event()


def wait_ready():
    for _ in range(60):
        try:
            request = urllib.request.Request(
                'http://127.0.0.1:14755/v1/models',
                headers={'Authorization': 'Bearer ' + KEYS['proxy']})
            with urllib.request.urlopen(request, timeout=3) as response:
                return json.load(response)
        except Exception:
            if proc is not None and proc.poll() is not None:
                raise RuntimeError('proxy exited; inspect ' + str(state_dir / 'proxy.log'))
            stop.wait(0.5)
    raise RuntimeError('proxy did not become ready')


report = {'state_dir': str(state_dir), 'live_codex_config_changed': False}
try:
    if not any(a['enabled'] for a in accounts):
        raise RuntimeError('no account with headroom')

    if FAILOVER:
        from quota_fault_relay import Relay
        relay = Relay(accounts)

    args = ['docker', 'run', '--rm', '-i', '--name', 'multivibe-vscode-proxy',
            '--cpus', '2', '--memory', '2g', '-p', '127.0.0.1:14755:14755',
            '--mount', 'type=volume,source=multivibe-review-target,target=/target,readonly',
            '--tmpfs', '/data:rw,noexec,nosuid,size=32m',
            '-e', 'STORE_PATH=/data/accounts.json', '-e', 'V1_EDGE_HOST=0.0.0.0',
            '-e', 'V1_EDGE_PORT=14755', '-e', 'MAX_UPSTREAM_RETRIES=0',
            '-e', 'V1_EDGE_UPSTREAM_TIMEOUT_MS=45000', '-e', 'CODEX_SESSION_AFFINITY=true']
    if relay:
        args[args.index('--tmpfs'):args.index('--tmpfs')] = [
            '-e', 'CHATGPT_BASE_URL=http://host.docker.internal:14757']
    env = os.environ.copy()
    env.update({'PROXY_API_KEY': KEYS['proxy'], 'ADMIN_TOKEN': KEYS['admin']})
    args += ['-e', 'PROXY_API_KEY', '-e', 'ADMIN_TOKEN', 'rust:bookworm', 'bash', '-c',
             'umask 077; cat > /data/accounts.json; exec /target/debug/multivibe-v1-edge']
    proc = subprocess.Popen(args, env=env, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
    proc.stdin.write(json.dumps({'accounts': accounts}).encode())
    proc.stdin.close()

    models = wait_ready()
    ids = [m['id'] for m in models.get('data', []) if isinstance(m, dict) and 'id' in m]
    report['model_ids'] = ids
    meta_file.write_text(json.dumps({
        'state_dir': str(state_dir), 'arm_file': str(arm_file), 'stop_file': str(stop_file),
        'proxy': 'http://127.0.0.1:14755/v1', 'model_ids': ids,
        'enabled_accounts': [i for i, a in enumerate(accounts) if a['enabled']],
    }, indent=2), encoding='utf-8')

    def watch():
        armed = False
        last_dump = 0.0
        while not stop.is_set():
            if not armed and arm_file.exists():
                relay.enable_fault()
                armed = True
                report['armed_at'] = time.time()
            if time.time() - last_dump > 3:
                events_file.write_text(json.dumps({
                    'armed': armed, 'events': relay.events if relay else []
                }, indent=2), encoding='utf-8')
                last_dump = time.time()
            if stop_file.exists():
                stop.set()
                break
            stop.wait(1)

    print('VSCODE_PROXY_READY ' + json.dumps({
        'state_dir': str(state_dir), 'arm_file': str(arm_file), 'stop_file': str(stop_file),
        'models': ids, 'enabled_accounts': [i for i, a in enumerate(accounts) if a['enabled']],
    }), flush=True)
    threading.Thread(target=watch, daemon=True).start()
    stop.wait(TIMEOUT_MIN * 60)
except Exception as exc:
    report['error'] = type(exc).__name__ + ': ' + str(exc)
    raise
finally:
    stop.set()
    if relay:
        report['events'] = relay.events
        try:
            relay.close()
        except Exception:
            pass
    if proc is not None:
        subprocess.run(['docker', 'stop', '-t', '3', 'multivibe-vscode-proxy'],
                       capture_output=True, timeout=20)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
    (state_dir / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    log.close()
    print('VSCODE_PROXY_STOPPED ' + str(state_dir), flush=True)
