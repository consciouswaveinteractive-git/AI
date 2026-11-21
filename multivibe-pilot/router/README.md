# Multi-account pilot router

These scripts are the local control layer for the OpenCode `pilot_gpt6` /
`pilot_multivibe` providers.

## Scripts

- `pilot_router.py` — policy layer. Keeps one account active while its
  5-hour quota is above the threshold, then selects the eligible account with
  the most weekly quota remaining. Upstream quota errors trigger one safe
  handover to another account. Errors are returned as JSON, and transient
  upstream connection failures are retried.
- `pilot_service.py` — single-account service: quota refresh loop, edge
  container, start/stop and status helpers.
- `pilot_parallel.py` — runs the edge (`14765`) and the router (`14767`) in one
  process, mirrors the account store every 30 seconds and refreshes quota.
- `pilot_parallel_watchdog.ps1` — restarts the control plane and the container
  when they are missing; suitable for Task Scheduler.

## Switching rules

| Rule | Behaviour |
|---|---|
| Threshold | Switch only when 5-hour quota is **below** `PILOT_SWITCH_THRESHOLD` (default `20`). Exactly 20 still counts as usable. |
| Target | Eligible account with the **most weekly quota** remaining. |
| Preferred account | `PILOT_PREFERRED_PATH` (1-based account number) is restored as soon as it is eligible again. |
| All accounts low | Keep the current account until it is actually exhausted, then pick the best remaining one. |
| Mid-stream | Never switch inside a running request. |
| Failed refresh | Last-success timestamp is not advanced, so cached quota is never shown as freshly refreshed. |

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `PILOT_SECRETS_FILE` | installation store under `%LOCALAPPDATA%` | Local secrets/account file |
| `PILOT_SWITCH_THRESHOLD` | `20` | 5-hour quota switch threshold |
| `PILOT_PREFERRED_PATH` | `pilot-preferred.txt` | Preferred account (1-based) |
| `PILOT_STATE_PATH` | `pilot-router-state.json` | Active account index (0-based) |
| `PILOT_EVENTS_PATH` | `pilot-switch-events.jsonl` | Switch event log |
| `PILOT_REQUESTS_PATH` | `pilot-router-requests.jsonl` | Per-request account/status log |
| `PILOT_REFRESH_INTERVAL` | `10` | Quota refresh interval in seconds |
| `PILOT_ROUTER_PORT` | `14757` | Router port |
| `CHATGPT_UPSTREAM` | `https://chatgpt.com` | Upstream base URL |

## Usage

```powershell
$env:PILOT_SECRETS_FILE = (Resolve-Path .\multivibe-pilot\local\pilot-secrets.json)
python .\multivibe-pilot\router\pilot_service.py status
python .\multivibe-pilot\router\pilot_parallel.py
```

Never commit the secrets file, account stores, logs or runtime state.
