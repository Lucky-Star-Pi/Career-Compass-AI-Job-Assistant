"""Offline reparse: reads only saved evidence/CSV and preserves originals as .v1."""
import csv
import hashlib
import json
import re
from pathlib import Path
from collect_jobs import now
from layout_parser import apply_layout
from manual_intake import COLUMNS, FILL_COLUMNS, PII, write_csv


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError('AutoCSVHeaderMismatch')
        return list(reader)


def reparse(batch, root):
    if not re.fullmatch(r'MANUAL-\d{8}-\d{6}', batch):
        print('STOP: invalid batch identifier')
        return 1
    raw = root / 'data/raw'
    auto, fill, run = [raw / (batch + suffix) for suffix in ('.auto.csv', '.FILL_ME.csv', '.run.json')]
    backups = [(path, path.with_name(path.name + '.v1')) for path in (auto, fill, run)]
    if any(not path.exists() or backup.exists() for path, backup in backups):
        print('STOP: source missing or .v1 already exists; refusing to overwrite backups')
        return 1
    before = read_rows(auto)
    files = sorted((raw / (batch + '.pages')).glob('*.evidence.txt'))
    by_path = {row['证据文件']: row for row in before}
    if len(by_path) != len(before) or len(files) != len(before):
        raise ValueError('EvidenceRecordCountMismatch')
    rows, metadata = [], []
    started = now()
    for file in files:
        relative = file.relative_to(root).as_posix()
        if relative not in by_path:
            raise ValueError('EvidenceMappingMissing')
        payload = file.read_bytes()
        text = payload.decode('utf-8-sig')
        if PII.search(text):
            raise ValueError('EvidencePII')
        old = by_path[relative]
        row, parsed = apply_layout(old, text)
        for field in ('条件原文', '证据引用'):
            if old[field] != 'PENDING' and old[field] not in text:
                raise ValueError('OriginalEvidenceMismatch')
        rows.append(row)
        metadata.append({'id': row['编号'], 'raw_snapshot': relative, 'sha256': hashlib.sha256(payload).hexdigest(), **parsed})
    # Only generated tables/ledger are renamed. Evidence is never changed or reconstructed.
    backup_hashes = {backup.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path, backup in backups}
    for path, backup in backups:
        if not backup.resolve().is_relative_to(raw.resolve()):
            raise ValueError('BackupOutsideRaw')
        path.rename(backup)
    write_csv(auto, rows)
    with fill.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FILL_COLUMNS)
        writer.writeheader()
        writer.writerows({column: row[column] for column in FILL_COLUMNS} for row in rows)
    fill_pending = sum(row[key] == 'PENDING' for row in rows for key in FILL_COLUMNS)
    ledger = {'mode': 'reparse', 'batch': batch, 'started_at': started, 'ended_at': now(), 'requests': 0, 'request_count': 0,
              'source_run': run.with_name(run.name + '.v1').relative_to(root).as_posix(), 'backup_sha256': backup_hashes, 'records': metadata,
              'success': len(rows), 'fill_pending_count': fill_pending, 'processed_written': False}
    run.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = ['# B05-I 离线重解析', '', f'实际重解析{len(rows)}条，requests=0。证据字节未改；auto/FILL_ME/run原文件保留为.v1。', '',
              '| 字段 | 修复前PENDING | 修复后PENDING | 修复前unknown | 修复后unknown |', '|---|---|---|---|---|']
    for key in ('单位性质', '报名截止', '学历', '专业'):
        counts = [sum(row[key] == value for row in source) for value in ('PENDING', 'unknown') for source in (before, rows)]
        report.append('| ' + key + ' | ' + ' | '.join(map(str, counts)) + ' |')
    report.extend(['', '| 编号 | 单位性质及原文引用 | 报名截止 | 开放状态 | open_basis | 剩余人工列 |', '|---|---|---|---|---|---|'])
    for row, meta in zip(rows, metadata):
        nature_ref = meta['field_evidence'].get('organization_type', {})
        ref = f'{row["证据文件"]}:{nature_ref.get("line", "unknown")} 原文「{nature_ref.get("evidence_ref", "unknown")}」'
        remaining = '、'.join(key for key, value in row.items() if value == 'PENDING') or '无'
        report.append('| ' + ' | '.join((row['编号'], row['单位性质'] + '；' + ref, meta.get('display_deadline', 'unknown'), row['开放状态'], meta['open_basis'], remaining)) + ' |')
    report.extend(['', f'FILL_ME的PENDING总数：{fill_pending}。备注可空，不作为PENDING。',
                  '长期招聘仅有页面显式原文支持时open，application_end仍unknown；展示“长期招聘，无固定截止日期”，不得渲染伪造日期或倒计时。',
                  'open只是页面声明的开放依据，不代表学生个人资格eligible、岗位永不提前关闭或来源已人工复核。未执行raw记录导出或processed导入。'])
    destination = root / 'data' / (batch + '.REPARSE.md')
    destination.write_text('\n'.join(report) + '\n', encoding='utf-8')
    for file, meta in zip(files, metadata):
        assert hashlib.sha256(file.read_bytes()).hexdigest() == meta['sha256']
    print(json.dumps({'mode': 'reparse', 'requests': 0, 'records': len(rows), 'nature_known': sum(row['单位性质'] != 'PENDING' for row in rows),
                      'specific_end': sum(isinstance(meta['application_end'], dict) for meta in metadata), 'long_term_open': sum(meta['open_basis'] == '长期招聘' and meta['open_status'] == 'open' for meta in metadata),
                      'education_known': sum(row['学历'] not in ('unknown', 'PENDING', '') for row in rows), 'fill_pending': fill_pending, 'evidence_unchanged': True}, ensure_ascii=False))
    return 0
