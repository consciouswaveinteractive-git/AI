# OpenCode plugins

Each directory is an independent OpenCode 2 plugin package with its own
`package.json`. Reference them from `opencode.jsonc` with an absolute path:

```jsonc
"plugins": [
  "<repo>/multivibe-pilot/plugin/pilot-gpt6-notifier",
  "<repo>/multivibe-pilot/plugin/agent-model-defaults"
]
```

| Plugin | Purpose |
|---|---|
| `pilot-gpt6-notifier` | Watches `pilot-gpt6-switch-events.jsonl` and posts account-switch notes into one fixed local session |
| `pilot-switch-notifier` | Same idea for the older `pilot-switch-events.jsonl` stream |
| `agent-model-defaults` | Forces the Build and Plan agents onto a chosen provider/model |
| `peer-orchestrator` | Spawns independent peer sessions and opens them as Desktop tabs |
| `opencode-desktop-timeline` | Timeline view for the desktop app |

## Notifier behaviour

- Only switch metadata (`from`, `to`, reason, remaining quota) is read. Tokens
  are never read or logged.
- The destination session is explicit. If the target file is missing or does
  not contain a valid `ses_…` id, nothing is sent rather than falling back to
  whatever session happens to be active.
- File offset is advanced only after a line has been delivered, so a restart
  does not duplicate or drop notifications.

Paths are resolved from the environment (`LOCALAPPDATA`, `PILOT_STATE_DIR`,
`PILOT_SWITCH_EVENTS`) so no personal path is committed.

## Development

```powershell
cd .\multivibe-pilot\plugin\peer-orchestrator
npm install
npm run typecheck
```
