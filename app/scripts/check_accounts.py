"""Local account-isolation acceptance. All credentials/data are synthetic and private."""
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


def main():
    app = Path(__file__).resolve().parents[1]
    private = app.parent / 'data/private'
    private.mkdir(parents=True, exist_ok=True)
    data_dir = Path(tempfile.mkdtemp(prefix='r4-http-', dir=private))
    env = os.environ.copy()
    env.update(USER_DATA_DIR=str(data_dir), DEEPSEEK_API_KEY='',
               PROFILE_COOKIE_SECRET=secrets.token_hex(32), NEXT_TELEMETRY_DISABLED='1')
    base = 'http://127.0.0.1:3113'
    def client():
        return urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                          urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(opener, path, body=None, method=None):
        request = urllib.request.Request(base + path,
                                         data=json.dumps(body).encode() if body is not None else None,
                                         headers={'Content-Type': 'application/json'}, method=method)
        try:
            response = opener.open(request, timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        raw = response.read()
        return response.status, response.headers, json.loads(raw) if raw.startswith(b'{') else raw
    def start():
        process = subprocess.Popen(['node', str(app / 'node_modules/next/dist/bin/next'),
                                    'start', '-H', '127.0.0.1', '-p', '3113'],
                                   cwd=app, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(80):
            if process.poll() is not None:
                raise AssertionError('local server exited')
            try:
                if call(client(), '/api/health')[0] == 200:
                    return process
            except OSError:
                time.sleep(.25)
        raise AssertionError('local server readiness timeout')
    def stop(process):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    server = start()
    try:
        anonymous = client()
        for path, body in [('/api/me', None), ('/api/profile', None), ('/api/chat', {'question': '测试问题'})]:
            assert call(anonymous, path, body)[0] == 401, path
        status, _, page = call(anonymous, '/')
        assert status == 200 and '使用体验账号进入'.encode() in page
        print('PASS anonymous: / redirects to login; me/profile/chat HTTP 401', flush=True)
        demo = client()
        assert call(demo, '/api/auth/login', {'username': 'demo', 'password': 'demo2026'})[0] == 200
        assert call(demo, '/api/me')[2]['user']['username'] == 'demo'
        print('PASS demo login; account identity restored', flush=True)
        password = secrets.token_hex(16)
        first, second = client(), client()
        assert call(first, '/api/auth/register', {'username': 'accountA', 'password': password})[0] == 200
        assert call(second, '/api/auth/register', {'username': 'accountB', 'password': password})[0] == 200
        assert call(client(), '/api/auth/register', {'username': 'accountA', 'password': password})[0] == 409
        profile = {'confirmed': True, 'education': '本科', 'major': '国际商务类', 'graduationYear': 2027}
        assert call(first, '/api/profile', profile)[0] == 200
        assert call(first, '/api/chat', {'question': '还需要核实哪些条件？'})[0] == 200
        first_data = call(first, '/api/profile')[2]
        second_data = call(second, '/api/profile')[2]
        assert first_data['profile'] == profile and len(first_data['messages']) == 2
        assert second_data['profile']['confirmed'] is False and second_data['messages'] == []
        assert 'resume' not in first_data
        print('PASS two accounts: profile/history isolated; duplicate username rejected', flush=True)
        browser_two = client()
        assert call(browser_two, '/api/auth/login', {'username': 'accountA', 'password': password})[0] == 200
        assert call(browser_two, '/api/profile')[2] == first_data
        print('PASS independent cookie jar: same account restores profile and messages', flush=True)
        stop(server)
        server = start()
        assert call(browser_two, '/api/profile')[2] == first_data
        users = json.loads((data_dir / 'users.json').read_text('utf-8'))
        assert password not in json.dumps(users) and all(len(u['hash']) == 128 for u in users)
        print('PASS process restart: persistent profile/history and signed session; scrypt hashes only', flush=True)
        assert call(browser_two, '/api/auth/logout', {}, 'POST')[0] == 200
        assert call(browser_two, '/api/me')[0] == 401
        print('PASS logout: /api/me HTTP 401; model not called', flush=True)
    finally:
        stop(server)


if __name__ == '__main__':
    main()
