"""B05-C bounded acquisition, ranking and crash-safe raw-only bookkeeping."""
import copy
import hashlib
import json
import re
import os
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import urllib.robotparser
from collect_jobs import BASE, ROOT, JOB, SITEMAP, LABELS, OPEN_DAY, PREFERRED_DAY, TZ, Fetcher, StopCollection, Visible, allowed, now, parse_page, redact
from csv_records import write_csv

PII = re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)\d{11}(?!\d)')


def atomic_json(path, content):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(content, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def append_json(path, content):
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(content, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def sitemap_entries(payload):
    if not payload or b'<!DOCTYPE' in payload.upper():
        return []
    result = []
    for child in ET.fromstring(payload):
        values = {part.tag.rsplit('}', 1)[-1]: (part.text or '').strip() for part in child}
        url = values.get('loc', '')
        if allowed(url):
            result.append((url, values.get('lastmod') or 'unknown'))
    return result


def modified_key(value):
    try:
        instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return instant.replace(tzinfo=timezone.utc).timestamp() if instant.tzinfo is None else instant.timestamp()
    except (ValueError, TypeError):
        return float('-inf')


def date_value(row, key):
    value = row.get(key)
    try:
        return date.fromisoformat(value['normalized']) if isinstance(value, dict) else None
    except (KeyError, ValueError, TypeError):
        return None


def exclusions(row, text):
    reasons = []
    employer = row.get('employer', 'unknown')
    if employer == 'unknown' or not employer.strip() or employer == row.get('name') or '职点迷津' in employer or employer not in text:
        reasons.append('单位缺失或无效')
    if row.get('recruitment_type') != '校招':
        reasons.append('招聘类型未知' if row.get('recruitment_type') == 'unknown' else '非校招')
    deadline = date_value(row, 'application_end')
    if deadline is None:
        reasons.append('截止未知')
    elif deadline < OPEN_DAY or row.get('open_status') != 'open':
        reasons.append('已截止')
    condition = row.get('condition_text', '')
    if not isinstance(condition, str) or len(condition) < 10 or condition not in text or row.get('evidence_excerpt', '') not in text:
        reasons.append('证据不符')
    if PII.search(text):
        reasons.append('PII')
    if row.get('application_start') != 'unknown':
        reasons.append('报名开始被推断')
    return reasons


def rank(row):
    end = date_value(row, 'application_end') or date.max
    published = date_value(row, 'published_at') or date.min
    return (0 if end >= PREFERRED_DAY else 1, end.toordinal(), -published.toordinal(), row['source_url'])


def remap(value, old, new):
    if isinstance(value, dict):
        return {k: remap(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [remap(v, old, new) for v in value]
    return new if value == old else value


def materialize(raw, batch, candidates):
    rows = []
    for number, original in enumerate(sorted(candidates, key=rank)[:50], 1):
        row = copy.deepcopy(original)
        destination = raw / f'{batch}-{number:02d}.evidence.txt'
        payload = (ROOT / row['raw_snapshot']).read_bytes()
        relative = destination.relative_to(ROOT).as_posix()
        row = remap(row, row['raw_snapshot'], relative)
        row['id'] = f'{batch}-{number:02d}'
        destination.write_bytes(payload)
        rows.append(row)
    write_csv(raw / (batch + '.records.csv'), rows)
    return rows


def summary(raw, batch, ledger, rows):
    pages = ledger['detail_pages']
    lines = ['# B05-C 公开校招岗位原始数据（未做个人资格匹配）', '',
             '基准日2026-10-30 +08:00；open截止≥2026-10-31；优选截止≥2026-11-07。报名开始恒unknown。',
             '公开截止时间是采集时点证据，不能保证招聘方未来不提前关闭，不能保证每位学生符合报名资格。', '',
             f'抓取页数：{pages}；严格合格：{len(rows)}；排除/失败：{pages - len(ledger["qualified"])}；目标缺口：{max(0, 50 - len(rows))}。',
             '停止原因：' + ledger['stop_reason'] + '。',
             '严格CSV只含明确校招且open的记录。招聘类型unknown仅登记次级线索，不补主池、不计合格。',
             '抓取顺序只能依据sitemap lastmod倒序，未访问前不能推断截止日；最终交付按优选线、截止升序、发布日期降序排列。', '',
             '## 排除原因（每页首要原因，合计可对账）', '']
    counts = Counter(x['reasons'][0] for x in ledger['details'] if x.get('reasons'))
    for reason in ('已截止', '截止未知', '非校招', '招聘类型未知', '单位缺失或无效', '证据不符', 'PII', 'HTTP失败', '解析失败'):
        lines.append(f'- {reason}：{counts[reason]}')
    lines.extend(['', '## 全部不符合项（同页可多项，不作页数相加）', ''])
    all_counts = Counter(reason for item in ledger['details'] for reason in item.get('reasons', []))
    for reason, count in sorted(all_counts.items()):
        lines.append(f'- {reason}：{count}')
    lines.extend(['', '## 字段解析率（以所有实际抓取页为分母，失败页计无值）', ''])
    for key in ('employer', 'education', 'major', 'application_end'):
        n = sum(x.get('parsed_fields', {}).get(key, False) for x in ledger['details'])
        lines.append(f'- {key}：{n}/{pages}' + (f'（{n / pages:.1%}）' if pages else '（无样本）'))
    lines.extend(['', '## 入选表', '', '| 编号 | 岗位 | 单位 | 地点 | 截止日 | 学历 | 专业 | 是否校招 | 入选理由 |', '|---|---|---|---|---|---|---|---|---|'])
    def cell(value):
        if isinstance(value, dict):
            value = value.get('raw', 'unknown')
        return str(value).replace('|', '／').replace('\n', ' ')
    for row in rows:
        preferred = date_value(row, 'application_end') >= PREFERRED_DAY
        cells = [row['id'], row['name'], row['employer'], row['location'], row['application_end']['normalized'], row['education'], row['major'], '校招', '单位及原文可追溯，截止满足优选线' if preferred else '单位及原文可追溯，截止仍开放（未达优选线）']
        lines.append('| ' + ' | '.join(cell(value) for value in cells) + ' |')
    lines.extend(['', 'raw页级TXT、page-records.jsonl、逐页索引在抓取时即落盘；CSV和本表只列严格入选记录。未写data/processed/。', '不足50的缺口按上述实数及原因披露，不放宽条件。'])
    (raw / (batch + '.summary.md')).write_text('\n'.join(lines) + '\n', encoding='utf-8')


def run_batch(args, contact):
    raw = ROOT / 'data/raw'
    if args.limit > 10:
        pilots = []
        for file in raw.glob('BATCH-*.run.json'):
            value = json.loads(file.read_text(encoding='utf-8'))
            if value.get('limit') == 10 and value.get('validation_passed') is True:
                pilots.append(file)
        if not pilots:
            print('STOP: a completed passing --limit 10 pilot is required before batch acquisition')
            return 1
    batch = 'BATCH-' + datetime.now(TZ).strftime('%Y%m%d-%H%M%S')
    pages_dir = raw / (batch + '.pages')
    pages_dir.mkdir()
    ledger_path = raw / (batch + '.run.json')
    ua = f'Mozilla/5.0 (compatible; CareerCompass/0.1; contest-demo; contact:{contact})'
    ledger = {'batch': batch, 'started_at': now(), 'ended_at': 'unknown', 'limit': args.limit, 'target': 50,
              'baseline': '2026-10-30', 'open_from': '2026-10-31', 'preferred_from': '2026-11-07',
              'ua': ua.replace(contact, '[REDACTED]'), 'delay': args.delay, 'requests': [], 'details': [],
              'detail_pages': 0, 'qualified': [], 'secondary': [], 'stop_reason': 'running', 'validation_passed': False}
    save = lambda: atomic_json(ledger_path, ledger)
    fetch = Fetcher(ua, args.delay, ledger)
    fetch.on_update = save
    index_path = raw / 'collect-index.jsonl'
    seen = set()
    candidates = []
    save()
    try:
        if index_path.exists():
            seen = {json.loads(line)['url'] for line in index_path.read_text(encoding='utf-8').splitlines() if line.strip()}
        payload, entry = fetch.get(BASE + '/robots.txt')
        if not payload or not re.search(rb'(?im)^user-agent\s*:', payload):
            raise StopCollection('RobotsUnavailableOrInvalid')
        robot = urllib.robotparser.RobotFileParser()
        robot.parse(payload.decode('utf-8').splitlines())
        fetch.robots = robot
        ledger['robots'] = {'http_status': entry['http_status'], 'checked_at': entry['obtained_at'], 'rules': [redact(line) for line in payload.decode('utf-8').splitlines() if re.match(r'(?i)^(user-agent|allow|disallow|sitemap)\s*:', line)], 'hard_deny': '/api/'}
        payload, _ = fetch.get(BASE + '/sitemap.xml')
        entries = sitemap_entries(payload)
        maps = sorted((x for x in entries if SITEMAP.fullmatch(urlsplit(x[0]).path)), key=lambda x: modified_key(x[1]), reverse=True)[:4]
        jobs = [(u, lastmod) for u, lastmod in entries if JOB.fullmatch(urlsplit(u).path)]
        ledger['sitemap_shards'] = [x[0] for x in maps]
        for url, _ in maps:
            payload, _ = fetch.get(url)
            jobs.extend((u, lastmod) for u, lastmod in sitemap_entries(payload) if JOB.fullmatch(urlsplit(u).path))
        latest = {}
        for url, lastmod in jobs:
            if url not in latest or modified_key(lastmod) > modified_key(latest[url]):
                latest[url] = lastmod
        targets = sorted(((u, m) for u, m in latest.items() if u not in seen), key=lambda x: modified_key(x[1]), reverse=True)[:args.limit]
        ledger['discovered_urls'] = len(latest)
        ledger['already_seen'] = sum(u in seen for u in latest)
        for page_number, (url, lastmod) in enumerate(targets, 1):
            if len(candidates) >= 50:
                ledger['stop_reason'] = 'Target50Reached'
                break
            detail = {'url': url, 'lastmod': lastmod, 'http_status': 'unknown', 'result': 'attempting', 'reasons': []}
            ledger['details'].append(detail)
            save()
            requests_before = len(ledger['requests'])
            payload = None
            try:
                payload, entry = fetch.get(url)
            finally:
                if len(ledger['requests']) > requests_before:
                    entry = ledger['requests'][-1]
                    ledger['detail_pages'] += 1
                    detail['http_status'] = entry['http_status']
                    if payload is None:
                        append_json(index_path, {'url': url, 'obtained_at': entry['obtained_at'], 'http_status': entry['http_status'], 'batch': batch})
                        seen.add(url)
                    save()
            if payload is None:
                detail.update(result='excluded', reasons=['HTTP失败'], error_type=entry['error_type'])
                save()
                continue
            path = pages_dir / f'{page_number:03d}.evidence.txt'
            relative = path.relative_to(ROOT).as_posix()
            try:
                row, txt = parse_page(payload.decode('utf-8'), url, entry['obtained_at'], f'{batch}-PAGE-{page_number:03d}', relative)
            except (ValueError, UnicodeError) as exc:
                diagnosis = Visible()
                diagnosis.feed(payload.decode('utf-8', errors='replace'))
                detail.update(result='excluded', reasons=['解析失败'], error_type=type(exc).__name__, parser_issue=str(exc) if str(exc) in ('DeadlineLabelMissing', 'IntroductionLabelMissing', 'EvidenceSubstringMismatch') else 'OtherParseError', observed_label_counts={label: sum(text.rstrip('：:') == label for text in diagnosis.parts) for label in LABELS})
                parts = getattr(exc, 'visible_parts', [])
                heading_positions = getattr(exc, 'visible_headings', [])
                detail['visible_headings'] = [parts[i] for i, _ in heading_positions if i < len(parts)]
                start = next((i for i, text in enumerate(parts) if text.rstrip('：:') == '报名截止'), None)
                if start is not None:
                    names = getattr(exc, 'observed_names', ('unknown', 'unknown'))
                    start = next((i for i in range(start) if parts[i] == names[1] and names[1] != 'unknown'), start)
                    end = next((i for i in range(start + 1, len(parts)) if parts[i] in ('查看原始公告', '问题反馈', '帮助我们把求职体验做得更好')), len(parts))
                    text = f'# 岗位名：{names[0]}\n# URL：{url}\n# 获取时间：{entry["obtained_at"]}\n' + '\n'.join(parts[start:end]) + '\n'
                    if not PII.search(text):
                        path.write_bytes(text.encode('utf-8'))
                        detail.update(partial_evidence_path=relative, partial_evidence_hash=hashlib.sha256(text.encode('utf-8')).hexdigest())
                append_json(index_path, {'url': url, 'obtained_at': entry['obtained_at'], 'http_status': entry['http_status'], 'batch': batch, 'result': 'parse_failed', 'partial_evidence_path': detail.get('partial_evidence_path', 'unknown')})
                save()
                continue
            # No HTML or raw PII is persisted; reject any missed PII instead of writing it.
            if PII.search(txt):
                detail.update(result='excluded', reasons=['PII'])
                append_json(index_path, {'url': url, 'obtained_at': entry['obtained_at'], 'http_status': entry['http_status'], 'batch': batch, 'result': 'PII_excluded'})
                save()
                continue
            with path.open('wb') as stream:
                stream.write(txt.encode('utf-8'))
                stream.flush()
                os.fsync(stream.fileno())
            append_json(pages_dir / 'page-records.jsonl', row)
            append_json(index_path, {'url': url, 'obtained_at': entry['obtained_at'], 'http_status': entry['http_status'], 'batch': batch, 'evidence_path': relative})
            seen.add(url)
            detail.update(evidence_path=relative, evidence_hash=hashlib.sha256(txt.encode('utf-8')).hexdigest(),
                          parsed_fields={k: row[k] != 'unknown' for k in ('employer', 'education', 'major', 'application_end')})
            reasons = exclusions(row, txt)
            detail.update(result='excluded' if reasons else 'qualified', reasons=reasons)
            if reasons == ['招聘类型未知']:
                ledger['secondary'].append(row['source_url'])
            if not reasons:
                candidates.append(row)
                ledger['qualified'].append(row['source_url'])
            save()
            # Preserve current qualified CSV/summary even if interrupted before the next page.
            rows = materialize(raw, batch, candidates)
            summary(raw, batch, ledger, rows)
            print(json.dumps({'page': ledger['detail_pages'], 'qualified': len(candidates), 'excluded': ledger['detail_pages'] - len(candidates), 'result': detail['result']}, ensure_ascii=False), flush=True)
            if args.dry_run:
                print(json.dumps(row, ensure_ascii=False), flush=True)
        if ledger['stop_reason'] == 'running':
            ledger['stop_reason'] = 'Target50Reached' if len(candidates) >= 50 else 'PageLimitReached' if ledger['detail_pages'] >= args.limit else 'BoundedSitemapsExhausted'
    except (StopCollection, OSError, ValueError, ET.ParseError) as exc:
        ledger['stop_reason'] = str(exc) if isinstance(exc, StopCollection) else type(exc).__name__
    except KeyboardInterrupt:
        ledger['stop_reason'] = 'Interrupted'
    finally:
        for detail in ledger['details']:
            if detail['result'] == 'attempting':
                detail.update(result='excluded', reasons=['HTTP失败'], error_type=ledger['stop_reason'])
        ledger['ended_at'] = now()
        ledger['request_count'] = len(ledger['requests'])
        ledger['qualified_count'] = len(candidates)
        ledger['excluded_count'] = ledger['detail_pages'] - len(candidates)
        # Pilot quality gate: at least one strict match, all produced records satisfy the gate,
        # no parser/PII failures, and a complete ten-page sample.
        ledger['validation_passed'] = args.limit == 10 and ledger['detail_pages'] == 10 and bool(candidates) and not any(set(d['reasons']) & {'解析失败', 'PII'} for d in ledger['details'])
        rows = materialize(raw, batch, candidates)
        summary(raw, batch, ledger, rows)
        save()
    print(json.dumps({'run': ledger_path.relative_to(ROOT).as_posix(), 'pages': ledger['detail_pages'], 'qualified': len(rows), 'shortfall': max(0, 50 - len(rows)), 'stop': ledger['stop_reason'], 'pilot_passed': ledger['validation_passed'], 'processed_written': False}, ensure_ascii=False), flush=True)
    return 0 if ledger['stop_reason'] in ('Target50Reached', 'PageLimitReached', 'BoundedSitemapsExhausted') else 1
