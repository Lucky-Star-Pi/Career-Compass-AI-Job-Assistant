"""Real chat guard acceptance, synthetic accounts only; never prints credentials.

Local mode starts an isolated production build, makes three real model requests,
then restarts with an invalid DeepSeek key and Qwen disabled to verify rules.
--online uses a fresh synthetic account and only asks questions 1 and 3.
"""
import argparse
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

QUESTIONS = ['央国企校招一般什么时候开始？', '这个岗位我能报吗？', '我是2027届本科，国际商务类，想留湛江']
APP = Path(__file__).resolve().parents[1]
JOBS = json.loads((APP / 'lib/jobs.json').read_text('utf-8'))


def client():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                      urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(opener, base, path, body=None):
    request = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Content-Type': 'application/json', 'Origin': base})
    try:
        response = opener.open(request, timeout=40)
    except urllib.error.HTTPError as error:
        response = error
    return response.status, json.loads(response.read())


def account(opener, base):
    assert call(opener, base, '/api/auth/register', {'username': 'guard' + secrets.token_hex(5),
                                                  'password': secrets.token_hex(20)})[0] == 200


def ask(opener, base, number, expected):
    started = time.monotonic()
    status, output = call(opener, base, '/api/chat', {'question': QUESTIONS[number - 1]})
    refs = output.get('references', [])
    print(json.dumps({'question': number, 'HTTP': status, 'mode': output.get('mode'),
                      'seconds': round(time.monotonic() - started, 2), 'references': len(refs),
                      'reply': output.get('reply'), 'profile_updates': output.get('profile_updates')}, ensure_ascii=False), flush=True)
    assert status == 200 and output.get('mode') in expected
    assert 'status' not in output
    assert all(any(ref['job_id'] == job['id'] and ref['source_url'] == job['source_url'] for job in JOBS) for ref in refs)
    assert not any(phrase in output['reply'] for phrase in ['保证' + '能报', '一定' + '能报'])
    if expected == ['deepseek']:
        assert output.get('connected') is True and 0 < len(output['reply']) < 300
        if number == 3:
            assert 1 <= len(refs) <= 5
    else:
        assert output['reply'].startswith('小职正在升级中')


def start(base, directory, invalid=False):
    env = os.environ.copy()
    env.pop('DEEPSEEK_API_KEY', None)  # Next reads its existing local environment; never export its value.
    env.update(USER_DATA_DIR=str(directory), PROFILE_COOKIE_SECRET=secrets.token_hex(32), NEXT_TELEMETRY_DISABLED='1')
    if invalid:
        env.update(DEEPSEEK_API_KEY='invalid-synthetic-guard-check', DASHSCOPE_API_KEY='')
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
        env.pop(key, None)
    process = subprocess.Popen(['node', str(APP / 'node_modules/next/dist/bin/next'), 'start',
                                '-H', '127.0.0.1', '-p', '3119'], cwd=APP, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        if process.poll() is not None:
            raise AssertionError('isolated server exited')
        try:
            if call(client(), base, '/api/health')[0] == 200:
                return process
        except OSError:
            time.sleep(.25)
    stop(process)
    raise AssertionError('isolated server readiness timeout')


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--online', action='store_true')
    args = parser.parse_args()
    base = 'http://118.89.79.239:3000' if args.online else 'http://127.0.0.1:3119'
    directory = None
    server = None
    try:
        if not args.online:
            private = APP.parent / 'data/private'
            private.mkdir(parents=True, exist_ok=True)
            directory = Path(tempfile.mkdtemp(prefix='reply-guard-', dir=private))
            server = start(base, directory)
        opener = client()
        account(opener, base)
        for number in ([1, 3] if args.online else [1, 2, 3]):
            ask(opener, base, number, ['deepseek'])
        if not args.online:
            stop(server)
            server = start(base, directory, invalid=True)
            opener = client()
            account(opener, base)
            ask(opener, base, 1, ['qwen', 'rules'])
        print('PASS reply-guard acceptance' + (' online' if args.online else ' local including invalid key'), flush=True)
    finally:
        if server is not None:
            stop(server)


if __name__ == '__main__':
    main()
