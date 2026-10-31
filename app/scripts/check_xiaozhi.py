"""R7 HTTP acceptance against an isolated local server with an invalid model key.

Start a production build on 127.0.0.1:3117 with USER_DATA_DIR outside app,
DEEPSEEK_API_KEY set to an intentionally invalid value, DASHSCOPE_API_KEY empty.
All accounts and resume strings in this check are synthetic; no raw data logged.
"""
import http.cookiejar
import json
import secrets
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:3117'


def client():
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(opener, path, body=None, method=None):
    request = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json', 'Origin': BASE}, method=method)
    try:
        response = opener.open(request, timeout=35)
    except urllib.error.HTTPError as error:
        response = error
    return response.status, json.loads(response.read())


def main():
    anonymous = client()
    assert call(anonymous, '/api/preferences')[0] == 401
    assert call(anonymous, '/api/me')[0] == 401
    first, second = client(), client()
    for target in [first, second]:
        assert call(target, '/api/auth/register', {
            'username': 'r7test' + secrets.token_hex(4),
            'password': secrets.token_hex(16)})[0] == 200
    assert call(first, '/api/preferences')[1]['preferences']['bubbleDismissed'] is False
    assert call(first, '/api/preferences', {'bubbleDismissed': True})[0] == 200
    assert call(first, '/api/preferences')[1]['preferences']['bubbleDismissed'] is True
    assert call(second, '/api/preferences')[1]['preferences']['bubbleDismissed'] is False
    assert call(first, '/api/preferences', {'bubbleDismissed': True, 'userId': 'invalid'})[0] == 400
    print('PASS preference persisted per account; second account isolated; anonymous 401; extra keys rejected', flush=True)
    resume = '以下是我的简历要点：本科；国际商务类；2027届；湛江市；CET-4；C1驾驶证。' + '合成测试材料，无真实身份信息。' * 16
    status, answer = call(first, '/api/chat', {'question': resume})
    assert status == 200 and answer['mode'] == 'rules' and answer['connected'] is False
    assert answer['reply'].startswith('小职正在升级中，先用规则结果帮你核对：')
    assert answer['profile_autofilled'] is True and len(answer['references']) == 3
    assert resume not in json.dumps(answer, ensure_ascii=False)
    _, data = call(first, '/api/profile')
    assert data['profileSource'] == 'resume' and data['profile']['confirmed'] is True
    assert data['profile']['education'] == '本科' and data['profile']['graduationYear'] == 2027
    assert 'resume' not in data and '合成测试材料' not in json.dumps(data, ensure_ascii=False)
    assert data['messages'][-1]['mode'] == 'rules'
    other = call(second, '/api/profile')[1]
    assert other['profile']['confirmed'] is False and not other['messages'] and not other['hasResume']
    print('PASS invalid DeepSeek key -> rules answer with 3 references; resume auto-filled; no raw echo; account isolation', flush=True)
    assert call(first, '/api/chat', {'question': '以下是我的简历要点：仅为没有明确枚举条件的合成材料。'})[0] == 200
    assert call(first, '/api/profile')[1]['profile']['confirmed'] is False
    print('PASS replacement resume without explicit slots clears stale profile instead of reusing previous qualifications', flush=True)
    assert call(first, '/api/profile?scope=resume', method='DELETE')[0] == 200
    assert call(first, '/api/profile')[1]['hasResume'] is False
    assert call(first, '/api/profile', method='DELETE')[0] == 200
    assert call(first, '/api/profile')[1]['profile']['confirmed'] is False
    print('PASS private synthetic resume deletion and profile clearing', flush=True)


if __name__ == '__main__':
    main()
