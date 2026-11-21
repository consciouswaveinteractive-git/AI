"""Print quota as card-style progress bars. No secrets, no network."""
import datetime, json, os, pathlib, sys

DATA = pathlib.Path(os.environ['LOCALAPPDATA']) / 'MultiVibe-Codex-Pilot'
TZ = datetime.timezone(datetime.timedelta(hours=7))
INNER = 70
TEXT = INNER - 2
BAR = 58


def left_text(ms):
    if not ms:
        return '-'
    target = datetime.datetime.fromtimestamp(ms / 1000, TZ)
    seconds = max(0, int((target - datetime.datetime.now(TZ)).total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes = seconds // 60
    parts = []
    if days:
        parts.append(f'{days}d')
    if hours:
        parts.append(f'{hours}h')
    parts.append(f'{minutes}m')
    return ' '.join(parts)


def bar(percent):
    filled = round(percent * BAR / 100)
    return '█' * filled + '░' * (BAR - filled)


def row(text):
    return '│ ' + text.ljust(TEXT) + ' │'


def metric(label, reset_ms, percent):
    left = f'Resets in {left_text(reset_ms)}'
    right = f'{percent}% left'
    return row(left.ljust(TEXT - len(right)) + right)


store = json.loads((DATA / 'accounts.json').read_text())
accounts = store.get('accounts', [])
highlight = int(sys.argv[1]) - 1 if len(sys.argv) > 1 and sys.argv[1].isdigit() else None

for index, account in enumerate(accounts):
    usage = account.get('usage') or {}
    primary = usage.get('primary') or {}
    secondary = usage.get('secondary') or {}
    five = 100 - int(primary.get('usedPercent') or 0)
    week = 100 - int(secondary.get('usedPercent') or 0)
    title = f'#{index + 1}  {account.get("email", "")}'
    if index == highlight:
        title += '  ◀ ĐANG DÙNG'
    print('┌' + '─' * INNER + '┐')
    print(row(title))
    print('├' + '─' * INNER + '┤')
    print(row('5-hour limit'))
    print(metric('', primary.get('resetAt'), five))
    print(row(bar(five)))
    print(row(''))
    print(row('Weekly limit'))
    print(metric('', secondary.get('resetAt'), week))
    print(row(bar(week)))
    print('└' + '─' * INNER + '┘')
    print()
