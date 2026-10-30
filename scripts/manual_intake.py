"""Offline manual CSV validation and raw-only contract export. Never fetches a URL."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
from validate_data import DENIED_QUERY_NAMES, OPTIONAL, REQUIRED, safe_path, timestamp, validate_record

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = '编号,岗位名称,单位名称,单位性质,招聘类型,批次届别,工作地点,详情页URL,公告URL,报名入口URL,发布时间,报名开始,报名截止,学历,学位,专业,毕业时间,工作经验,政治面貌,证书,年龄,其他限制,条件原文,证据引用,开放状态,采集时间,证据文件,备注'.split(',')
HARD = '岗位名称 单位名称 详情页URL 采集时间 条件原文 证据引用 证据文件 编号'.split()
DATE_COLUMNS = ('发布时间', '报名开始', '报名截止')
ORGANIZATIONS = {'央企', '国企', '事业单位', '民企', 'unknown'}
PII = re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)(?:\d{11}|\d{17}[\dXx])(?!\d)')
MAPPING = dict(zip(COLUMNS, 'id name employer organization_type recruitment_type batch location source_url announcement_url application_url published_at application_start application_end education degree major graduation_time experience political_status certificates age other_restrictions condition_text evidence_excerpt open_status obtained_at raw_snapshot notes'.split()))
CONDITIONS = 'education degree major graduation_time experience political_status certificates age other_restrictions'.split()
FILL_COLUMNS = '编号,岗位名称,单位名称,详情页URL,公告URL,报名开始,报名截止,开放状态,单位性质,备注'.split(',')


def pending(value):
    return isinstance(value, str) and bool(re.search(r'(?i)(?<![A-Z0-9_])PENDING(?![A-Z0-9_])', value))


def unknown(value):
    return not isinstance(value, str) or not value.strip() or value.strip().lower() == 'unknown'


def parse_day(value):
    if unknown(value):
        return None
    match = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})|(\d{4})年(\d{1,2})月(\d{1,2})日', value.strip())
    if not match:
        raise ValueError('date format')
    return date(*map(int, match.groups()[:3] if match[1] else match.groups()[3:]))


def write_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def create_templates(root=ROOT):
    raw = root / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    template = raw / 'MANUAL_TEMPLATE.csv'
    if not template.exists():
        row = {field: 'unknown' for field in COLUMNS}
        row.update(编号='SAMPLE', 岗位名称='示例岗位（非真实记录）', 单位名称='示例单位', 备注='示例，导入时必须删除')
        write_csv(template, [row])
    manual = raw / 'MANUAL.csv'
    if not manual.exists():
        write_csv(manual, [])


def read_input(path, columns=COLUMNS):
    if not path.exists() or path.stat().st_size == 0:
        return [], []
    try:
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != columns:
                return [], [f'CSV表头必须为固定{len(columns)}列且顺序一致']
            rows = []
            for record_number, row in enumerate(reader, 2):
                if None not in row and all(isinstance(v, str) and not v.strip() for v in row.values()):
                    continue
                rows.append((record_number, row))
            return rows, []
    except (UnicodeError, csv.Error, OSError):
        return [], ['CSV不可读取或不是UTF-8，请另存为CSV UTF-8']


def validate_url(value, role):
    if unknown(value):
        return role != 'detail'
    try:
        u = urlsplit(value)
        if not u.hostname or u.username is not None or u.password is not None or u.fragment:
            return False
        if any(key.casefold() in DENIED_QUERY_NAMES for key, _ in parse_qsl(u.query, keep_blank_values=True)):
            return False
        if role == 'detail':
            return u.scheme in ('http', 'https') and u.hostname in ('zhidianmijin.com.cn', 'www.zhidianmijin.com.cn')
        if u.scheme != 'https':
            return False
        return role != 'announcement' or not (u.hostname == 'zhidianmijin.com.cn' or u.hostname.endswith('.zhidianmijin.com.cn'))
    except ValueError:
        return False


def check_row(raw, root, collected=False):
    errors = []
    if None in raw or any(raw.get(key) is None for key in COLUMNS):
        return None, ['CSV行列数与表头不符'], None
    # Preserve original condition/excerpt characters; trimming them would silently alter evidence.
    row = {key: raw[key] if key in ('条件原文', '证据引用') else raw[key].strip() for key in COLUMNS}
    if row['编号'].upper() == 'SAMPLE' or '示例' in row['备注']:
        return None, ['示例行必须删除'], None
    remaining = [key for key, value in row.items() if key != '备注' and pending(value)]
    if remaining:
        return None, ['PENDING未补：' + '、'.join(remaining)], None
    for key in HARD:
        if unknown(row[key]):
            errors.append('硬性字段缺失或unknown：' + key)
    if any(PII.search(value) for value in row.values()):
        errors.append('单元格含邮箱、11位手机号或证件号，须脱敏')
    for key, role in (('详情页URL', 'detail'), ('公告URL', 'announcement'), ('报名入口URL', 'application')):
        if not validate_url(row[key], role):
            errors.append(key + '不符合主机/协议/凭据/参数/fragment规则')
    days = {}
    for key in DATE_COLUMNS:
        try:
            days[key] = parse_day(row[key])
        except ValueError:
            errors.append(key + '日期不可解析')
    if not timestamp(row['采集时间']):
        errors.append('采集时间须为ISO8601且显式+08:00')
    state = row['开放状态'] if not unknown(row['开放状态']) else 'unknown'
    end = days.get('报名截止')
    from layout_parser import facts
    # Read the evidence below before accepting an open-without-date claim.
    if state not in ('open', 'closed', 'unknown'):
        errors.append('开放状态仅允许open/closed/unknown')
    elif state == 'open' and end is not None and end < date(2026, 10, 31):
        errors.append('open要求报名截止≥2026-10-31')
    elif state == 'closed' and (end is None or end >= date(2026, 10, 30)):
        errors.append('closed要求报名截止<2026-10-30')
    if row['单位性质'] not in ORGANIZATIONS:
        errors.append('单位性质不在允许枚举中')
    path, payload, text = None, None, None
    if not unknown(row['证据文件']):
        try:
            path = safe_path(root, row['证据文件'], 'data/raw')
            payload = path.read_bytes()
            text = payload.decode('utf-8-sig')
        except (OSError, ValueError, UnicodeError):
            errors.append('证据文件须为data/raw内存在的UTF-8 TXT，不可越界')
    if text is not None:
        source_facts = facts(text, row['证据文件'])
        if state == 'open' and end is None and source_facts['open_basis'] != '长期招聘':
            errors.append('open无截止日仅允许证据显式长期招聘')
        if PII.search(text):
            errors.append('证据TXT含邮箱、11位手机号或证件号，须脱敏')
        for key in ('条件原文', '证据引用'):
            if unknown(row[key]) or row[key] not in text:
                errors.append(key + '未在证据TXT逐字命中')
        expected_headers = [f'# 岗位名称：{row["岗位名称"]}', f'# 详情页URL：{row["详情页URL"]}', '# 公告URL：' + ('unknown' if unknown(row['公告URL']) else row['公告URL']), f'# 采集时间：{row["采集时间"]}']
        collected_headers = [f'# 岗位名：{row["岗位名称"]}', f'# URL：{row["详情页URL"]}', f'# 获取时间：{row["采集时间"]}', '# 公告URL：' + ('unknown' if unknown(row['公告URL']) else row['公告URL'])]
        if text.splitlines()[:4] != expected_headers and not (collected and text.splitlines()[:4] == collected_headers):
            errors.append('证据TXT四行头部须与CSV一致')
    if errors:
        return None, errors, path
    output = {key: 'unknown' for key in OPTIONAL}
    for chinese, internal in MAPPING.items():
        value = row[chinese]
        output[internal] = 'unknown' if unknown(value) else value
    evidence_path = path.relative_to(root.resolve()).as_posix()
    output['raw_snapshot'] = evidence_path
    for key in DATE_COLUMNS:
        day = days[key]
        output[MAPPING[key]] = {'raw': row[key], 'normalized': day.isoformat(), 'precision': 'date', 'timezone': '+08:00'} if day else 'unknown'
    conditions = []
    for key in CONDITIONS:
        value = output[key]
        if value != 'unknown':
            if value not in text:
                errors.append(next(cn for cn, en in MAPPING.items() if en == key) + '值未在证据TXT逐字命中')
            output[key] = {'raw': value, 'normalized': 'unknown', 'evidence_ref': evidence_path}
            conditions.append({'field': key, 'raw': value, 'normalized': 'unknown', 'logic': 'unparsed', 'evidence_ref': evidence_path})
    digest = hashlib.sha256(payload).hexdigest()
    refs = [{'source_url': row['详情页URL'], 'obtained_at': row['采集时间'], 'raw_snapshot': evidence_path, 'evidence_hash': digest, 'source_role': 'detail'}]
    if not unknown(row['公告URL']):
        refs.append({'source_url': row['公告URL'], 'obtained_at': row['采集时间'], 'raw_snapshot': evidence_path, 'evidence_hash': digest, 'source_role': 'announcement'})
    output.update(status='unknown', profile_confirmed=False, profile_version='unknown', is_fixture=False,
                  last_verified_at='unknown', open_status=state, evidence_hash=digest, source_refs=refs,
                  conditions=conditions, standardized_values={}, logical_relationships=[], conflicts=[], evaluations=[],
                  human_verification={'state': 'pending', 'verified_at': 'unknown', 'evidence_refs': [evidence_path]},
                  evidence_metadata={'url': row['详情页URL'], 'obtained_at': row['采集时间'], 'http_status': 'unknown', 'screenshot_path': 'unknown'},
                  manual_review_status='entered-not-independently-reviewed')
    output['field_evidence'] = source_facts['field_evidence']
    if state == 'open' and end is None and source_facts['open_basis'] == '长期招聘':
        output.update(open_basis='长期招聘', display_deadline='长期招聘，无固定截止日期')
    else:
        output['open_basis'] = '具体截止日期' if end else 'unknown'
    output['missing_fields'] = sorted(key for key, value in output.items() if value == 'unknown')
    # This calls the same evidence/fixture gate as production, without writing processed.
    errors.extend(validate_record(output, root))
    return (None if errors else output), errors, path


def evaluate(rows, root=ROOT, collected=False):
    results, records = [], []
    ids = Counter((row.get('编号') or '').strip().casefold() for _, row in rows)
    paths = []
    for _, row in rows:
        try:
            path = safe_path(root, row.get('证据文件'), 'data/raw')
            stat = path.stat()
            paths.append(('inode', stat.st_dev, stat.st_ino))
        except (OSError, ValueError):
            paths.append(None)
    counts = Counter(path for path in paths if path is not None)
    for index, (line, row) in enumerate(rows):
        record, errors, path = check_row(row, root, collected)
        ident = (row.get('编号') or '').strip().casefold()
        if ident and ids[ident] > 1:
            errors.append('编号重复')
        if paths[index] is not None and counts[paths[index]] > 1:
            errors.append('证据文件复用')
        results.append({'csv_line': line, 'passed': not errors, 'reasons': sorted(set(errors))})
        if not errors:
            records.append(record)
    return records, results


def merge_inputs(fill_path, auto_path):
    automatic, errors = read_input(auto_path)
    human, human_errors = read_input(fill_path, FILL_COLUMNS)
    errors.extend(human_errors)
    auto_map, human_map = {}, {}
    for label, rows, mapping, columns in (('自动表', automatic, auto_map, COLUMNS), ('人工表', human, human_map, FILL_COLUMNS)):
        for line, row in rows:
            if None in row or any(row.get(key) is None for key in columns):
                errors.append(f'{label}第{line}行列数不符')
                continue
            ident = row['编号'].strip().casefold()
            if not ident or ident in mapping:
                errors.append(f'{label}第{line}行编号为空或重复')
                continue
            mapping[ident] = (line, row)
    if auto_map.keys() != human_map.keys():
        errors.append('两表编号集合不一致：缺少或新增的行必须核对，不能静默丢弃')
    merged = []
    for ident, (line, original) in auto_map.items():
        row = {key: ('PENDING' if key != '备注' and not value.strip() else value) for key, value in original.items()}
        if ident in human_map:
            line, entered = human_map[ident]
            for key in FILL_COLUMNS:
                # Clearing a placeholder is NOT confirmation that the source omitted it.
                row[key] = 'PENDING' if pending(row[key]) and not entered[key].strip() else entered[key]
        merged.append((line, row))
    return merged, errors


def report_text(rows, records, results, structural):
    rejected = sum(not item['passed'] for item in results)
    lines = ['# 人工录入校验报告', '', f'输入{len(rows)}行；通过{len(records)}行；拒绝{rejected}行；A档（open）{sum(r["open_status"] == "open" for r in records)}条。',
             '人工目标15条；当前缺口' + str(max(0, 15 - len(records))) + '。',
             '批次全通过才导出记录；任何拒绝或结构错误时生成空数组阻止旧导出被误用。',
             '0行只是尚无数据，不代表真实行或15条验收通过。字段值和来源尚未独立人工复核。', '',
             '## 逐行结果', '', '| CSV行号 | 结果 | 原因 |', '|---|---|---|']
    for item in results:
        lines.append(f'| {item["csv_line"]} | {"通过" if item["passed"] else "拒绝"} | ' + ('；'.join(item['reasons']) or '结构/证据校验通过，来源仍待人工复核') + ' |')
    lines.extend(['', '结构错误：' + ('；'.join(structural) or '无'), '', '## 字段有值率（以全部输入行计）', ''])
    for key in COLUMNS:
        count = sum(not unknown(row.get(key)) for _, row in rows)
        lines.append('- ' + key + f'：{count}/{len(rows)}' + (f'（{count / len(rows):.1%}）' if rows else '（0行）'))
    stamps = sorted(r['obtained_at'] for r in records)
    lines.extend(['', '通过记录获取时间窗：' + (stamps[0] + ' 至 ' + stamps[-1] if stamps else 'unknown（无通过记录）'),
                  '缺公告允许：仅保留真实详情引用，announcement_url=unknown并列missing_fields，不伪造第二条source_ref。',
                  '没有请求网站，没有写data/processed；后续导入须人工另行确认。'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=ROOT / 'data/raw/MANUAL.csv')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--auto', type=Path, help='merge a fixed 10-column FILL_ME over the matching 28-column auto CSV')
    args = parser.parse_args()
    rows, structural = merge_inputs(args.input, args.auto) if args.auto else read_input(args.input)
    records, results = evaluate(rows, ROOT, collected=bool(args.auto))
    if not rows:
        print('0 行：尚无人工记录，不代表15条数据验收通过')
    for item in results:
        print('第' + str(item['csv_line']) + '行：' + ('通过' if item['passed'] else '拒绝：' + '；'.join(item['reasons'])))
    for error in structural:
        print('拒绝：' + error)
    rejected = sum(not item['passed'] for item in results)
    print(f'通过={len(records)} 拒绝={rejected} A档(open)={sum(r["open_status"] == "open" for r in records)} check_only={args.check_only}')
    if not args.check_only:
        destination = ROOT / 'data/raw'
        destination.mkdir(parents=True, exist_ok=True)
        exported = [] if rejected or structural else records
        (destination / 'MANUAL.records.json').write_text(json.dumps(exported, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (destination / 'MANUAL_REPORT.md').write_text(report_text(rows, records, results, structural), encoding='utf-8')
        print(f'仅raw导出={len(exported)}；processed未写入')
    return 1 if rejected or structural else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, csv.Error):
        print('拒绝：本地输入或输出不可处理；未访问网络，未写processed')
        raise SystemExit(1)
