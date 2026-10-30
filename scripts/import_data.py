"""Offline manual-material import. No network, model, database, or eligibility inference."""
import argparse
import hashlib
import json
from csv_records import read_csv
from pathlib import Path
from copy import deepcopy
from validate_data import ROOT, OPTIONAL, safe_path, validate_record


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def normalize(source, fixture):
    if not isinstance(source, dict):
        raise ValueError('input record must be object')
    row = {k: source.get(k, 'unknown') for k in OPTIONAL}
    row.update(source)
    for k in ('name', 'employer', 'source_url', 'obtained_at', 'raw_snapshot', 'condition_text', 'evidence_excerpt'):
        if not isinstance(row.get(k), str) or not row[k] or row[k] == 'unknown':
            raise ValueError('missing required manual field: ' + k)
    if not fixture and source.get('is_fixture') is not False:
        raise ValueError('real input must explicitly declare is_fixture=false')
    payload = safe_path(ROOT, row['raw_snapshot'], 'data/fixtures' if fixture else 'data/raw').read_bytes()
    row['evidence_hash'] = hashlib.sha256(payload).hexdigest()
    row['id'] = source.get('id') or hashlib.sha256('|'.join(str(row[k]) for k in ('employer', 'name', 'batch', 'location', 'source_url')).encode()).hexdigest()[:20]
    row['is_fixture'] = fixture
    row['conditions'] = source.get('conditions', [])
    row['standardized_values'] = source.get('standardized_values', {})
    row['logical_relationships'] = source.get('logical_relationships', [])
    row['human_verification'] = source.get('human_verification', {'state': 'pending', 'verified_at': 'unknown', 'evidence_refs': []})
    row['open_status'] = source.get('open_status', 'unknown')
    row['conflicts'] = source.get('conflicts', [])
    row['evaluations'] = []
    row['profile_confirmed'] = False
    row['profile_version'] = 'unknown'
    row['status'] = 'unknown'
    row['missing_fields'] = sorted(set(source.get('missing_fields', [])) | {k for k in OPTIONAL if row[k] == 'unknown'})
    row['evidence_metadata'] = {'url': row['source_url'], 'obtained_at': row['obtained_at'], 'http_status': 'unknown', 'screenshot_path': 'unknown'} | source.get('evidence_metadata', {})
    row['source_refs'] = deepcopy(source['source_refs']) if 'source_refs' in source else [{'source_url': row['source_url'], 'obtained_at': row['obtained_at'], 'raw_snapshot': row['raw_snapshot'], 'evidence_hash': row['evidence_hash']}]
    problems = validate_record(row, ROOT, fixture)
    if problems:
        raise ValueError('; '.join(problems))
    return row


def import_rows(sources, fixture):
    imported, errors, review, dedup = [], [], [], {}
    for index, source in enumerate(sources):
        try:
            row = normalize(source, fixture)
            base = tuple(str(row[k]) for k in ('employer', 'name', 'batch', 'location'))
            key = base + ((row['source_url'],) if 'unknown' in base else ())
            if key in dedup:
                old = dedup[key]
                conflicts = [k for k in OPTIONAL + ['condition_text', 'conditions', 'open_status'] if old.get(k) != row.get(k)]
                old['source_refs'].extend(r for r in row['source_refs'] if r not in old['source_refs'])
                if conflicts:
                    item = {'record_id': old['id'], 'fields': conflicts, 'left_evidence': old['raw_snapshot'], 'right_evidence': row['raw_snapshot'], 'reason': 'same-key evidence differs; human review required'}
                    review.append(item)
                    old['conflicts'].append(item)
                    old['human_verification']['state'] = 'conflict'
                    old['status'] = 'unknown'
                continue
            dedup[key] = row
            imported.append(row)
            if row['conflicts']:
                review.append({'record_id': row['id'], 'conflicts': row['conflicts']})
        except (ValueError, OSError, TypeError, KeyError) as exc:
            # Do not log source content or exception payload containing user material.
            reason = str(exc) if isinstance(exc, ValueError) and str(exc).startswith('missing required manual field: ') else type(exc).__name__
            errors.append({'input_index': index, 'reason': reason, 'action': 'check CONTRACT required fields and evidence; original retained'})
    return imported, errors, review


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--fixture', action='store_true')
    p.add_argument('--check-only', action='store_true', help='validate input without writing processed or audit outputs')
    args = p.parse_args()
    if args.fixture != args.input.resolve().is_relative_to((ROOT / 'data/fixtures').resolve()):
        p.error('fixture input must be physically isolated and use --fixture')
    files = sorted(args.input.parent.glob(args.input.name)) if '*' in args.input.name else [args.input]
    if not files:
        p.error('input pattern matched no files')
    if len(files) != 1 and not args.check_only:
        p.error('select one concrete batch to avoid ambiguous AUTO identifiers')
    sources = []
    for source_file in files:
        part = read_csv(source_file) if source_file.suffix.lower() == '.csv' else json.loads(source_file.read_text(encoding='utf-8-sig'))
        if not isinstance(part, list):
            p.error('input must be record array')
        sources.extend(part)
    if not isinstance(sources, list):
        p.error('input must be JSON array')
    destination = ROOT / ('data/fixtures/output' if args.fixture else 'data/processed')
    if not args.fixture and not args.check_only and (destination / 'jobs.json').exists():
        p.error('existing production jobs.json: archive/reconcile manually before replacement')
    rows, errors, review = import_rows(sources, args.fixture)
    if args.check_only:
        print(json.dumps({'mode': 'CHECK_ONLY', 'input': len(sources), 'validated': len(rows), 'failed': len(errors), 'errors': errors, 'review': len(review), 'input_empty': not bool(sources), 'processed_written': False}, ensure_ascii=False))
        raise SystemExit(1 if errors else 0)
    write(destination / 'jobs.json', rows)
    audit = ROOT / ('data/fixtures/audit' if args.fixture else 'data/audit')
    write(audit / 'import-errors.json', errors)
    write(audit / 'review-queue.json', review)
    summary = {'mode': 'FICTIONAL_FIXTURE' if args.fixture else 'REAL_MANUAL', 'input': len(sources), 'output': len(rows), 'failed': len(errors), 'deduplicated': len(sources) - len(errors) - len(rows), 'review': len(review), 'eligible': 0}
    write(audit / 'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(1 if errors else 0)
