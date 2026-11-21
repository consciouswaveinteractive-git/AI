# MultiVibe pilot

Local control layer that puts the OpenAI Codex / GPT-6 models from several
ChatGPT accounts behind one OpenCode provider (`pilot_gpt6`). It rotates the
account automatically, keeps quota state fresh, and reports switches into a
single local session.

## Layout

| Path | Purpose |
|---|---|
| `router/` | Account router, quota refresh loop, parallel service and watchdog |
| `multivibe-review/` | Control-plane launcher, review build source and diagnostic scripts |
| `plugin/` | OpenCode 2 plugins (notifiers, agent model defaults, peer orchestrator, timeline) |
| `local/` | Machine-local secrets file (ignored by Git, `README.md` only) |

## How account switching works

- The active account stays in use while its **5-hour** quota is at or above the
  threshold (`PILOT_SWITCH_THRESHOLD`, default `20`). Exactly 20 still counts as
  usable, and a switch never happens in the middle of a stream.
- When it drops below the threshold, the router picks the eligible account with
  the **most weekly quota left**.
- An optional preferred account (`PILOT_PREFERRED_PATH`, 1-based number) is
  restored as soon as it becomes eligible again.
- If every account is below the threshold, the current account is kept until it
  is actually exhausted, to avoid churn and needless `503` responses.
- Quota is only treated as live after a successful `/admin/usage/refresh`; a
  failed refresh never refreshes the "last updated" timestamp.

## Router

```powershell
$env:PILOT_SECRETS_FILE = (Resolve-Path .\multivibe-pilot\local\pilot-secrets.json)
python .\multivibe-pilot\router\pilot_parallel.py
```

- `pilot_router.py` — policy: threshold, weekly-quota ranking, preferred
  account, upstream `429` handover, JSON error bodies, retry on transient
  network failures.
- `pilot_service.py` — single account: refresh loop, edge container, start/stop
  and status helpers.
- `pilot_parallel.py` — both services in one process (`edge` on `14765`,
  `router` on `14767`), mirrors the account store and refreshes quota.
- `pilot_parallel_watchdog.ps1` — starts the control plane and container when
  they are missing; run it from Task Scheduler.

## Plugins

See [`plugin/README.md`](plugin/README.md). Each plugin is a standalone
package that OpenCode loads from an absolute path in `opencode.jsonc`.

## Secrets

Access tokens, refresh tokens, the account store, request logs and runtime
state stay outside Git:

- `multivibe-pilot/local/*` (except `README.md`)
- `multivibe-pilot/router/__pycache__/`
- `*.log`

The scripts read credentials from `PILOT_SECRETS_FILE` (default: the existing
pilot installation store under `%LOCALAPPDATA%\MultiVibe-Codex-Pilot`). Never
commit that file, the account store, or the generated request/switch logs.
