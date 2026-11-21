"""Resident MultiVibe edge proxy for OpenCode.

Usage:
  python opencode_proxy.py start   # start container + wait ready
  python opencode_proxy.py status  # check readiness
  python opencode_proxy.py stop    # stop container

This is the daily-use mode: no relay, no simulated 429. Failover happens only
when the real upstream reports a quota error. Never prints credentials.
"""
import json, os, pathlib, subprocess, sys, time, urllib.request

DATA = pathlib.Path(os.environ['LOCALAPPDATA']) / 'MultiVibe-Codex-Pilot'
NAME = 'multivibe-opencode-proxy'
PORT = 14755
SNAPSHOT = DATA / 'opencode-accounts.json'


def keys():
    return json.loads((DATA / 'local-keys.json').read_text())


def snapshot(pin=None):
    store = json.loads((DATA / 'accounts.json').read_text())
    accounts = store.get('accounts', [])
    if pin is not None:
        if not 0 <= pin < len(accounts):
            raise SystemExit(f'account #{pin + 1} does not exist')
        for index, account in enumerate(accounts):
            account['enabled'] = index == pin
    SNAPSHOT.write_text(json.dumps({'accounts': accounts}), encoding='utf-8')
    return [i for i, a in enumerate(accounts)
            if a.get('enabled', True)
            and ((a.get('usage') or {}).get('primary') or {}).get('usedPercent', 100) < 100]


def save_state(pin, enabled):
    (DATA / 'opencode-proxy-state.json').write_text(json.dumps({
        'pinned_account': (pin + 1) if pin is not None else None,
        'accounts_with_quota': [i + 1 for i in enabled],
        'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }, indent=2), encoding='utf-8')


def load_state():
    path = DATA / 'opencode-proxy-state.json'
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def ready():
    try:
        request = urllib.request.Request(
            f'http://127.0.0.1:{PORT}/v1/models',
            headers={'Authorization': 'Bearer ' + keys()['proxy']})
        with urllib.request.urlopen(request, timeout=3) as response:
            return [m['id'] for m in json.load(response).get('data', [])
                    if isinstance(m, dict) and 'id' in m]
    except Exception:
        return None


def start(pin=None):
    env = keys()
    enabled = snapshot(pin)
    if not enabled:
        raise SystemExit('no account with headroom; refresh quota first')
    subprocess.run(['docker', 'rm', '-f', NAME], capture_output=True)
    child_env = os.environ.copy()
    child_env.update({'PROXY_API_KEY': env['proxy'], 'ADMIN_TOKEN': env['admin']})
    args = ['docker', 'run', '-d', '--rm', '--name', NAME,
            '--cpus', '2', '--memory', '2g', '-p', f'127.0.0.1:{PORT}:{PORT}',
            '--mount', 'type=volume,source=multivibe-review-target,target=/target,readonly',
            '--mount', f'type=bind,source={SNAPSHOT},target=/data/accounts.json',
            '-e', 'STORE_PATH=/data/accounts.json', '-e', 'V1_EDGE_HOST=0.0.0.0',
            '-e', f'V1_EDGE_PORT={PORT}', '-e', 'MAX_UPSTREAM_RETRIES=0',
            '-e', 'V1_EDGE_UPSTREAM_TIMEOUT_MS=45000', '-e', 'CODEX_SESSION_AFFINITY=true',
            '-e', 'PROXY_API_KEY', '-e', 'ADMIN_TOKEN',
            'rust:bookworm', '/target/debug/multivibe-v1-edge']
    result = subprocess.run(args, env=child_env, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise SystemExit('docker run failed: ' + (result.stderr or '').strip())
    for _ in range(40):
        ids = ready()
        if ids is not None:
            save_state(pin, enabled)
            print(json.dumps({'status': 'ready', 'port': PORT, 'models': ids,
                              'pinned_account': (pin + 1) if pin is not None else None,
                              'accounts_with_quota': [i + 1 for i in enabled]}, indent=2))
            return
        state = subprocess.run(['docker', 'inspect', '-f', '{{.State.Status}}', NAME],
                               capture_output=True, text=True)
        if 'running' not in state.stdout:
            logs = subprocess.run(['docker', 'logs', '--tail', '20', NAME],
                                  capture_output=True, text=True)
            subprocess.run(['docker', 'rm', '-f', NAME], capture_output=True)
            raise SystemExit('proxy exited: ' + (logs.stderr or logs.stdout))
    subprocess.run(['docker', 'rm', '-f', NAME], capture_output=True)
    raise SystemExit('proxy did not become ready')


def stop():
    subprocess.run(['docker', 'stop', '-t', '3', NAME], capture_output=True, timeout=30)
    print('stopped ' + NAME)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'
    pin = None
    if '--account' in sys.argv:
        try:
            pin = int(sys.argv[sys.argv.index('--account') + 1]) - 1
        except (IndexError, ValueError):
            raise SystemExit('--account needs a 1-based account number')
    if action == 'start':
        start(pin)
    elif action == 'stop':
        stop()
    elif action == 'status':
        ids = ready()
        print(json.dumps({'status': 'ready' if ids else 'stopped', 'models': ids,
                          'state': load_state()}, indent=2))
    else:
        raise SystemExit('usage: opencode_proxy.py start [--account N] | stop | status')


if __name__ == '__main__':
    main()
