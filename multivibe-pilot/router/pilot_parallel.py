"""Parallel GPT-6 pilot: separate ports/state; never stop the original service."""
import base64
import json
import os
import pathlib
import subprocess
import threading
import time
import urllib.request

DATA = pathlib.Path(os.environ['LOCALAPPDATA']) / 'MultiVibe-Codex-Pilot'
os.environ['PILOT_ROUTER_PORT'] = '14767'
os.environ['PILOT_STATE_PATH'] = str(DATA / 'pilot-gpt6-router-state.json')
os.environ['PILOT_REQUESTS_PATH'] = str(DATA / 'pilot-gpt6-requests.jsonl')
os.environ['PILOT_EVENTS_PATH'] = str(DATA / 'pilot-gpt6-switch-events.jsonl')
os.environ['PILOT_PREFERRED_PATH'] = str(DATA / 'pilot-gpt6-preferred.txt')
os.environ['PILOT_PRIORITY_PATH'] = str(DATA / 'pilot-gpt6-priority.txt')
# Preference order comes from pilot-gpt6-priority.txt (editable at runtime);
# "2,3,4,1" burns the accounts expiring soonest first.
os.environ.pop('PILOT_PRIORITY', None)

import pilot_router as pr

CONTAINER = 'multivibe-pilot-gpt6'
gate = threading.RLock()
inflight = 0
last_success = 0.0
ensure_active = pr.router.ensure_active
quota_error_switch = pr.router.quota_error_switch
dispatch = pr.Handler.dispatch

def ensure_gated():
    with gate:
        return pr.router.active if inflight else ensure_active()

def switch_gated():
    with gate:
        # A rejected request has not started streaming, but another request may have.
        return None if inflight > 1 else quota_error_switch()

def dispatch_gated(self):
    global inflight
    with gate:
        if time.time() - last_success > 90:
            self.json_error(503, 'quota_refresh_stale', 'Quota refresh unavailable or stale')
            return
        if not inflight:
            ensure_active()
        current = pr.router.current()
        if current is None or not pr.eligible(current, 0):
            self.json_error(503, 'no_accounts', 'No account with verified quota available')
            return
        inflight += 1
    try:
        dispatch(self)
    finally:
        with gate:
            inflight -= 1

pr.router.ensure_active = ensure_gated
pr.router.quota_error_switch = switch_gated
pr.Handler.dispatch = dispatch_gated
pr.Handler.do_POST = dispatch_gated
pr.Handler.do_GET = dispatch_gated

def sync_edge_store():
    """Keep the edge's read-only store copy fresh (valid tokens, live accounts).

    The edge mounts a single-file copy, so rewrite it in place: a rename would
    leave the container bound to the old inode.
    """
    source = DATA / 'accounts.json'
    target = DATA / 'pilot-accounts.json'
    try:
        data = source.read_bytes()
    except OSError as error:
        print('edge_store_read_error', type(error).__name__, flush=True)
        return
    try:
        if target.read_bytes() == data:
            return
    except OSError:
        pass
    try:
        with open(target, 'wb') as handle:
            handle.write(data)
    except OSError as error:
        print('edge_store_sync_error', type(error).__name__, flush=True)


def refresh():
    global last_success
    accounts = pr.load_accounts()
    if not accounts:
        raise RuntimeError('No accounts')
    for account in accounts:
        if not account.get('enabled', True):
            continue
        token = account['accessToken']
        part = token.split('.')[1]
        claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
        account_id = claims.get('https://api.openai.com/auth', {}).get('chatgpt_account_id')
        headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json',
                   'User-Agent': 'codex_cli_rs'}
        if account_id:
            headers['ChatGPT-Account-Id'] = account_id
        req = urllib.request.Request('https://chatgpt.com/backend-api/wham/usage', headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            rate = json.load(response)['rate_limit']
        primary = rate['primary_window']['used_percent']
        weekly = rate['secondary_window']['used_percent']
        account['usage'] = {'primary': {'usedPercent': primary},
                            'secondary': {'usedPercent': weekly}}
    with gate:
        with pr.router.lock:
            pr.router.accounts = accounts
        last_success = time.time()

def run():
    refresh()
    sync_edge_store()
    server = pr.serve()
    keys = json.loads((DATA / 'local-keys.json').read_text(encoding='utf-8'))
    env = os.environ.copy()
    env.update(PROXY_API_KEY=keys['proxy'], ADMIN_TOKEN=keys['admin'])
    args = ['docker', 'run', '-d', '--rm', '--name', CONTAINER,
            '-p', '127.0.0.1:14765:14755',
            '--mount', 'type=volume,source=multivibe-review-target,target=/target,readonly',
            '--mount', f'type=bind,source={DATA / "pilot-accounts.json"},target=/data/accounts.json,readonly',
            '-e', 'STORE_PATH=/data/accounts.json', '-e', 'V1_EDGE_HOST=0.0.0.0',
            '-e', 'V1_EDGE_PORT=14755', '-e', 'MAX_UPSTREAM_RETRIES=0',
            '-e', 'V1_EDGE_UPSTREAM_TIMEOUT_MS=90000', '-e', 'CODEX_SESSION_AFFINITY=true',
            '-e', 'CHATGPT_BASE_URL=http://host.docker.internal:14767',
            '-e', 'NODE_CONTROL_PLANE_URL=http://host.docker.internal:1456',
            '-e', 'PROXY_API_KEY', '-e', 'ADMIN_TOKEN', 'rust:bookworm',
            '/target/debug/multivibe-v1-edge']
    started = False
    try:
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError('Edge start failed: ' + result.stderr[:300])
        started = True
        print('parallel_pilot_started ports=14765,14767', flush=True)
        while True:
            time.sleep(30)
            try:
                refresh()
                sync_edge_store()
            except Exception as error:
                print('quota_refresh_error', type(error).__name__, flush=True)
    finally:
        if started:
            subprocess.run(['docker', 'stop', '-t', '3', CONTAINER], capture_output=True, timeout=30)
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    run()
