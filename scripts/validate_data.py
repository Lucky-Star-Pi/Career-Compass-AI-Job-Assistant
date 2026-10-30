"""Offline, standard-library-only production data gate. Empty data is reported explicitly."""
import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OPTIONAL = 'batch location organization_type announcement_url application_url last_verified_at published_at application_start application_end education degree major graduation_time experience political_status certificates age other_restrictions profile_version'.split()
REQUIRED = set(OPTIONAL + 'id name employer source_url obtained_at conditions condition_text standardized_values logical_relationships human_verification open_status raw_snapshot evidence_hash evidence_excerpt evidence_metadata source_refs missing_fields conflicts status evaluations profile_confirmed is_fixture'.split())


def timestamp(value):
    try:
        return isinstance(value, str) and value.endswith('+08:00') and datetime.fromisoformat(value).utcoffset().total_seconds() == 28800
    except (ValueError, AttributeError, TypeError):
        return False


def safe_path(root, value, area):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('invalid relative evidence path')
    path = (root / value).resolve()
    if not path.is_relative_to((root / area).resolve()) or path.suffix.lower() != '.txt':
        raise ValueError('evidence must be a TXT within ' + area)
    return path


def validate_record(row, root=ROOT, allow_fixtures=False):
    errors = []
    if not isinstance(row, dict):
        return ['record must be object']
    absent = sorted(REQUIRED - row.keys())
    if absent:
        errors.append('missing keys: ' + ','.join(absent))
    fixture_hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / 'data/fixtures').rglob('*.txt')}
    serialized = json.dumps(row, ensure_ascii=False).lower()
    if re.search(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}|(?<!\d)1[3-9]\d{9}(?!\d)|(?<!\d)\d{17}[\dx](?!\d)', serialized):
        errors.append('record requires contact/identifier redaction')
    if not allow_fixtures and (row.get('is_fixture') is not False or 'fixtures/' in serialized.replace('\\', '/') or '虚构' in serialized or row.get('evidence_hash') in fixture_hashes):
        errors.append('fixtures contamination or missing real-data marker')
    u = urlsplit(row.get('source_url', '') if isinstance(row.get('source_url'), str) else '')
    if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password or u.query or u.fragment:
        errors.append('invalid source_url (no credential/query/fragment allowed)')
    elif not allow_fixtures and u.hostname not in ('zhidianmijin.com.cn', 'www.zhidianmijin.com.cn'):
        errors.append('source_url must identify actual zhidianmijin source')
    if not timestamp(row.get('obtained_at')):
        errors.append('obtained_at must be ISO8601 with explicit +08:00')
    if row.get('last_verified_at', 'unknown') != 'unknown' and not timestamp(row.get('last_verified_at')):
        errors.append('invalid last_verified_at')
    if not re.fullmatch('[0-9a-f]{64}', str(row.get('evidence_hash', ''))):
        errors.append('invalid evidence_hash')
    for key in ('id', 'name', 'employer', 'condition_text', 'evidence_excerpt'):
        if not isinstance(row.get(key), str) or not row[key].strip() or row[key] == 'unknown':
            errors.append(key + ' must be nonempty evidence-backed text')
    for key in ('conditions', 'logical_relationships', 'source_refs', 'missing_fields', 'conflicts', 'evaluations'):
        if not isinstance(row.get(key), list):
            errors.append(key + ' must be list')
    for key in ('standardized_values', 'human_verification', 'evidence_metadata'):
        if not isinstance(row.get(key), dict):
            errors.append(key + ' must be object')
    missing = row.get('missing_fields', [])
    if isinstance(missing, list):
        for key in OPTIONAL:
            if row.get(key) == 'unknown' and key not in missing:
                errors.append('unknown not listed in missing_fields: ' + key)
    if row.get('open_status') not in ('open', 'closed', 'not_started', 'unknown', 'conflict'):
        errors.append('invalid open_status')
    try:
        evidence = safe_path(root, row.get('raw_snapshot'), 'data/fixtures' if allow_fixtures else 'data/raw').read_bytes()
        if hashlib.sha256(evidence).hexdigest() != row.get('evidence_hash'):
            errors.append('evidence_hash mismatch')
        text = evidence.decode('utf-8')
        if re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)1[3-9]\d{9}(?!\d)|(?<!\d)\d{17}[\dXx](?!\d)', text):
            errors.append('evidence requires contact/identifier redaction')
        for key in ('evidence_excerpt', 'condition_text'):
            if not isinstance(row.get(key), str) or row[key] not in text:
                errors.append(key + ' absent from evidence')
    except (ValueError, OSError, UnicodeError):
        errors.append('raw_snapshot unavailable or outside allowed TXT evidence area')
    refs = row.get('source_refs')
    if not isinstance(refs, list) or not refs:
        errors.append('source_refs required')
    else:
        for ref in refs:
            if not isinstance(ref, dict) or not all(k in ref for k in ('source_url', 'obtained_at', 'raw_snapshot', 'evidence_hash')):
                errors.append('invalid source_ref')
                continue
            if not timestamp(ref['obtained_at']):
                errors.append('source_ref timestamp invalid')
            if not allow_fixtures and ref.get('evidence_hash') in fixture_hashes:
                errors.append('fixtures contamination in source_ref')
            try:
                b = safe_path(root, ref['raw_snapshot'], 'data/fixtures' if allow_fixtures else 'data/raw').read_bytes()
                if hashlib.sha256(b).hexdigest() != ref['evidence_hash']:
                    errors.append('source_ref hash mismatch')
            except (OSError, ValueError):
                errors.append('source_ref evidence unavailable')
    meta = row.get('evidence_metadata', {})
    if not isinstance(meta, dict) or not all(k in meta for k in ('url', 'obtained_at', 'http_status', 'screenshot_path')) or meta.get('url') != row.get('source_url') or meta.get('obtained_at') != row.get('obtained_at'):
        errors.append('evidence_metadata missing or inconsistent')
    status = row.get('status')
    verification = row.get('human_verification', {})
    if not isinstance(verification, dict) or verification.get('state') not in ('pending', 'verified', 'conflict') or not all(k in verification for k in ('verified_at', 'evidence_refs')):
        errors.append('invalid human_verification')
    if status not in ('eligible', 'ineligible', 'unknown'):
        errors.append('invalid status')
    evaluations = row.get('evaluations', [])
    valid_evaluations = isinstance(evaluations, list) and bool(evaluations) and all(isinstance(e, dict) and e.get('result') in ('pass', 'fail', 'unknown') and e.get('field') and e.get('evidence_ref') and e.get('profile_fact_ref') for e in evaluations)
    if status == 'eligible':
        if row.get('profile_confirmed') is not True or row.get('profile_version') in (None, '', 'unknown') or missing or row.get('conflicts') or row.get('open_status') != 'open' or verification.get('state') != 'verified' or not timestamp(row.get('last_verified_at')) or not valid_evaluations or any(e['result'] != 'pass' for e in evaluations):
            errors.append('eligible lacks confirmed profile / complete passing evidence')
    if status == 'ineligible' and (not valid_evaluations or not any(e['result'] == 'fail' for e in evaluations)):
        errors.append('ineligible requires explicit evidenced failing condition')
    if row.get('conflicts') and status != 'unknown':
        errors.append('conflict must remain unknown')
    return errors


def run(data_dir, root=ROOT):
    count, failures = 0, []
    if not data_dir.is_dir():
        return 0, ['data directory missing']
    for file in sorted(data_dir.rglob('*')):
        if file.is_file() and file.name != '.gitkeep' and file.suffix != '.json':
            failures.append('unsupported file in processed data: ' + file.name)
    for file in sorted(data_dir.rglob('*.json')):
        try:
            rows = json.loads(file.read_text(encoding='utf-8-sig'))
            if not isinstance(rows, list):
                raise ValueError('expected record array')
        except (ValueError, OSError) as exc:
            failures.append(file.name + ': invalid record array')
            continue
        for index, row in enumerate(rows):
            count += 1
            failures.extend(file.name + '[' + str(index) + ']: ' + e for e in validate_record(row, root))
    return count, failures


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', type=Path, default=ROOT / 'data/processed')
    args = p.parse_args()
    count, failures = run(args.data_dir)
    for failure in failures:
        print('FAIL: ' + failure)
    print(('FAIL' if failures else 'PASS') + ': production records=' + str(count) + ('; NO REAL DATA / eligibility not proven' if count == 0 else ''))
    raise SystemExit(1 if failures else 0)
