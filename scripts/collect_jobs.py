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
from datetime import date, datetime, timedelta, timezone
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
BASE_DAY = date(2026, 10, 30)
OPEN_DAY = date(2026, 10, 31)
PREFERRED_DAY = date(2026, 11, 7)


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
    text = re.sub(r'(?<!\d)(?:\d{11}|\d{17}[\dXx])(?!\d)', '[REDACTED]', text)
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
        self.part_paths = []
        self.node_number = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.node_number += 1
        hidden = any(x[1] for x in self.stack) or tag in ('script', 'style', 'noscript', 'footer', 'nav') or (tag == 'header' and not any(x[0] == 'main' for x in self.stack)) or 'hidden' in attrs or attrs.get('aria-hidden') == 'true' or bool(re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', attrs.get('style', ''), re.I))
        if tag not in ('meta', 'link', 'img', 'br', 'hr', 'input', 'source', 'wbr', 'area', 'base', 'embed', 'param', 'track', 'col'):
            self.stack.append((tag, hidden, self.node_number))
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
        if any(x[0] == 'title' for x in self.stack):
            self.title.append(text)
            return
        if self.stack and not any(x[1] for x in self.stack):
            self.parts.append(text)
            self.part_paths.append([(tag, node) for tag, _, node in self.stack])
            if self.anchor:
                self.anchor[1].append(text)


def parse_page(html, url, obtained_at, ident, evidence_path):
    parser = Visible()
    parser.feed(html)
    pieces, remap = [], {}
    i = 0
    while i < len(parser.parts):
        remap[i] = len(pieces)
        text = redact(parser.parts[i])
        if text in ('学历', '专业') and i + 1 < len(parser.parts) and parser.parts[i + 1] == '要求':
            common = [x for x in parser.part_paths[i] if x in parser.part_paths[i + 1]]
            if any(tag in ('dt', 'label', 'p', 'h2', 'h3') for tag, _ in common) or (common and common[-1] == parser.part_paths[i][-1]):
                remap[i + 1] = len(pieces)
                text += '要求'
                i += 1
        pieces.append(text)
        i += 1
    title_parts = [x.strip() for x in redact(''.join(parser.title)).split('｜')]
    names = title_parts[:2] if len(title_parts) == 3 and title_parts[-1] == '职点迷津' else ('unknown', 'unknown')
    deadline = next((i for i, part in enumerate(pieces) if part.rstrip('：:') == '报名截止'), len(pieces))
    headings = [(remap[index], level) for index, level in parser.headings if index in remap]
    h1 = next((index for index, level in headings if level == 1), None)
    body_employer = None
    preamble = pieces[:deadline]
    if names[1] != 'unknown' and names[1] in preamble and not re.fullmatch(r'[^｜]*(?:省|市|区|县)', names[1]):
        body_employer = names[1]
    for index, part in enumerate(preamble):
        if part.rstrip('：:') in ('单位', '招聘单位', '单位名称') and index + 1 < len(preamble):
            body_employer = preamble[index + 1]
            break
    if body_employer is None and h1 is not None:
        for part in pieces[h1 + 1:min(h1 + 7, deadline)]:
            if re.search(r'(有限公司|有限责任公司|集团|银行|研究院|研究所|大学|学院|中心|委员会|管理局|分公司|总公司|公司|厂)$', part):
                body_employer = part
                break
    names = (names[0], body_employer or 'unknown')
    try:
        return parse_visible(pieces, headings, names, parser.links, url, obtained_at, ident, evidence_path)
    except ValueError as exc:
        exc.visible_parts = pieces
        exc.visible_headings = headings
        exc.observed_names = names
        raise


def parse_visible(pieces, headings, names, links, url, obtained_at, ident, evidence_path):
    """Parse observed visible text; offline corrections never refetch or invent DOM."""
    matches = {}
    deadline_index = next((i for i, text in enumerate(pieces) if re.match(r'^报名截止(?:[：:]|$)', text)), None)
    if deadline_index is None:
        raise ValueError('DeadlineLabelMissing')
    for label in LABELS:
        for i, text in enumerate(pieces):
            if i >= deadline_index and re.match('^' + re.escape(label) + r'(?:[：:]|$)', text):
                matches[label] = i
                break
    # Some actual pages omit the introduction entirely. Keep it unknown, never synthesize it.
    intro = matches.get('岗位介绍', matches['报名截止'])
    intro_level = next((level for index, level in headings if index == intro), None)
    end = next((index for index, level in headings if index > intro and (intro_level is None or level <= intro_level)), len(pieces)) if '岗位介绍' in matches else len(pieces)
    # Observed action/privacy sections are outside the job introduction.
    end = min(end, next((i for i in range(intro + 1, len(pieces)) if pieces[i] in ('查看原始公告', '问题反馈', '帮助我们把求职体验做得更好')), len(pieces)))
    if '岗位介绍' not in matches:
        end = min(end, next((i for i in range(matches['报名截止'] + 1, end) if pieces[i].startswith('选好学历和专业') or pieces[i] == '在列表里为这个岗位选条件'), end))
    fields, spans = {}, {}
    for n, label in enumerate(LABELS):
        if label not in matches:
            fields[label] = 'unknown'
            continue
        start = matches[label]
        stop = min((position for position in matches.values() if position > start), default=end)
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
    employer_position = next((i for i in range(matches['报名截止']) if pieces[i] == employer and employer != 'unknown'), matches['报名截止'])
    evidence = '\n'.join(pieces[employer_position:end]).strip()
    condition_start = min((matches[x] for x in ('学历要求', '专业要求', '岗位介绍') if x in matches), default=end)
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
                    row['open_status'] = 'open' if day >= OPEN_DAY else 'closed'
            except ValueError:
                pass
    for label, key in (('工作经验', 'experience'), ('其他限制', 'other_restrictions')):
        match = re.search(r'(?:^|[ \t\n])' + label + r'[：:][ \t]*([^\n]+)', condition)
        if match and not any(x in match[1] for x in UNKNOWN_PHRASES):
            row[key] = {'raw': match[1], 'normalized': 'unknown', 'evidence_ref': evidence_path}
    row['missing_fields'] = sorted({k for k, value in row.items() if k != 'missing_fields' and value == 'unknown'} | {x for x in LABELS if fields[x] == 'unknown'})
    txt = '# 岗位名：' + row['name'] + '\n# URL：' + url + '\n# 获取时间：' + obtained_at + '\n' + evidence + '\n'
    if condition and (condition not in txt or excerpt not in txt):
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
        self.on_update = None
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
        if self.on_update:
            self.on_update()
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
            if self.on_update:
                self.on_update()
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
    if not 1 <= args.limit <= 150 or not 1.5 <= args.delay <= 60 or (args.dry_run and args.limit > 3):
        p.error('limit must be 1..150 (dry-run <=3); delay must be 1.5..60')
    contact = os.environ.get('CAREER_COMPASS_CONTACT', '')
    if not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', contact):
        p.error('configure local CAREER_COMPASS_CONTACT with public role address; value is never logged')
    from batch_jobs import run_batch
    return run_batch(args, contact)


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
