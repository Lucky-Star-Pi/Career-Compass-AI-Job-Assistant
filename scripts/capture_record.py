"""Copy a completed-line native snapshot without rewriting; never prints content."""
import argparse
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--task', required=True)
args = p.parse_args()
root = Path(__file__).resolve().parents[1]
now = datetime.now(timezone(timedelta(hours=8)))
payload = args.source.read_bytes()
source_size = len(payload)
complete = payload.rfind(b'\n') + 1
payload = payload[:complete]
rows = [json.loads(line) for line in payload.splitlines() if line.strip()]
if not rows:
    raise SystemExit('FAIL: no complete native records')
target = root / 'agent-records/raw/native' / (now.strftime('%Y%m%d-%H%M%S') + '-' + args.task + '.jsonl')
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('xb') as f:
    f.write(payload)
digest = hashlib.sha256(payload).hexdigest()
assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
manifest = {'file': target.relative_to(root).as_posix(), 'task': args.task,
            'captured_at': now.isoformat(timespec='seconds'), 'sha256': digest,
            'export_method': 'native-byte-prefix-copy', 'bytes': len(payload),
            'complete_lines': len(rows), 'source_bytes_at_read': source_size,
            'commit': 'pending-next-task-commit', 'privacy_review': 'pending-human-local-only'}
with (root / 'agent-records/native-manifest.jsonl').open('a', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(manifest, ensure_ascii=False) + '\n')
print(json.dumps(manifest, ensure_ascii=False))
