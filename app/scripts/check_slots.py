"""Opt-in live slot/confirmation/resume acceptance; only synthetic account data."""
import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    if not parser.parse_args().live:
        parser.error('Requires --live: up to three real chat calls, each with at most one retry.')
    app = Path(__file__).resolve().parents[1]
    private = app.parent / 'data/private'
    private.mkdir(parents=True, exist_ok=True)
    data_dir = Path(tempfile.mkdtemp(prefix='r4-slots-', dir=private))
    env = os.environ.copy()
    env.pop('DEEPSEEK_API_KEY', None)  # Next loads existing .env.local; never read/print it here.
    env.update(USER_DATA_DIR=str(data_dir), PROFILE_COOKIE_SECRET=secrets.token_hex(32), NEXT_TELEMETRY_DISABLED='1')
    base = 'http://127.0.0.1:3115'
    def client():
        return urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                          urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(opener, path, body=None, method=None):
        request = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                         headers={'Content-Type': 'application/json', 'Origin': base}, method=method)
        try:
            response = opener.open(request, timeout=60)
        except urllib.error.HTTPError as error:
            response = error
        return response.status, json.loads(response.read())
    server = subprocess.Popen(['node', str(app / 'node_modules/next/dist/bin/next'),
                               'start', '-H', '127.0.0.1', '-p', '3115'], cwd=app, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            if server.poll() is not None:
                raise AssertionError('server exited before readiness')
            try:
                if call(client(), '/api/health')[0] == 200:
                    break
            except OSError:
                time.sleep(.25)
        else:
            raise AssertionError('server readiness timeout')
        first, second = client(), client()
        password = secrets.token_hex(20)
        assert call(first, '/api/auth/register', {'username': 'slotUserA', 'password': password})[0] == 200
        assert call(second, '/api/auth/register', {'username': 'slotUserB', 'password': password})[0] == 200
        status, answer = call(first, '/api/chat', {'question': '我是2027届本科，国际商务类，想留湛江'})
        print('C initial chat:', json.dumps({'HTTP': status, 'connected': answer.get('connected'), 'model_status': answer.get('model_status'), 'references': len(answer.get('references', [])), 'profile_updates': answer.get('profile_updates'), 'dropped_fields': answer.get('dropped_fields')}, ensure_ascii=False), flush=True)
        assert status == 200 and answer.get('connected') is True
        expected = {'education': '本科', 'major': '国际商务类', 'graduationYear': 2027, 'city': '湛江市'}
        assert all(answer['profile_updates'].get(k) == v for k, v in expected.items())
        assert 'status' not in answer and isinstance(answer['dropped_fields'], list)
        before = call(first, '/api/profile')[1]
        assert before['profile']['confirmed'] is False
        assert call(first, '/api/profile', {**expected, 'confirmed': True})[0] == 200
        assert call(first, '/api/profile')[1]['profile']['confirmed'] is True
        print('PASS C proposal did not alter profile; explicit confirmation persisted four slots', flush=True)
        status, followup = call(first, '/api/chat', {'question': '那我还差什么'})
        assert status == 200 and followup.get('connected') is True and followup.get('reply')
        assert len(call(first, '/api/profile')[1]['messages']) == 4
        print('PASS C contextual follow-up: connected=true; server history=4', flush=True)
        resume = '以下是我的简历要点：学历本科；专业国际商务类；2027届毕业；意向地区湛江。\n' + '合成项目经历：参与校园业务分析，整理需求文档并复核交付依据。' * 10
        assert len(resume) > 200
        status, resume_answer = call(first, '/api/chat', {'question': resume})
        assert status == 200 and resume_answer.get('resume_received') is True and resume_answer.get('profile_updates')
        data = call(first, '/api/profile')[1]
        assert data['hasResume'] is True and 'resume' not in data
        assert resume not in json.dumps(data, ensure_ascii=False) and resume not in json.dumps(resume_answer, ensure_ascii=False)
        assert data['messages'][-2]['content'].startswith('已提交简历要点')
        disk = json.loads((data_dir / 'profiles' / (data['userId'] + '.json')).read_text('utf-8'))
        assert disk['resume'] == resume
        print('PASS C synthetic resume >200 chars: private file only; confirmation available; API/history do not echo original', flush=True)
        assert call(first, '/api/profile?scope=resume', method='DELETE')[0] == 200
        assert call(first, '/api/profile')[1]['hasResume'] is False
        disk = json.loads((data_dir / 'profiles' / (data['userId'] + '.json')).read_text('utf-8'))
        assert disk['resume'] is None
        assert call(second, '/api/profile')[1]['messages'] == []
        assert call(second, '/api/profile')[1]['profile']['confirmed'] is False
        browser_two = client()
        assert call(browser_two, '/api/auth/login', {'username': 'slotUserA', 'password': password})[0] == 200
        assert len(call(browser_two, '/api/profile')[1]['messages']) == 6
        assert call(client(), '/api/me')[0] == 401
        print('PASS C delete resume; second account empty; independent session restores six messages; anonymous me=401', flush=True)
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


if __name__ == '__main__':
    main()
