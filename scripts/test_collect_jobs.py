"""Synthetic, offline tests for bounded collection; no real records are written."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from collect_jobs import Fetcher, NoRedirect, StopCollection, allowed, parse_page
from csv_records import read_csv, write_csv
from import_data import import_rows
from validate_data import ROOT

URL = 'https://www.zhidianmijin.com.cn/jobs/00000000-0000-0000-0000-000000000001'
# Fictional parser fixture only; never a real job.
HTML = '''<html><head><title>虚构岗位｜虚构单位｜职点迷津</title></head><body><main>
<div>报名截止</div><div>2099年10月30日</div><div>招聘类型</div><div>虚构校招</div>
<div>工作地点</div><div>虚构地区</div><div>薪资待遇</div><div>公告未写明</div>
<div>发布时间</div><div>2026年10月30日</div><div>学历要求</div><div>本科及以上学历。</div>
<div>专业要求</div><div>公告未写明</div><h2>岗位介绍</h2><p>工作经验：公告未写明</p>
<p>其他限制：仅为虚构解析样例。</p><h2>后续无关内容</h2><p>不应进入证据。</p>
</main></body></html>'''


class Tests(unittest.TestCase):
    def test_boundaries_and_exact_evidence(self):
        row, txt = parse_page(HTML, URL, '2026-10-30T21:05:00+08:00', 'AUTO-01', 'data/raw/test.txt')
        self.assertEqual(row['name'], '虚构岗位')
        self.assertEqual(row['major'], 'unknown')
        self.assertEqual(row['salary'], 'unknown')
        self.assertEqual(row['experience'], 'unknown')
        self.assertEqual(row['open_status'], 'open')
        self.assertEqual(row['application_end']['normalized'], '2099-10-30')
        self.assertIn(row['condition_text'], txt)
        self.assertIn(row['evidence_excerpt'], txt)
        self.assertNotIn('不应进入证据', txt)
        self.assertEqual(len(txt.splitlines()[:3]), 3)
        missing, _ = parse_page(HTML.replace('<div>学历要求</div><div>本科及以上学历。</div>', ''), URL, '2026-10-30T21:05:00+08:00', 'AUTO-01', 'data/raw/test.txt')
        self.assertEqual(missing['education'], 'unknown')
        self.assertIn('education', missing['missing_fields'])

    def test_unknown_deadline_and_same_day(self):
        for replacement, state in (('长期招聘，无固定截止日期', 'unknown'), ('2026年10月30日', 'unknown'), ('2020年1月1日', 'closed')):
            row, _ = parse_page(HTML.replace('2099年10月30日', replacement), URL, '2026-10-30T21:05:00+08:00', 'AUTO-01', 'data/raw/test.txt')
            self.assertEqual(row['open_status'], state)

    def test_observed_auxiliary_labels_and_privacy_boundary(self):
        # Synthetic variation of the observed text-node boundary, not a real job fixture.
        html = HTML.replace('<div>2026年10月30日</div>', '<div>2026年10月30日</div><div>能不能报</div><div>公告未写明</div>')
        html = html.replace('<div>虚构校招</div>', '<div>虚构校招</div><div>经验要求</div><div>0-1年</div>')
        html = html.replace('<h2>后续无关内容</h2>', '<a>查看原始公告</a><div>问题反馈</div><div>站点隐私文案</div><h2>后续无关内容</h2>')
        row, txt = parse_page(html, URL, '2026-10-30T21:05:00+08:00', 'AUTO-01', 'data/raw/test.txt')
        self.assertEqual(row['published_at']['normalized'], '2026-10-30')
        self.assertEqual(row['recruitment_type'], '虚构校招')
        self.assertNotIn('站点隐私文案', txt)
        self.assertNotIn('missing_fields', row['missing_fields'])
        row, _ = parse_page(html.replace('虚构单位', '广东省/东莞市'), URL, '2026-10-30T21:05:00+08:00', 'AUTO-01', 'data/raw/test.txt')
        self.assertEqual(row['employer'], 'unknown')

    def test_url_allowlist_and_redirect(self):
        self.assertTrue(allowed(URL))
        for url in ('https://www.zhidianmijin.com.cn/api/jobs', 'https://other.invalid/jobs/x', URL + '?token=fixture', URL + '#fragment', 'https://www.zhidianmijin.com.cn/jobs?page=2'):
            self.assertFalse(allowed(url))
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, '', {}, URL))

    def test_stop_rules(self):
        for code in (403, 429):
            fetch = Fetcher('offline-test', 1.5, {'requests': []})
            with patch.object(fetch.opener, 'open', side_effect=HTTPError(URL, code, '', {}, io.BytesIO(b'private-body'))):
                with self.assertRaises(StopCollection):
                    fetch.get(URL)
            self.assertNotIn('private-body', json.dumps(fetch.ledger))
            self.assertEqual(len(fetch.ledger['requests']), 1)
        fetch = Fetcher('offline-test', 1.5, {'requests': []})
        errors = [HTTPError(URL, code, '', {}, io.BytesIO()) for code in (500, 502)]
        with patch.object(fetch.opener, 'open', side_effect=errors), patch('collect_jobs.time.sleep'):
            self.assertEqual(fetch.get(URL)[0], None)
            with self.assertRaises(StopCollection):
                fetch.get(URL)
        self.assertEqual(len(fetch.ledger['requests']), 2)

    def test_spacing_and_csv_roundtrip(self):
        fetch = Fetcher('offline-test', 1.5, {'requests': []})
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = response
        response.status, response.read.return_value = 200, b'<xml/>'
        with patch.object(fetch.opener, 'open', return_value=response), patch('collect_jobs.time.monotonic', return_value=100), patch('collect_jobs.time.sleep') as sleep:
            fetch.get(URL)
            fetch.get(URL)
            sleep.assert_called_once_with(1.5)
        folder = ROOT / 'data/.tmp'
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder, ignore_cleanup_errors=True) as tmp:
            row, _ = parse_page(HTML, URL, '2026-10-30T21:05:00+08:00', 'AUTO-01', 'data/raw/test.txt')
            path = Path(tmp) / 'fictional.csv'
            row['is_fixture'] = True
            write_csv(path, [row])
            result = read_csv(path)
            self.assertEqual(result[0]['condition_text'], row['condition_text'])
            self.assertTrue(result[0]['is_fixture'])

    def test_csv_to_existing_fixture_import(self):
        from csv_records import COLUMNS
        source = json.loads((ROOT / 'data/fixtures/input.json').read_text(encoding='utf-8'))[0]
        row = {k: 'unknown' for k in COLUMNS}
        row.update(source, missing_fields=[], conditions=[], evidence_metadata={'url': source['source_url'], 'obtained_at': source['obtained_at'], 'http_status': 'unknown', 'screenshot_path': 'unknown'})
        folder = ROOT / 'data/.tmp'
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder, ignore_cleanup_errors=True) as tmp:
            path = Path(tmp) / 'fictional.csv'
            write_csv(path, [row])
            rows, errors, review = import_rows(read_csv(path), True)
            self.assertEqual(errors, [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['status'], 'unknown')


if __name__ == '__main__':
    unittest.main(verbosity=2)
