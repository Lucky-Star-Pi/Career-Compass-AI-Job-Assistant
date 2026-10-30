"""Loopback-only production smoke; no model key, no paid calls, no cookie logging."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request


def main():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop('DEEPSEEK_API_KEY', None)
    env.pop('PROFILE_COOKIE_SECRET', None)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    server = subprocess.Popen(['node', str(root / 'node_modules/next/dist/bin/next'),
                               'start', '-H', '127.0.0.1', '-p', '3107'],
                              cwd=root, env=env, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    def call(path, method='GET', body=None, cookie=None):
        headers = {'Content-Type': 'application/json'}
        if cookie:
            headers['Cookie'] = cookie
        req = urllib.request.Request('http://127.0.0.1:3107' + path,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers, method=method)
        try:
            response = opener.open(req, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        return response.status, response.headers, response.read()

    try:
        for _ in range(80):
            try:
                status, _, body = call('/api/health')
                if status == 200:
                    break
            except (OSError, urllib.error.URLError):
                time.sleep(.25)
        else:
            raise AssertionError('server did not become ready')
        health = json.loads(body)
        assert health['data_count'] == 10 and health['model'] == '未接通'
        print('PASS health: data_count=10; model=未接通')
        status, _, body = call('/')
        assert status == 200 and '职点迷津'.encode() in body
        print('PASS production home: HTTP 200')
        profile = {'confirmed': True, 'education': '本科', 'major': '计算机类',
                   'graduationYear': 2027, 'certificates': []}
        status, headers, _ = call('/api/profile', 'POST', profile)
        assert status == 200
        token = headers['Set-Cookie']
        assert 'HttpOnly' in token and 'SameSite=Lax' in token
        cookie = token.split(';')[0]
        status, _, body = call('/api/profile', cookie=cookie)
        assert status == 200 and json.loads(body) == profile
        print('PASS signed cookie: roundtrip and privacy flags')
        name, value = cookie.split('=', 1)
        tampered = name + '=' + ('A' if value[0] != 'A' else 'B') + value[1:]
        _, _, body = call('/api/profile', cookie=tampered)
        assert json.loads(body) == {'confirmed': False}
        print('PASS tampered cookie: unconfirmed')
        status, _, _ = call('/api/profile', 'POST', {**profile, 'name': '测试输入'})
        assert status == 400
        print('PASS identity fields: rejected')
        _, _, body = call('/api/chat', 'POST', {'question': '还有哪些条件需要核实？'}, cookie)
        answer = json.loads(body)
        assert answer['connected'] is False and answer['model_status'] == '未接通'
        assert all(r['job_id'] and r['source_url'] for r in answer['references'])
        print('PASS missing-key chat: connected=false; 未接通; no paid request')
        status, headers, _ = call('/api/profile', 'DELETE')
        assert status == 200 and 'Max-Age=0' in headers['Set-Cookie']
        print('PASS clear conditions: cookie expires')
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


if __name__ == '__main__':
    main()
