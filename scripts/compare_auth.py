"""Two read-only same-job requests. Credentials and response bodies never enter logs."""
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import urlsplit
from collect_jobs import ROOT, JOB, NoRedirect, Visible, allowed, now, parse_page

FIELDS = 'employer location recruitment_type salary published_at education degree major experience graduation_time political_status certificates age other_restrictions application_end condition_text'.split()
RISK = re.compile(r'验证码|安全验证|安全检查|安全检测|访问验证|完成验证|验证身份|访问异常|请求过于频繁|风控|captcha|verify you are human|access denied|security check', re.I)
LOGIN_PROMPTS = ('登录后可见', '登录后查看', '登录查看', '请先登录', '登录以查看')


class ComparisonStop(Exception):
    def __init__(self, reason, exit_code=4):
        self.reason, self.exit_code = reason, exit_code


def read_session():
    # This exact private path is the only credential source. Never return exported_at to a logger.
    try:
        value = json.loads((ROOT / 'data/private/session.json').read_text(encoding='utf-8-sig'))
        cookie = value['cookie']
        exported = value['exported_at']
        if not isinstance(cookie, str) or not cookie.strip() or any(c in cookie for c in ('\r', '\n', '\x00')) or cookie.lower().startswith('cookie:'):
            raise ValueError()
        cookie.encode('latin-1')
        if not isinstance(exported, str) or not exported.endswith('+08:00') or datetime.fromisoformat(exported).utcoffset().total_seconds() != 28800:
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, AttributeError):
        raise ComparisonStop('PrivateSessionMissingOrInvalid', 2) from None
    return cookie


def job_only(url):
    try:
        return bool(allowed(url) and JOB.fullmatch(urlsplit(url).path))
    except ValueError:
        return False


def inspect_body(payload, url):
    html = payload.decode('utf-8', errors='replace')
    visible = Visible()
    visible.feed(html)
    text = ''.join(visible.parts)
    # Inspect titles too, so a risk/login page whose body is hidden still cannot pass.
    risk_text = ''.join(visible.title) + text
    if RISK.search(risk_text):
        raise ComparisonStop('RiskOrCaptchaPage', 4)
    prompt = any(value in text for value in LOGIN_PROMPTS)
    try:
        row, evidence = parse_page(html, url, now(), 'AUTH-COMPARE', 'unknown')
    except (ValueError, UnicodeError):
        return {'fields': [], 'body_length': 0, 'login_prompt': prompt, 'deadline_unwritten': False, 'parsed': False}
    fields = []
    for field in FIELDS:
        value = row.get(field, 'unknown')
        if value != 'unknown' and value not in ('', [], {}):
            if field != 'condition_text' or len(value) >= 10:
                fields.append(field)
    # Persist aggregate metadata only, never a row, header, account UI, or body fragment.
    target = evidence.split('\n', 3)[-1]
    unwritten = bool(re.search(r'报名截止[：:]?\s*公告未写明', target))
    return {'fields': sorted(fields), 'body_length': len(target), 'login_prompt': prompt, 'deadline_unwritten': unwritten, 'parsed': True}


def fetch_once(opener, url, ua, cookie, entry):
    if not job_only(url):
        raise ComparisonStop('URLNotAllowed', 2)
    headers = {'User-Agent': ua}
    if cookie is not None:
        headers['Cookie'] = cookie
    try:
        request = urllib.request.Request(url, headers=headers, method='GET')
        with opener.open(request, timeout=20) as response:
            entry['http_status'] = response.status
            if response.status != 200:
                raise ComparisonStop('UnexpectedHTTPStatus', 4 if response.status in (401, 403, 429) or 300 <= response.status < 400 else 1)
            payload = response.read(4 * 1024 * 1024 + 1)
            if len(payload) > 4 * 1024 * 1024:
                raise ComparisonStop('ResponseSizeLimit', 1)
    except urllib.error.HTTPError as exc:
        entry['http_status'] = exc.code
        code = 4 if exc.code in (401, 403, 429) or 300 <= exc.code < 400 else 1
        exc.close()  # Do not read the error body or redirect Location.
        raise ComparisonStop('AuthOrHTTPStop', code) from None
    except (OSError, urllib.error.URLError, UnicodeError, ValueError):
        raise ComparisonStop('TransportFailure', 1) from None
    entry.update(inspect_body(payload, url))


def compare(url, ua, cookie):
    if not job_only(url):
        raise ComparisonStop('URLNotAllowed', 2)
    report = {'task': 'B05-E', 'source_url': url, 'started_at': now(), 'ended_at': 'unknown',
              'auth_mode': 'session-cookie', 'cookie_sha256_8': hashlib.sha256(cookie.encode('utf-8')).hexdigest()[:8],
              'session_validity': 'not_independently_verified', 'requests': [], 'decision': 'inconclusive',
              'added_fields': [], 'removed_fields': [], 'batch_authorized_by_comparison': False}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    exit_code = 0
    previous_completion = None
    try:
        for mode, credential in (('anonymous', None), ('session-cookie', cookie)):
            if previous_completion is not None:
                time.sleep(max(0, 2.0 - (time.monotonic() - previous_completion)))
            entry = {'auth_mode': mode, 'url': url, 'http_status': 'unknown', 'requested_at': now(),
                     'gap_after_previous_completion_seconds': round(time.monotonic() - previous_completion, 3) if previous_completion is not None else 'unknown'}
            report['requests'].append(entry)
            fetch_once(opener, url, ua, credential, entry)
            previous_completion = time.monotonic()
        anonymous, authenticated = report['requests']
        if not anonymous['parsed'] or not authenticated['parsed']:
            report['stop_reason'] = 'JobFieldsCouldNotBeCompared'
            exit_code = 1
        else:
            report['added_fields'] = sorted(set(authenticated['fields']) - set(anonymous['fields']))
            report['removed_fields'] = sorted(set(anonymous['fields']) - set(authenticated['fields']))
            report['body_length_delta'] = authenticated['body_length'] - anonymous['body_length']
            if report['added_fields']:
                report['decision'] = 'gain'
                report['batch_authorized_by_comparison'] = True
            elif authenticated['deadline_unwritten']:
                report['decision'] = 'no-gain'
            else:
                report['decision'] = 'no-new-fields'
                report['stop_reason'] = 'NoNewParseableFieldsDoNotStartBulk'
    except ComparisonStop as exc:
        report['stop_reason'], exit_code = exc.reason, exc.exit_code
    report['ended_at'] = now()
    report['request_count'] = len(report['requests'])
    return report, exit_code


def write_result(report):
    directory = ROOT / 'data/auth'
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    path = directory / ('AUTH-' + stamp + '.run.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# B05-E 登录差异验证', '', '采集使用了参赛者本人账号的登录态。此授权来自参赛者，不是站点许可。',
             '实际操作仅为同岗位匿名/带Cookie只读比较；登录数据不称为匿名公开数据。', '',
             '| 请求 | HTTP | 字段集合 | 正文长度 | 登录后可见提示 |', '|---|---|---|---|---|']
    for entry in report['requests']:
        lines.append('| ' + ' | '.join(str(value) for value in (entry['auth_mode'], entry['http_status'], ', '.join(entry.get('fields', [])) or '未解析', entry.get('body_length', 'unknown'), entry.get('login_prompt', 'unknown'))) + ' |')
    lines.extend(['', '新增字段：' + (', '.join(report['added_fields']) or '无'),
                  '减少字段：' + (', '.join(report['removed_fields']) or '无'),
                  '正文长度变化：' + str(report.get('body_length_delta', 'unknown')),
                  '判定：' + report['decision'], '停止原因：' + report.get('stop_reason', '无'),
                  '台账：' + path.relative_to(ROOT).as_posix(), '',
                  '本结果仅适用于该URL、本次提供的Cookie与当前响应；未独立验证Cookie会话有效性，不外推全站或永久状态。不保存响应正文、原始Cookie、Set-Cookie或个人账户信息。'])
    if report['decision'] == 'no-gain':
        lines.extend(['', '**登录不增加数据，放弃登录态采集。**', '登录响应截止仍为公告未写明，且无新增可解析字段；未改动批量逻辑，未运行第二阶段。'])
        destination = ROOT / 'AUTH_NO_GAIN.md'
    else:
        destination = ROOT / ('AUTH_GAIN.md' if report['decision'] == 'gain' else 'AUTH_COMPARE_STATUS.md')
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return destination


def run_compare(url, contact):
    try:
        if not job_only(url):
            raise ComparisonStop('URLNotAllowed', 2)
        cookie = read_session()
    except ComparisonStop as exc:
        print('STOP: ' + exc.reason + '; no comparison requests sent')
        return exc.exit_code
    ua = f'Mozilla/5.0 (compatible; CareerCompass/0.1; contest-demo; contact:{contact})'
    report, exit_code = compare(url, ua, cookie)
    result = write_result(report)
    for entry in report['requests']:
        print(json.dumps({key: entry.get(key, 'unknown') for key in ('auth_mode', 'http_status', 'fields', 'body_length', 'login_prompt')}, ensure_ascii=False))
    print(json.dumps({'decision': report['decision'], 'added_fields': report['added_fields'], 'body_length_delta': report.get('body_length_delta', 'unknown'), 'request_count': report['request_count'], 'report': result.relative_to(ROOT).as_posix(), 'exit_code': exit_code}, ensure_ascii=False))
    return exit_code
