"""Refresh and print sanitized quota. No email, token, id or credential output."""
import json, os, pathlib, urllib.request, http.cookiejar

p = pathlib.Path(os.environ['LOCALAPPDATA']) / 'MultiVibe-Codex-Pilot'
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.open(urllib.request.Request('http://localhost:1455/admin/session',
        data=json.dumps({'token': (p / 'admin-password.txt').read_text()}).encode(),
        headers={'Content-Type': 'application/json'}), timeout=10).close()
r = op.open(urllib.request.Request('http://localhost:1455/admin/usage/refresh', data=b'{}',
        headers={'Content-Type': 'application/json'}), timeout=90)
d = json.loads(r.read())
accounts = d.get('accounts', [])


def safe_usage(v):
    if isinstance(v, dict):
        return {k: safe_usage(x) for k, x in v.items()
                if not any(s in k.lower() for s in ['token', 'email', 'accountid', 'userid'])}
    if isinstance(v, list):
        return [safe_usage(x) for x in v]
    return v


def percent(window):
    used = (window or {}).get('usedPercent')
    return None if used is None else max(0.0, min(100.0, float(used)))


rows = []
for index, a in enumerate(accounts):
    usage = a.get('usage') or {}
    remaining = [100.0 - value for value in
                 (percent(usage.get('primary')), percent(usage.get('secondary')),
                  percent(usage.get('monthly')), percent(usage.get('credits')))
                 if value is not None]
    headroom = min(remaining) if remaining else None
    primary = percent(usage.get('primary'))
    rows.append({
        'account_index': index,
        'enabled': bool(a.get('enabled', True)),
        'quotaStatus': usage.get('quotaStatus'),
        'primary_usedPercent': primary,
        'secondary_usedPercent': percent(usage.get('secondary')),
        'fetchedAt': usage.get('fetchedAt'),
        'headroom_percent': headroom,
        'five_hour_near_limit': bool(primary is not None and primary >= 90.0),
        'reauthRequired': (a.get('state') or {}).get('reauthRequired'),
        'usage': safe_usage(usage),
    })

eligible = [row['account_index'] for row in rows
            if row['enabled'] and row['headroom_percent'] not in (None, 0.0)
            and not row['five_hour_near_limit'] and not row['reauthRequired']]
print(json.dumps({
    'accounts': rows,
    'failover_eligible_accounts': eligible,
    'failover_gate_two_accounts': len(eligible) >= 2,
}, indent=2))
