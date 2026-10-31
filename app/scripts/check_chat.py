"""Explicit live acceptance: three signed-cookie chat requests, no credential output."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Allow up to three real chat requests (each may retry once).')
    args = parser.parse_args()
    if not args.live:
        parser.error('Requires --live; real model requests can incur usage charges.')
    root = Path(__file__).resolve().parents[1]
    allowed = {j['id']: j['source_url'] for j in json.loads((root / 'lib/jobs.json').read_text('utf-8'))}
    env = os.environ.copy()
    env['NEXT_TELEMETRY_DISABLED'] = '1'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    server = subprocess.Popen(['node', str(root / 'node_modules/next/dist/bin/next'),
                               'start', '-H', '127.0.0.1', '-p', '3109'],
                              cwd=root, env=env, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)

    def call(path, body=None, cookie=None):
        headers = {'Content-Type': 'application/json'}
        if cookie:
            headers['Cookie'] = cookie
        request = urllib.request.Request('http://127.0.0.1:3109' + path,
                                         data=json.dumps(body, ensure_ascii=False).encode() if body is not None else None,
                                         headers=headers)
        with opener.open(request, timeout=70) as response:
            return response.headers, json.loads(response.read())

    results = []
    try:
        for _ in range(80):
            if server.poll() is not None:
                raise AssertionError('Local server exited before readiness')
            try:
                _, health = call('/api/health')
                break
            except (OSError, urllib.error.URLError):
                time.sleep(.25)
        else:
            raise AssertionError('Local server was not ready')
        if health['model'] == '未接通':
            raise AssertionError('Model key not configured; no live chat requests issued')
        profile = {'confirmed': True, 'education': '本科', 'major': '国际商务类',
                   'graduationYear': 2027, 'city': '湛江市', 'certificates': []}
        headers, _ = call('/api/profile', profile)
        cookie = headers['Set-Cookie'].split(';')[0]
        _, restored = call('/api/profile', cookie=cookie)
        assert restored == profile, 'Signed cookie did not roundtrip'
        print('PASS signed cookie roundtrip (not logged)', flush=True)
        for run in range(1, 4):
            started = time.monotonic()
            _, answer = call('/api/chat', {'question': '我是2027届本科，国际商务类，想留在湛江'}, cookie)
            refs = answer.get('references', [])
            result = {'run': run, 'connected': answer.get('connected'),
                      'model_status': answer.get('model_status'),
                      'reply_chars': len(answer.get('reply', '')),
                      'references': len(refs),
                      'candidate_pairs_valid': bool(refs) and all(allowed.get(r.get('job_id')) == r.get('source_url') for r in refs),
                      'seconds': round(time.monotonic() - started, 2)}
            print(json.dumps(result, ensure_ascii=False), flush=True)
            results.append(result)
            if not (result['connected'] is True and 0 < result['reply_chars'] < 300 and result['candidate_pairs_valid']):
                raise AssertionError('Live chat acceptance failed; stopped without issuing remaining requests')
        print('PASS live acceptance: 3/3 connected, nonempty reply <300 chars, references within 10 candidate pairs', flush=True)
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


if __name__ == '__main__':
    main()
