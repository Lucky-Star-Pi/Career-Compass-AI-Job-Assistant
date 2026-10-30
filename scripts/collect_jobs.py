"""CO-002: bounded serial public-detail collection; no HTML persisted or printed."""
import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from csv_records import COLUMNS, read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.zhidianmijin.com.cn'
TZ = timezone(timedelta(hours=8))
LABELS = ['报名截止', '招聘类型', '工作地点', '薪资待遇', '发布时间', '学历要求', '专业要求', '岗位介绍']
JOB = re.compile(r'/jobs/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
SITEMAP = re.compile(r'/sitemaps/jobs-[A-Za-z0-9_-]+\.xml')
UNKNOWN_PHRASES = ('公告未写明', '长期招聘')


def now():
    return datetime.now(TZ).isoformat(timespec='seconds')


def allowed(url):
    try:
        u = urlsplit(url)
        return (u.scheme == 'https' and u.netloc == 'www.zhidianmijin.com.cn' and not u.query and not u.fragment
                and (u.path in ('/robots.txt', '/sitemap.xml') or JOB.fullmatch(u.path) or SITEMAP.fullmatch(u.path)))
    except ValueError:
        return False


def redact(text):
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[REDACTED]', text)
    text = re.sub(r'(?<!\d)(?:1[3-9]\d{9}|\d{17}[\dXx])(?!\d)', '[REDACTED]', text)
    text = re.sub(r'(?<!\d)0\d{2,3}[- ]?\d{7,8}(?!\d)', '[REDACTED]', text)
    return re.sub(r'(?:联系方式|联系电话|手机号码|身份证号|通讯地址|家庭住址)[：:]?[^\n]*', '[REDACTED]', text)


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []
        self.headings = []
        self.title = []
        self.links = []
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = any(x[1] for x in self.stack) or tag in ('script', 'style', 'noscript', 'header', 'footer', 'nav') or 'hidden' in attrs or attrs.get('aria-hidden') == 'true' or bool(re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', attrs.get('style', ''), re.I))
        if tag not in ('meta', 'link', 'img', 'br', 'hr', 'input', 'source', 'wbr', 'area', 'base', 'embed', 'param', 'track', 'col'):
            self.stack.append((tag, hidden))
        if re.fullmatch('h[1-6]', tag) and not hidden:
            self.headings.append((len(self.parts), int(tag[1])))
        if tag == 'a' and not hidden:
            self.anchor = [attrs.get('href', ''), []]

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor:
            self.links.append((self.anchor[0], ''.join(self.anchor[1]).strip()))
            self.anchor = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        text = re.sub(r'\s+', ' ', data).strip()
        if not text:
            return
        if any(tag == 'title' for tag, _ in self.stack):
            self.title.append(text)
            return
        if self.stack and not any(hidden for _, hidden in self.stack):
            self.parts.append(text)
            if self.anchor:
                self.anchor[1].append(text)


def parse_page(html, url, obtained_at, ident, evidence_path):
    parser = Visible()
    parser.feed(html)
    pieces = [redact(x) for x in parser.parts]
    title_parts = [x.strip() for x in redact(''.join(parser.title)).split('｜')]
    names = title_parts[:2] if len(title_parts) == 3 and title_parts[-1] == '职点迷津' else ('unknown', 'unknown')
    return parse_visible(pieces, parser.headings, names, parser.links, url, obtained_at, ident, evidence_path)


def parse_visible(pieces, headings, names, links, url, obtained_at, ident, evidence_path):
    """Parse observed visible text; offline corrections never refetch or invent DOM."""
    matches = {}
    for label in LABELS:
        for i, text in enumerate(pieces):
            if re.match('^' + re.escape(label) + r'(?:[：:]|$)', text):
                matches[label] = i
                break
    ordered = [matches[x] for x in LABELS if x in matches]
    if ordered != sorted(ordered) or '报名截止' not in matches or '岗位介绍' not in matches:
        raise ValueError('RequiredEvidenceBoundaryMissingOrOrderConflict')
    intro = matches['岗位介绍']
    intro_level = next((level for index, level in headings if index == intro), None)
    end = next((index for index, level in headings if index > intro and (intro_level is None or level <= intro_level)), len(pieces))
    # Observed action/privacy sections are outside the job introduction.
    end = min(end, next((i for i in range(intro + 1, len(pieces)) if pieces[i] in ('查看原始公告', '问题反馈', '帮助我们把求职体验做得更好')), len(pieces)))
    fields, spans = {}, {}
    for n, label in enumerate(LABELS):
        if label not in matches:
            fields[label] = 'unknown'
            continue
        start = matches[label]
        stop = next((matches[x] for x in LABELS[n + 1:] if x in matches), end)
        if label == '岗位介绍':
            stop = end
        else:
            # Exact auxiliary labels terminate values, but NEVER replace missing requested labels.
            stop = min(stop, next((i for i in range(start + 1, stop) if pieces[i] in ('能不能报', '经验要求', '适用届别', '学历', '专业', '要求')), stop))
        value = '\n'.join(pieces[start:stop])
        value = re.sub('^' + label + r'[：:]?\s*', '', value).strip()
        fields[label] = 'unknown' if not value or any(x in value for x in UNKNOWN_PHRASES) else value
        spans[label] = (start, stop)
    name, employer = names
    if employer != 'unknown' and re.fullmatch(r'[^｜]*(?:省|市|区|县)', employer):
        employer = 'unknown'  # observed title second segment is a region, not proven employer
    evidence = '\n'.join(pieces[matches['报名截止']:end]).strip()
    condition_start = next((matches[x] for x in ('学历要求', '专业要求', '岗位介绍') if x in matches), intro)
    condition = '\n'.join(pieces[condition_start:end]).strip()
    sentences = [x.strip() for x in re.split(r'(?<=[。；;！？])|\n', condition) if len(x.strip()) >= 8 and x.strip() not in LABELS]
    excerpt = min(sentences, key=len) if sentences else condition
    announcement = 'unknown'
    for href, text in links:
        if text == '查看原始公告':
            target = urljoin(url, href)
            u = urlsplit(target)
            if u.scheme == 'https' and u.hostname in ('zhidianmijin.com.cn', 'www.zhidianmijin.com.cn') and not u.query and not u.fragment and not u.username and not u.password and not u.path.startswith('/api/'):
                announcement = target
            break
    row = {k: 'unknown' for k in COLUMNS}
    row.update(id=ident, name=name or 'unknown', employer=employer or 'unknown', source_url=url, announcement_url=announcement,
               obtained_at=obtained_at, raw_snapshot=evidence_path, condition_text=condition or 'unknown', evidence_excerpt=excerpt or 'unknown',
               open_status='unknown', is_fixture=False, conditions=[], evidence_metadata={'url': url, 'obtained_at': obtained_at, 'http_status': 200, 'screenshot_path': 'unknown'})
    mapping = {'招聘类型': 'recruitment_type', '工作地点': 'location', '薪资待遇': 'salary', '学历要求': 'education', '专业要求': 'major'}
    for label, key in mapping.items():
        value = fields[label]
        row[key] = {'raw': value, 'normalized': 'unknown', 'evidence_ref': evidence_path} if key in ('education', 'major') and value != 'unknown' else value
    for label, key in (('报名截止', 'application_end'), ('发布时间', 'published_at')):
        value = fields[label]
        date_match = re.search(r'(20\d{2})[年/.-](\d{1,2})[月/.-](\d{1,2})日?', value)
        if date_match:
            try:
                day = datetime(*map(int, date_match.groups()), tzinfo=TZ).date()
                row[key] = {'raw': value, 'normalized': day.isoformat(), 'precision': 'date', 'timezone': '+08:00'}
                if key == 'application_end':
                    today = datetime.fromisoformat(obtained_at).date()
                    row['open_status'] = 'open' if day > today else 'closed' if day < today else 'unknown'
            except ValueError:
                pass
    for label, key in (('工作经验', 'experience'), ('其他限制', 'other_restrictions')):
        match = re.search(r'(?:^|[ \t\n])' + label + r'[：:][ \t]*([^\n]+)', condition)
        if match and not any(x in match[1] for x in UNKNOWN_PHRASES):
            row[key] = {'raw': match[1], 'normalized': 'unknown', 'evidence_ref': evidence_path}
    row['missing_fields'] = sorted({k for k, value in row.items() if k != 'missing_fields' and value == 'unknown'} | {x for x in LABELS if fields[x] == 'unknown'})
    txt = '# 岗位名：' + row['name'] + '\n# URL：' + url + '\n# 获取时间：' + obtained_at + '\n' + evidence + '\n'
    if condition not in txt or excerpt not in txt:
        raise ValueError('EvidenceSubstringMismatch')
    return row, txt


def reparse_saved_preview(csv_path):
    """Offline correction of an unapproved preview, preserving fetch facts and old hashes."""
    ledger_path = csv_path.with_name(csv_path.name.replace('.records.csv', '.run.json'))
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    if ledger['mode'] != 'dry-run-live-preview':
        raise ValueError('Only unapproved dry-run previews may be reparsed')
    corrected, revisions = [], []
    for old in read_csv(csv_path):
        path = ROOT / old['raw_snapshot']
        original = path.read_bytes()
        parts = original.decode('utf-8').splitlines()[3:]
        row, txt = parse_visible(parts, [], (old['name'], old['employer']), [], old['source_url'], old['obtained_at'], old['id'], old['raw_snapshot'])
        # The previous captured href was already sanitized; no new source is inferred.
        row['announcement_url'] = old['announcement_url']
        if row['announcement_url'] != 'unknown':
            row['missing_fields'] = [x for x in row['missing_fields'] if x != 'announcement_url']
        payload = txt.encode('utf-8')
        path.write_bytes(payload)
        revisions.append({'url': row['source_url'], 'previous_evidence_hash': hashlib.sha256(original).hexdigest(), 'evidence_hash': hashlib.sha256(payload).hexdigest(), 'reason': 'offline visible-text boundary correction; no network request'})
        detail = next(x for x in ledger['details'] if x['url'] == row['source_url'])
        detail.update(evidence_hash=hashlib.sha256(payload).hexdigest(), length_warning=not 300 <= len(txt.split('\n', 3)[-1]) <= 800, human_review_required=True)
        corrected.append(row)
    write_csv(csv_path, corrected)
    ledger.setdefault('offline_revisions', []).append({'reparsed_at': now(), 'parser': 'visible-boundary-v2', 'records': revisions})
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return corrected


class StopCollection(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Fetcher:
    def __init__(self, ua, delay, ledger):
        self.ua, self.delay, self.ledger = ua, delay, ledger
        self.last = None
        self.non200 = 0
        self.robots = None
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(self, url):
        if not allowed(url):
            raise StopCollection('URLNotAllowed')
        if self.robots and not self.robots.can_fetch(self.ua, url):
            raise StopCollection('RobotsDisallowed')
        if self.last is not None:
            time.sleep(max(0, self.delay - (time.monotonic() - self.last)))
        entry = {'url': url, 'http_status': 'unknown', 'error_type': 'unknown', 'obtained_at': now()}
        entry['gap_after_previous_completion_seconds'] = round(time.monotonic() - self.last, 3) if self.last is not None else 'unknown'
        self.ledger['requests'].append(entry)
        payload = None
        try:
            request = urllib.request.Request(url, headers={'User-Agent': self.ua})
            with self.opener.open(request, timeout=20) as response:
                entry['http_status'] = response.status
                if response.status == 200:
                    payload = response.read(4 * 1024 * 1024 + 1)
                    if len(payload) > 4 * 1024 * 1024:
                        payload = None
                        entry['error_type'] = 'ResponseSizeLimit'
        except urllib.error.HTTPError as exc:
            entry['http_status'] = exc.code
            entry['error_type'] = 'HTTPError'
            exc.close()
        except (OSError, urllib.error.URLError) as exc:
            entry['error_type'] = type(exc).__name__
        finally:
            self.last = time.monotonic()
        self.non200 = 0 if entry['http_status'] == 200 else self.non200 + 1
        if entry['http_status'] in (403, 429) or self.non200 >= 2:
            raise StopCollection('HTTPStopRule')
        return payload, entry


def locations(payload):
    if not payload or b'<!DOCTYPE' in payload.upper():
        return []
    root = ET.fromstring(payload)
    return [element.text.strip() for element in root.iter() if element.tag.rsplit('}', 1)[-1] == 'loc' and element.text and allowed(element.text.strip())]


def run_main():
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=30)
    p.add_argument('--delay', type=float, default=1.5)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    if not 1 <= args.limit <= 50 or not 1.5 <= args.delay <= 60 or (args.dry_run and args.limit > 3):
        p.error('limit must be 1..50 (dry-run <=3); delay must be 1.5..60')
    contact = os.environ.get('CAREER_COMPASS_CONTACT', '')
    if not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', contact):
        p.error('configure local CAREER_COMPASS_CONTACT with public role address; value is never logged')
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    batch = 'AUTO-' + datetime.now(TZ).strftime('%Y%m%d-%H%M')
    ledger_path = raw / (batch + '.run.json')
    if ledger_path.exists():
        p.error('run name already exists this minute; do not overwrite evidence')
    ua = 'Mozilla/5.0 (compatible; CareerCompass/0.1; contest-demo; contact:' + contact + ')'
    ledger = {'batch': batch, 'started_at': now(), 'ended_at': 'unknown', 'mode': 'dry-run-live-preview' if args.dry_run else 'live', 'delay': args.delay, 'ua': ua.replace(contact, '[REDACTED]'), 'limit': args.limit, 'robots': 'unknown', 'requests': [], 'details': [], 'stop_reason': 'unknown'}
    fetch = Fetcher(ua, args.delay, ledger)
    index_path = raw / 'collect-index.jsonl'
    seen = set()
    if index_path.exists():
        seen = {json.loads(line)['url'] for line in index_path.read_text(encoding='utf-8').splitlines() if line.strip()}
    rows = []
    try:
        payload, entry = fetch.get(BASE + '/robots.txt')
        if not payload:
            raise StopCollection('RobotsUnavailable')
        robot = urllib.robotparser.RobotFileParser()
        robot_text = payload.decode('utf-8')
        if not re.search(r'(?im)^user-agent\s*:', robot_text):
            raise StopCollection('RobotsInvalidText')
        robot.parse(robot_text.splitlines())
        fetch.robots = robot
        ledger['robots'] = {'http_status': entry['http_status'], 'checked_at': entry['obtained_at'], 'api_allowed': robot.can_fetch(ua, BASE + '/api/'), 'sitemap_allowed': robot.can_fetch(ua, BASE + '/sitemap.xml'), 'applicable_policy': 'hard-deny /api/ regardless of robots', 'rules': [redact(line) for line in robot_text.splitlines() if re.match(r'(?i)^(user-agent|allow|disallow|sitemap)\s*:', line)]}
        payload, _ = fetch.get(BASE + '/sitemap.xml')
        entries = locations(payload)
        jobs = [u for u in entries if JOB.fullmatch(urlsplit(u).path)]
        maps = [u for u in entries if SITEMAP.fullmatch(urlsplit(u).path)][:3]
        for sitemap in maps:
            if len([u for u in set(jobs) if u not in seen]) >= args.limit:
                break
            payload, _ = fetch.get(sitemap)
            jobs.extend(u for u in locations(payload) if JOB.fullmatch(urlsplit(u).path))
        targets = list(dict.fromkeys(u for u in jobs if u not in seen))[:args.limit]
        if not targets:
            ledger['stop_reason'] = 'NoUnseenAllowedJobsInBoundedSitemaps'
        for number, url in enumerate(targets, 1):
            detail = {'url': url, 'http_status': 'unknown', 'result': 'failed', 'reason': 'unknown'}
            ledger['details'].append(detail)
            payload = None
            try:
                payload, entry = fetch.get(url)
            finally:
                if fetch.ledger['requests'][-1]['url'] == url:
                    entry = fetch.ledger['requests'][-1]
                    detail['http_status'] = entry['http_status']
                    with index_path.open('a', encoding='utf-8', newline='\n') as stream:
                        stream.write(json.dumps({'url': url, 'obtained_at': entry['obtained_at'], 'http_status': entry['http_status'], 'batch': batch}, ensure_ascii=False) + '\n')
            if payload is None:
                detail['reason'] = entry['error_type']
                continue
            evidence_path = 'data/raw/' + batch + '-' + str(number).zfill(2) + '.evidence.txt'
            try:
                row, txt = parse_page(payload.decode('utf-8'), url, entry['obtained_at'], 'AUTO-' + str(number).zfill(2), evidence_path)
                (ROOT / evidence_path).write_bytes(txt.encode('utf-8'))
                rows.append(row)
                detail.update(result='success', reason='unknown', evidence_path=evidence_path, evidence_hash=hashlib.sha256(txt.encode('utf-8')).hexdigest(), length_warning=not 300 <= len(txt.split('\n', 3)[-1]) <= 800, human_review_required=True)
                if args.dry_run:
                    print(json.dumps(row, ensure_ascii=False))
            except (ValueError, UnicodeError) as exc:
                detail.update(result='excluded', reason=str(exc) if str(exc) in ('RequiredEvidenceBoundaryMissingOrOrderConflict', 'EvidenceSubstringMismatch') else type(exc).__name__)
    except (StopCollection, ET.ParseError, OSError, ValueError) as exc:
        ledger['stop_reason'] = str(exc) if isinstance(exc, StopCollection) else type(exc).__name__
    finally:
        write_csv(raw / (batch + '.records.csv'), rows)
        for detail in ledger['details']:
            if detail['result'] == 'failed' and detail['reason'] == 'unknown':
                detail['reason'] = ledger['stop_reason']
        ledger.update(ended_at=now(), request_count=len(ledger['requests']), request_success_count=sum(x['http_status'] == 200 for x in ledger['requests']), request_failure_count=sum(x['http_status'] != 200 for x in ledger['requests']), success_count=len(rows), failure_count=sum(x['result'] == 'failed' for x in ledger['details']), excluded_count=sum(x['result'] == 'excluded' for x in ledger['details']))
        ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'run': ledger_path.relative_to(ROOT).as_posix(), 'success': len(rows), 'stop_reason': ledger['stop_reason'], 'processed_written': False}, ensure_ascii=False))
    return 0 if rows and ledger['stop_reason'] == 'unknown' else 1


def main():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    lock_path = raw / '.collect.lock'
    try:
        with lock_path.open('x', encoding='utf-8') as lock:
            lock.write(str(os.getpid()))
    except FileExistsError:
        print('STOP: collector lock exists; no concurrent run allowed; inspect before manual recovery')
        return 1
    try:
        return run_main()
    finally:
        lock_path.unlink()


if __name__ == '__main__':
    raise SystemExit(main())
