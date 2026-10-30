"""B05-H: anonymous GETs from an explicit local URL list only; never lists or APIs."""
import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from collect_jobs import ROOT, TZ, LABELS, UNKNOWN_PHRASES, Fetcher, StopCollection, Visible, now, parse_page
from batch_jobs import atomic_json
from manual_intake import COLUMNS, FILL_COLUMNS, MAPPING, PII, parse_day, validate_url, write_csv

URL_PATTERN = re.compile(r'https://www\.zhidianmijin\.com\.cn/jobs/[0-9a-f-]{36}')
RISK = re.compile(r'验证码|安全验证|安全检查|访问验证|完成验证|风控|访问异常|captcha|verify you are human', re.I)
MARKER = 'PENDING'


def read_urls(path):
    if not path.exists():
        return [], [{'line': 0, 'result': 'missing', 'reason': '人工URL文件不存在'}]
    selected, lines, seen = [], [], set()
    for number, original in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        if not original.strip():
            continue
        try:
            split = urlsplit(original.strip())
            canonical = urlunsplit((split.scheme, split.netloc, split.path, '', ''))
            if not URL_PATTERN.fullmatch(canonical):
                raise ValueError()
        except ValueError:
            lines.append({'line': number, 'result': 'invalid', 'reason': '非允许的https岗位详情URL（不记录原始非法行）'})
            continue
        if canonical in seen:
            lines.append({'line': number, 'url': canonical, 'result': 'duplicate', 'reason': '规范化后重复'})
            continue
        seen.add(canonical)
        if len(selected) >= 30:
            lines.append({'line': number, 'url': canonical, 'result': 'over_limit', 'reason': '超出30条上限，未请求'})
            continue
        selected.append((number, canonical))
        lines.append({'line': number, 'url': canonical, 'result': 'selected', 'query_fragment_removed': bool(split.query or split.fragment)})
    return selected, lines


def source_value(value):
    if isinstance(value, dict):
        return value.get('normalized', 'unknown') if 'precision' in value else value.get('raw', 'unknown')
    return value


def exact_label(lines, labels):
    for index, text in enumerate(lines):
        for label in labels:
            match = re.match('^' + re.escape(label) + r'[：:](.*)$', text)
            if match and match[1].strip():
                return match[1].strip()
            if text.rstrip('：:') == label:
                if index + 1 < len(lines) and lines[index + 1].rstrip('：:') not in LABELS + ['能不能报', '经验要求', '适用届别']:
                    return lines[index + 1].strip()
                return 'unknown'
    return None


def safe_announcement(links, source):
    for href, text in links:
        if text == '查看原始公告':
            candidate = urljoin(source, href)
            if validate_url(candidate, 'announcement') and not PII.search(unquote(candidate)):
                return candidate
            return MARKER
    return MARKER  # absence of a captured anchor is not proof that no announcement exists


def automatic_row(html, url, obtained, ident, relative):
    visible = Visible()
    visible.feed(html)
    if RISK.search(''.join(visible.title + visible.parts)):
        raise StopCollection('RiskOrCaptchaPage')
    parsed, original_txt = parse_page(html, url, obtained, ident, relative)
    body = original_txt.split('\n', 3)[-1]
    lines = body.splitlines()
    output = {key: 'unknown' for key in COLUMNS}
    for chinese, internal in MAPPING.items():
        if internal in parsed:
            output[chinese] = source_value(parsed[internal])
    output.update(编号=ident, 详情页URL=url, 采集时间=obtained, 证据文件=relative, 单位性质=MARKER, 备注=MARKER)
    for key in ('岗位名称', '单位名称'):
        if output[key] == 'unknown':
            output[key] = MARKER
    output['公告URL'] = safe_announcement(visible.links, url)
    for chinese, labels in (
        ('招聘类型', ['招聘类型']), ('批次届别', ['批次届别', '适用届别']),
        ('工作地点', ['工作地点']), ('学历', ['学历要求']), ('专业', ['专业要求']),
        ('工作经验', ['工作经验', '经验要求']), ('学位', ['学位要求', '学位']),
        ('毕业时间', ['毕业时间']), ('政治面貌', ['政治面貌']), ('证书', ['证书要求', '证书']),
        ('年龄', ['年龄要求', '年龄']), ('其他限制', ['其他限制']),
    ):
        value = exact_label(lines, labels)
        if value is not None:
            output[chinese] = 'unknown' if any(phrase in value for phrase in UNKNOWN_PHRASES) else value
        elif output[chinese] == 'unknown':
            # Mark uncertainty if a relevant word exists outside a parsed label.
            output[chinese] = MARKER if any(label.replace('要求', '') in body for label in labels) else 'unknown'
    # No start time is inferred from publication, and no concrete deadline is filled on a human's behalf.
    start = exact_label(lines, ['报名开始'])
    output['报名开始'] = MARKER if start and not any(x in start for x in UNKNOWN_PHRASES) else 'unknown'
    end = exact_label(lines, ['报名截止'])
    output['报名截止'] = 'unknown' if end and any(x in end for x in UNKNOWN_PHRASES) else MARKER
    output['开放状态'] = MARKER
    if output['发布时间'] == 'unknown':
        published = exact_label(lines, ['发布时间'])
        output['发布时间'] = 'unknown' if published and any(x in published for x in UNKNOWN_PHRASES) else MARKER
    if parsed['condition_text'] == 'unknown' or parsed['evidence_excerpt'] == 'unknown':
        output['条件原文'], output['证据引用'] = MARKER, MARKER
    announcement = output['公告URL'] if output['公告URL'] != MARKER else 'unknown'
    # BATCH's first three metadata lines are retained, with an announcement provenance line added.
    evidence = '\n'.join(original_txt.split('\n')[:3]) + '\n# 公告URL：' + announcement + '\n' + body
    if PII.search(evidence) or any(PII.search(str(value)) for value in output.values()):
        raise ValueError('PIIRemaining')
    return output, evidence


def write_fill(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FILL_COLUMNS)
        writer.writeheader()
        writer.writerows({key: row[key] for key in FILL_COLUMNS} for row in rows)


def write_report(path, ledger, rows):
    lines = ['# 人工URL清单详情抓取报告', '',
             f'输入非空行{len(ledger["input_lines"])}；选中{ledger["selected"]}；实际请求{len(ledger["requests"])}；成功产出{len(rows)}；失败{ledger["failed"]}；未抓{ledger["not_requested"]}。',
             '停止原因：' + ledger['stop_reason'],
             '仅匿名只读清单详情；没有请求列表、sitemap、robots、API或公告页，没有使用Cookie，没有写processed。', '',
             '## 每条产物的待人工字段', '', '| 编号 | 岗位 | PENDING数 | PENDING列 |', '|---|---|---|---|']
    for row in rows:
        missing = [key for key, value in row.items() if value == MARKER]
        lines.append('| ' + ' | '.join((row['编号'], row['岗位名称'].replace('|', '／'), str(len(missing)), '、'.join(missing))) + ' |')
    lines.extend(['', '## 公告页人工核对清单（脚本没有请求这些URL）', ''])
    for row in rows:
        value = row['公告URL']
        lines.append('- ' + row['编号'] + '：' + (f'[{value}]({value})' if value not in ('unknown', MARKER) else 'PENDING，需本人从详情核对公告入口，不猜链接'))
    lines.extend(['', '## 非法、重复、超上限及未抓行', ''])
    for item in ledger['input_lines']:
        if item['result'] != 'selected':
            lines.append(f'- 原清单第{item["line"]}行：{item["result"]}；{item.get("reason", "unknown")}')
    attempted = {request['url'] for request in ledger['requests']}
    for item in ledger['input_lines']:
        if item['result'] == 'selected' and item['url'] not in attempted:
            lines.append(f'- 原清单第{item["line"]}行：因停止规则未请求')
    lines.extend(['', '## 失败详情', ''])
    for detail in ledger['details']:
        if detail['result'] != 'success':
            lines.append(f'- 原清单第{detail["line"]}行：HTTP {detail["http_status"]}；{detail.get("reason", "unknown")}')
    lines.extend(['', '## 解析率（成功产出行为分母，unknown与PENDING分别统计）', ''])
    for key in COLUMNS:
        concrete = sum(row[key] not in ('unknown', MARKER, '') for row in rows)
        pending_count = sum(row[key] == MARKER for row in rows)
        lines.append(f'- {key}：具体值{concrete}/{len(rows)}；PENDING={pending_count}；unknown={len(rows) - concrete - pending_count}')
    lines.extend(['', 'FILL_ME固定10列；若其他列仍有PENDING，须在28列auto表中人工补证据后填写，不能删标记或自动转unknown。',
                  '人工显式填写unknown表示本人确认未写；留空不能消除原PENDING。新增公告URL或更正岗位名称时，须同步维护证据元信息并补原文，脚本不伪造公告来源。',
                  '证据保留BATCH前三行并追加公告URL行；合并模式接受该有来源的四行格式，其他证据校验沿用G。'])
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=ROOT / 'data/raw/MANUAL_URLS.txt')
    parser.add_argument('--delay', type=float, default=1.5)
    args = parser.parse_args()
    if not 1.5 <= args.delay <= 60:
        parser.error('delay must be 1.5..60')
    targets, input_lines = read_urls(args.input)
    contact = os.environ.get('CAREER_COMPASS_CONTACT', '')
    if targets and not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', contact):
        parser.error('configure CAREER_COMPASS_CONTACT locally; value is never printed')
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    lock = raw / '.collect.lock'
    try:
        with lock.open('x', encoding='utf-8') as stream:
            stream.write(str(os.getpid()))
    except FileExistsError:
        print('STOP: collector lock exists; concurrent requests are prohibited')
        return 1
    batch = 'MANUAL-' + datetime.now(TZ).strftime('%Y%m%d-%H%M%S')
    directory = raw / (batch + '.pages')
    if directory.exists():
        lock.unlink()
        print('STOP: timestamp already used; existing evidence will not be overwritten')
        return 1
    directory.mkdir()
    ledger_path = raw / (batch + '.run.json')
    ua = f'Mozilla/5.0 (compatible; CareerCompass/0.1; contest-demo; contact:{contact})'
    ledger = {'batch': batch, 'started_at': now(), 'ended_at': 'unknown', 'auth_mode': 'anonymous',
              'ua': ua.replace(contact, '[REDACTED]') if contact else 'unknown', 'delay': args.delay,
              'selected': len(targets), 'input_lines': input_lines, 'requests': [], 'details': [], 'stop_reason': 'running'}
    fetch = Fetcher(ua, args.delay, ledger)
    fetch.on_update = lambda: atomic_json(ledger_path, ledger)
    rows = []
    def save():
        ledger.update(success=len(rows), failed=sum(d['result'] == 'failed' for d in ledger['details']), request_count=len(ledger['requests']),
                      http_success_count=sum(q['http_status'] == 200 for q in ledger['requests']), limit=30,
                      invalid_count=sum(item['result'] in ('invalid', 'missing') for item in input_lines), duplicate_count=sum(item['result'] == 'duplicate' for item in input_lines),
                      not_requested=len(targets) - len(ledger['requests']) + sum(item['result'] == 'over_limit' for item in input_lines),
                      pending_count=sum(value == MARKER for row in rows for value in row.values()),
                      field_parse_counts={key: sum(row[key] not in ('unknown', MARKER, '') for row in rows) for key in COLUMNS},
                      field_parse_rates={key: sum(row[key] not in ('unknown', MARKER, '') for row in rows) / len(rows) if rows else 0 for key in COLUMNS})
        write_csv(raw / (batch + '.auto.csv'), rows)
        write_fill(raw / (batch + '.FILL_ME.csv'), rows)
        atomic_json(ledger_path, ledger)
        write_report(ROOT / 'data' / (batch + '.REPORT.md'), ledger, rows)
    try:
        save()
        for index, (line, url) in enumerate(targets, 1):
            detail = {'line': line, 'url': url, 'http_status': 'unknown', 'result': 'requesting'}
            ledger['details'].append(detail)
            try:
                payload, entry = fetch.get(url)
            finally:
                if ledger['requests'] and ledger['requests'][-1]['url'] == url:
                    detail['http_status'] = ledger['requests'][-1]['http_status']
            if payload is None:
                detail.update(result='failed', reason=entry['error_type'])
                save()
                continue
            path = directory / f'{index:02d}.evidence.txt'
            try:
                row, evidence = automatic_row(payload.decode('utf-8'), url, entry['obtained_at'], f'{batch}-{index:02d}', path.relative_to(ROOT).as_posix())
                path.write_bytes(evidence.encode('utf-8'))
                rows.append(row)
                detail.update(result='success', evidence_path=row['证据文件'], evidence_hash=hashlib.sha256(evidence.encode('utf-8')).hexdigest(), pending_fields=[key for key, value in row.items() if value == MARKER], pending_count=sum(value == MARKER for value in row.values()))
            except (ValueError, UnicodeError) as exc:
                detail.update(result='failed', reason=type(exc).__name__)
            save()
            print(json.dumps({'line': line, 'http_status': detail['http_status'], 'result': detail['result'], 'pending': len(detail.get('pending_fields', []))}, ensure_ascii=False), flush=True)
        ledger['stop_reason'] = 'URLListCompleted'
    except StopCollection as exc:
        ledger['stop_reason'] = str(exc)
    except (OSError, ValueError):
        ledger['stop_reason'] = 'LocalOrParseFailure'
    except KeyboardInterrupt:
        ledger['stop_reason'] = 'Interrupted'
    finally:
        for detail in ledger['details']:
            if detail['result'] == 'requesting':
                detail.update(result='failed', reason=ledger['stop_reason'])
        ledger['ended_at'] = now()
        try:
            save()
        finally:
            lock.unlink()
    print(json.dumps({'run': ledger_path.relative_to(ROOT).as_posix(), 'success': len(rows), 'failed': ledger['failed'], 'not_requested': ledger['not_requested'], 'pending_count': ledger['pending_count'], 'processed_written': False}, ensure_ascii=False), flush=True)
    return 0 if ledger['stop_reason'] == 'URLListCompleted' else 1


if __name__ == '__main__':
    raise SystemExit(main())
