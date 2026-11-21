# MultiVibe review runtime source

This directory contains the source needed to build the `multivibe-v1-edge`
runtime and the local control-plane launcher.

## Contents

- `source/` — Rust workspace and host source from the MultiVibe review build.
- `start_pilot_control.py` — starts the isolated Node control plane after a
  host runtime has been built or supplied locally.
- `DANH_GIA.md`, `HANDOFF_2026-11-02.md` — review notes and handoff state from
  the acceptance run.
- `*.json` — recorded acceptance/smoke results used as evidence.

### Login and proxy helpers

| Script | Purpose |
|---|---|
| `login_gateway.py`, `login.html` | Minimal local login gateway used to seed a session |
| `start_login_pilot.py` | Starts the login pilot together with the gateway |
| `check_login_api.py` | Verifies the login endpoint answers correctly |
| `opencode_proxy.py` | OpenAI-compatible proxy shim in front of the edge |

### Quota helpers

| Script | Purpose |
|---|---|
| `check_real_quota.py` | Reads live quota from the control plane for every account |
| `quota_cards.py` | Renders the compact per-account quota cards |
| `quota_fault_relay.py` | Fault-injection relay used to test quota failover |

### Acceptance and smoke tests

| Script | Purpose |
|---|---|
| `client_acceptance.py` | End-to-end client acceptance run |
| `real_client_probe.py` | Probes the running service with a real client payload |
| `real_model_smoke.py` | Smoke test for each exposed model id |
| `relay_header_check.py` | Asserts forwarded headers are stripped or kept correctly |
| `vscode_failover_service.py` | Failover service used by the editor client tests |

Logs (`*.log`) and the prebuilt host archive (`host.zip`) stay local.

The prebuilt Windows host package and Rust `target/` output are deliberately
not committed. They are large, platform-specific build artifacts. Build the
Rust edge binary from `source/` with:

```powershell
cd .\multivibe-pilot\multivibe-review\source
cargo build --release --bin multivibe-v1-edge
```

For the control plane, point the launcher at a locally installed host app:

```powershell
$env:MULTIVIBE_HOST_APP = 'C:\path\to\multivibe-host\app'
python .\multivibe-pilot\multivibe-review\start_pilot_control.py
```

Credentials, account stores, runtime packages, logs, and local state remain
outside Git. See `..\local\README.md` for the local secrets file.

Quota refreshes every 10 seconds by default. Override with
`PILOT_REFRESH_INTERVAL` when operating against a rate-limited control plane.
