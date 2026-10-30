"""Offline regression: fictional inputs stay in fixtures or temporary test directories."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from import_data import import_rows, normalize
from validate_data import ROOT, validate_record


def main():
    source = json.loads((ROOT / 'data/fixtures/input.json').read_text(encoding='utf-8'))[0]
    row = normalize(source, True)
    assert not validate_record(row, ROOT, True)
    assert row['status'] == 'unknown' and row['profile_confirmed'] is False
    print('PASS fixture import: unknown; no eligibility inferred')
    # This runs the actual gate as a child process, not a mirrored boolean assertion.
    with tempfile.TemporaryDirectory(prefix='stage1-data-gate-') as folder:
        path = Path(folder)
        for field in ('source_url', 'obtained_at', 'evidence_hash', 'raw_snapshot', 'status', 'missing_fields'):
            bad = copy.deepcopy(row)
            del bad[field]
            (path / 'jobs.json').write_text(json.dumps([bad], ensure_ascii=False), encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_data.py'), '--data-dir', str(path)], capture_output=True, text=True, encoding='utf-8')
            assert result.returncode != 0 and 'missing keys: ' + field in result.stdout, field
            print('PASS missing ' + field + ': child exit=' + str(result.returncode))
        (path / 'jobs.json').write_text(json.dumps([row], ensure_ascii=False), encoding='utf-8')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_data.py'), '--data-dir', str(path)], capture_output=True, text=True, encoding='utf-8')
        assert result.returncode != 0 and 'fixtures contamination' in result.stdout
        print('PASS fixtures mixed into production input: child exit=' + str(result.returncode))
    tampered = copy.deepcopy(row)
    tampered['evidence_hash'] = '0' * 64
    assert 'evidence_hash mismatch' in validate_record(tampered, ROOT, True)
    print('PASS evidence hash mismatch rejected')
    rows, errors, review = import_rows([source, source], True)
    assert len(rows) == 1 and len(rows[0]['source_refs']) == 1 and not errors
    changed = copy.deepcopy(source)
    changed['education']['normalized'] = 'test-conflict'
    rows, errors, review = import_rows([source, changed], True)
    assert len(rows) == 1 and review and rows[0]['status'] == 'unknown' and rows[0]['human_verification']['state'] == 'conflict'
    print('PASS dedup retains sources; conflicting evidence queued as unknown')
    rows, errors, review = import_rows([{}], True)
    assert not rows and len(errors) == 1
    print('PASS failed import recorded without source content')
    bad = copy.deepcopy(row)
    bad['status'] = 'eligible'
    assert any('eligible lacks' in x for x in validate_record(bad, ROOT, True))
    print('PASS missing profile and conditions cannot become eligible')
    bad = copy.deepcopy(row)
    bad['status'] = 'ineligible'
    assert any('ineligible requires' in x for x in validate_record(bad, ROOT, True))
    print('PASS ineligible requires evidenced failure')
    print('PASS all offline pipeline regression checks')


if __name__ == '__main__':
    main()
