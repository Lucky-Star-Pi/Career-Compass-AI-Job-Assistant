"""Sequential live evidence checks with one synthetic account, no credential output."""
import argparse
from pathlib import Path
import json
import re
import tempfile
import time
from check_reply_guard import APP, JOBS, client, call, account, start, stop

QUESTIONS = ['我是2027届本科，国际商务类，想留湛江', '这些岗位里有湛江的吗？', '03 号岗位学历要求是什么？']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--online', action='store_true')
    args = parser.parse_args()
    base = 'http://118.89.79.239:3000' if args.online else 'http://127.0.0.1:3119'
    server = None
    try:
        if not args.online:
            private = APP.parent / 'data/private'
            private.mkdir(parents=True, exist_ok=True)
            directory = Path(tempfile.mkdtemp(prefix='model-evidence-', dir=private))
            server = start(base, directory)
        opener = client()
        account(opener, base)
        for number, question in enumerate(QUESTIONS, 1):
            began = time.monotonic()
            status, output = call(opener, base, '/api/chat', {'question': question})
            refs = output.get('references', [])
            reply = output.get('reply', '')
            print(json.dumps({'question': number, 'HTTP': status, 'mode': output.get('mode'),
                              'seconds': round(time.monotonic() - began, 2), 'references': refs,
                              'reply': reply}, ensure_ascii=False), flush=True)
            assert status == 200 and output.get('mode') == 'deepseek'
            assert output.get('connected') is True and 'status' not in output and 0 < len(reply) < 300
            assert not any(phrase in reply for phrase in ['可以报名', '保证', '一定' + '能报'])
            assert all(any(ref['job_id'] == job['id'] and ref['source_url'] == job['source_url'] for job in JOBS) for ref in refs)
            target = JOBS[0] if number < 3 else JOBS[2]
            assert any(ref['job_id'] == target['id'] for ref in refs)
            if number < 3:
                assert '湛江' in reply and (target['name'] in reply or re.search(r'0?1\s*号', reply))
                assert not re.search(r'(?:未见|没有|无|不存在)(?:明确的|在)?湛江岗位', reply)
                assert not re.search(r'广东省.{0,4}非湛江', reply)
                if number == 2:
                    assert '本科' in reply and '国际商务类' in reply
            else:
                assert '硕士' in reply
        print('PASS structured evidence acceptance ' + ('online' if args.online else 'local'), flush=True)
    finally:
        if server is not None:
            stop(server)


if __name__ == '__main__':
    main()
