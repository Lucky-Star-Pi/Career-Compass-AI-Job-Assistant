"""Offline regression: fictional inputs stay in fixtures or temporary test directories."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from import_data import import_rows, normalize
from validate_data import DENIED_QUERY_NAMES, ROOT, validate_record

CURRENT_CASE = 'load fictional fixture'


def check(condition, expected, actual):
    if not condition:
        raise AssertionError(f'{CURRENT_CASE}: expected {expected}; actual {actual}')


def main():
    global CURRENT_CASE
    source = json.loads((ROOT / 'data/fixtures/input.json').read_text(encoding='utf-8'))[0]
    row = normalize(source, True)
    errors = validate_record(row, ROOT, True)
    check(not errors, 'no fixture validation errors', errors)
    check(row['status'] == 'unknown' and row['profile_confirmed'] is False, 'unknown and unconfirmed profile', (row['status'], row['profile_confirmed']))
    print('PASS fixture import: unknown; no eligibility inferred')
    for label, url, expected in (
        ('?id=12345', 'https://example.invalid/job/detail?id=12345', False),
        ('?token=abc', 'https://example.invalid/job/detail?token=abc', True),
        ('#frag', 'https://example.invalid/job/detail#frag', True),
        ('user:pass@', 'https://user:pass@host/x', True),
        ('ordinary jobId/from/utm_*', 'https://example.invalid/x?jobId=123&from=test&utm_source=fixture', False),
    ):
        CURRENT_CASE = 'source_url ' + label
        sample = copy.deepcopy(row)
        sample['source_url'] = url
        errors = validate_record(sample, ROOT, allow_fixtures=True)
        invalid = any('invalid source_url' in e for e in errors)
        check(invalid == expected, 'invalid source_url=' + str(expected), invalid)
        print('PASS ' + CURRENT_CASE + ': invalid source_url=' + str(invalid))
    for name in sorted(DENIED_QUERY_NAMES) + ['ToKeN', '%74oken']:
        CURRENT_CASE = 'denied query name ' + name
        sample = copy.deepcopy(row)
        sample['source_url'] = 'https://example.invalid/x?' + name + '=fixture'
        errors = validate_record(sample, ROOT, allow_fixtures=True)
        check(any('invalid source_url' in e for e in errors), 'invalid source_url', errors)
    print('PASS all denied query names, mixed-case and encoded names')
    # This runs the actual gate as a child process, not a mirrored boolean assertion.
    CURRENT_CASE = 'create repository-local temporary directory'
    temporary_root = ROOT / 'data/.tmp'
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='stage1-data-gate-', dir=temporary_root, ignore_cleanup_errors=True) as folder:
        path = Path(folder)
        for field in ('source_url', 'obtained_at', 'evidence_hash', 'raw_snapshot', 'status', 'missing_fields'):
            CURRENT_CASE = 'missing ' + field
            bad = copy.deepcopy(row)
            del bad[field]
            (path / 'jobs.json').write_text(json.dumps([bad], ensure_ascii=False), encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_data.py'), '--data-dir', str(path)], capture_output=True, text=True, encoding='utf-8')
            check(result.returncode != 0 and 'missing keys: ' + field in result.stdout, 'nonzero exit and missing keys: ' + field, (result.returncode, result.stdout, result.stderr))
            print('PASS missing ' + field + ': child exit=' + str(result.returncode))
        CURRENT_CASE = 'fixtures mixed into production input'
        (path / 'jobs.json').write_text(json.dumps([row], ensure_ascii=False), encoding='utf-8')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_data.py'), '--data-dir', str(path)], capture_output=True, text=True, encoding='utf-8')
        check(result.returncode != 0 and 'fixtures contamination' in result.stdout, 'nonzero exit and fixtures contamination', (result.returncode, result.stdout, result.stderr))
        print('PASS fixtures mixed into production input: child exit=' + str(result.returncode))
    CURRENT_CASE = 'evidence hash mismatch rejected'
    tampered = copy.deepcopy(row)
    tampered['evidence_hash'] = '0' * 64
    errors = validate_record(tampered, ROOT, True)
    check('evidence_hash mismatch' in errors, 'evidence_hash mismatch', errors)
    print('PASS evidence hash mismatch rejected')
    CURRENT_CASE = 'dedup retains sources'
    rows, errors, review = import_rows([source, source], True)
    check(len(rows) == 1 and len(rows[0]['source_refs']) == 1 and not errors, 'one row/source and no errors', (len(rows), errors))
    changed = copy.deepcopy(source)
    changed['education']['normalized'] = 'test-conflict'
    CURRENT_CASE = 'conflicting evidence queued as unknown'
    rows, errors, review = import_rows([source, changed], True)
    check(len(rows) == 1 and bool(review) and rows[0]['status'] == 'unknown' and rows[0]['human_verification']['state'] == 'conflict', 'one unknown/conflict row and review queue', (len(rows), errors, bool(review)))
    print('PASS dedup retains sources; conflicting evidence queued as unknown')
    CURRENT_CASE = 'failed import recorded without source content'
    rows, errors, review = import_rows([{}], True)
    check(not rows and len(errors) == 1, 'zero rows and one error', (len(rows), len(errors)))
    print('PASS failed import recorded without source content')
    bad = copy.deepcopy(row)
    bad['status'] = 'eligible'
    CURRENT_CASE = 'missing profile and conditions cannot become eligible'
    errors = validate_record(bad, ROOT, True)
    check(any('eligible lacks' in x for x in errors), 'eligible lacks', errors)
    print('PASS missing profile and conditions cannot become eligible')
    bad = copy.deepcopy(row)
    bad['status'] = 'ineligible'
    CURRENT_CASE = 'ineligible requires evidenced failure'
    errors = validate_record(bad, ROOT, True)
    check(any('ineligible requires' in x for x in errors), 'ineligible requires', errors)
    print('PASS ineligible requires evidenced failure')
    print('PASS all offline pipeline regression checks')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'FAIL {CURRENT_CASE}: expected current check to complete; actual {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
