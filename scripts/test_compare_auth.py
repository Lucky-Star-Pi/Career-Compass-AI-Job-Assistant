"""Synthetic credentials stay in memory; offline tests send no actual requests."""
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
import io
from compare_auth import ComparisonStop, compare, inspect_body, job_only, read_session
from test_collect_jobs import HTML, URL

# Deliberately fictional, not a working credential and never written as session.json.
DUMMY = 'fixture-only=not-a-real-session'
UNKNOWN_HTML = HTML.replace('2099年10月30日', '公告未写明').encode()


def response(payload):
    result = MagicMock()
    result.__enter__.return_value = result
    result.status = 200
    result.read.return_value = payload
    return result


class Tests(unittest.TestCase):
    def test_two_requests_same_ua_cookie_only_second_no_leak(self):
        opener = MagicMock()
        opener.open.side_effect = [response(UNKNOWN_HTML), response(UNKNOWN_HTML)]
        with patch('compare_auth.urllib.request.build_opener', return_value=opener), patch('compare_auth.time.sleep') as sleep, patch('compare_auth.time.monotonic', return_value=100):
            report, code = compare(URL, 'fixed-offline-UA', DUMMY)
        self.assertEqual(code, 0)
        self.assertEqual(report['decision'], 'no-gain')
        self.assertEqual(opener.open.call_count, 2)
        first, second = [call.args[0] for call in opener.open.call_args_list]
        self.assertFalse(first.has_header('Cookie'))
        self.assertTrue(second.get_header('Cookie') == DUMMY)
        self.assertEqual(first.get_header('User-agent'), second.get_header('User-agent'))
        self.assertFalse(DUMMY in json.dumps(report))
        self.assertEqual(len(report['cookie_sha256_8']), 8)
        sleep.assert_called_once_with(2.0)

    def test_real_field_gain_only(self):
        opener = MagicMock()
        opener.open.side_effect = [response(UNKNOWN_HTML), response(HTML.encode())]
        with patch('compare_auth.urllib.request.build_opener', return_value=opener), patch('compare_auth.time.sleep'):
            report, code = compare(URL, 'fixed-offline-UA', DUMMY)
        self.assertEqual(report['added_fields'], ['application_end'])
        self.assertEqual(report['decision'], 'gain')

    def test_auth_redirect_and_status_stop_without_second_request(self):
        for status in (401, 403, 302, 429):
            opener = MagicMock()
            opener.open.side_effect = HTTPError(URL, status, '', {}, io.BytesIO(b'never-log-this-body'))
            with patch('compare_auth.urllib.request.build_opener', return_value=opener):
                report, code = compare(URL, 'fixed-offline-UA', DUMMY)
            self.assertEqual(code, 4)
            self.assertEqual(opener.open.call_count, 1)
            self.assertFalse('never-log-this-body' in json.dumps(report))

    def test_risk_stops_but_normal_job_safety_word_does_not(self):
        for text in ('安全验证', '请输入验证码', '风控提示'):
            with self.assertRaises(ComparisonStop) as caught:
                inspect_body(('<title>' + text + '</title>').encode(), URL)
            self.assertEqual(caught.exception.exit_code, 4)
        self.assertTrue(inspect_body(HTML.replace('虚构岗位', '安全工程师').encode(), URL)['parsed'])

    def test_risk_second_request_is_inconclusive_exit_four(self):
        opener = MagicMock()
        opener.open.side_effect = [response(UNKNOWN_HTML), response('<h1>安全验证</h1>'.encode())]
        with patch('compare_auth.urllib.request.build_opener', return_value=opener), patch('compare_auth.time.sleep'):
            report, code = compare(URL, 'fixed-offline-UA', DUMMY)
        self.assertEqual(code, 4)
        self.assertEqual(report['decision'], 'inconclusive')
        self.assertFalse(report['batch_authorized_by_comparison'])
        self.assertEqual(opener.open.call_count, 2)
        self.assertFalse(DUMMY in json.dumps(report))

    def test_non_job_paths_never_requested(self):
        for path in ('/api/jobs', '/account', '/profile', '/resume', '/messages', '/applications', '/users/fixture/jobs', '/sitemap.xml'):
            self.assertFalse(job_only('https://www.zhidianmijin.com.cn' + path))
        self.assertFalse(job_only(URL + '?user_id=fixture'))

    def test_private_file_validation_without_ever_writing_it(self):
        with patch('pathlib.Path.read_text', return_value=json.dumps({'cookie': DUMMY, 'exported_at': '2026-10-30T21:00:00+08:00'})):
            self.assertTrue(read_session() == DUMMY)
        for value in ({'cookie': DUMMY + '\n', 'exported_at': '2026-10-30T21:00:00+08:00'}, {'cookie': DUMMY, 'exported_at': 'invalid'}):
            with patch('pathlib.Path.read_text', return_value=json.dumps(value)):
                with self.assertRaises(ComparisonStop):
                    read_session()


if __name__ == '__main__':
    unittest.main(verbosity=2)
