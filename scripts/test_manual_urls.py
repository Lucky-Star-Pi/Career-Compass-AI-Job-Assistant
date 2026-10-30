"""Offline synthetic H workflow, merge and request-boundary tests under ignored roots."""
import csv
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
import manual_intake as intake
import collect_manual_urls as collect
from test_collect_jobs import HTML, URL

HTML_TEST = HTML.replace('虚构', '测试')


class Tests(unittest.TestCase):
    def setUp(self):
        base = intake.ROOT / 'data/.tmp'
        base.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=base, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'data/raw').mkdir(parents=True)

    def test_url_normalization_duplicate_invalid_cap(self):
        file = self.root / 'data/raw/MANUAL_URLS.txt'
        urls = [f'https://www.zhidianmijin.com.cn/jobs/{i:08x}-0000-0000-0000-000000000001' for i in range(33)]
        file.write_text('\n'.join(urls + [urls[0] + '?token=fixture#fragment', 'https://www.zhidianmijin.com.cn/api/jobs', 'https://other.invalid/jobs/x']), encoding='utf-8')
        targets, rows = collect.read_urls(file)
        self.assertEqual(len(targets), 30)
        self.assertEqual(sum(r['result'] == 'over_limit' for r in rows), 3)
        self.assertEqual(sum(r['result'] == 'duplicate' for r in rows), 1)
        self.assertEqual(sum(r['result'] == 'invalid' for r in rows), 2)
        self.assertFalse('token=fixture' in json.dumps(rows))

    def outputs(self):
        evidence = self.root / 'data/raw/MANUAL-TEST.pages'
        evidence.mkdir()
        row, text = collect.automatic_row(HTML_TEST, URL, '2026-10-30T22:00:00+08:00', 'MANUAL-TEST-01', 'data/raw/MANUAL-TEST.pages/01.evidence.txt')
        (evidence / '01.evidence.txt').write_bytes(text.encode('utf-8'))
        auto = self.root / 'data/raw/MANUAL-TEST.auto.csv'
        fill = self.root / 'data/raw/MANUAL-TEST.FILL_ME.csv'
        intake.write_csv(auto, [row])
        collect.write_fill(fill, [row])
        return row, auto, fill

    def complete(self, row, fill):
        human = {key: row[key] for key in intake.FILL_COLUMNS}
        human.update(公告URL='unknown', 报名截止='2099-10-30', 开放状态='open', 单位性质='unknown', 备注='本人已核验测试条件')
        with fill.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=intake.FILL_COLUMNS)
            writer.writeheader()
            writer.writerow(human)
        return human

    def test_shapes_pending_deadline_not_filled_and_remaining_rejected(self):
        row, auto, fill = self.outputs()
        self.assertEqual(list(row), intake.COLUMNS)
        self.assertEqual(row['报名截止'], 'PENDING')
        self.assertEqual(row['报名开始'], 'unknown')
        with fill.open(encoding='utf-8-sig') as stream:
            self.assertEqual(next(csv.reader(stream)), intake.FILL_COLUMNS)
        merged, errors = intake.merge_inputs(fill, auto)
        records, result = intake.evaluate(merged, self.root, collected=True)
        self.assertFalse(records)
        self.assertTrue(any('PENDING未补' in x for x in result[0]['reasons']))

    def test_completed_merge_passes_without_writes(self):
        row, auto, fill = self.outputs()
        self.complete(row, fill)
        merged, errors = intake.merge_inputs(fill, auto)
        self.assertEqual(errors, [])
        records, results = intake.evaluate(merged, self.root, collected=True)
        self.assertTrue(all(r['passed'] for r in results), results)
        self.assertEqual(records[0]['status'], 'unknown')
        before = (self.root / row['证据文件']).read_bytes()
        with patch.object(intake, 'ROOT', self.root), patch('sys.argv', ['manual_intake.py', '--input', str(fill), '--auto', str(auto), '--check-only']), redirect_stdout(io.StringIO()):
            self.assertEqual(intake.main(), 0)
        self.assertEqual((self.root / row['证据文件']).read_bytes(), before)
        self.assertFalse((self.root / 'data/raw/MANUAL.records.json').exists())

    def test_blank_pending_does_not_become_unknown(self):
        row, auto, fill = self.outputs()
        human = self.complete(row, fill)
        human['单位性质'] = ''
        with fill.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=intake.FILL_COLUMNS)
            writer.writeheader()
            writer.writerow(human)
        merged, errors = intake.merge_inputs(fill, auto)
        self.assertEqual(merged[0][1]['单位性质'], 'PENDING')
        self.assertFalse(intake.evaluate(merged, self.root, collected=True)[0])

    def test_risk_is_detected_before_attempt_to_parse(self):
        with self.assertRaises(collect.StopCollection):
            collect.automatic_row('<h1>安全验证</h1>', URL, '2026-10-30T22:00:00+08:00', 'ID', 'data/raw/file.txt')

    def test_full_request_loop_stops_403_without_discovery_or_cookie(self):
        file = self.root / 'data/raw/MANUAL_URLS.txt'
        file.write_text(URL + '\n' + URL.replace('000000000001', '000000000002'), encoding='utf-8')
        opener = MagicMock()
        opener.open.side_effect = HTTPError(URL, 403, '', {}, io.BytesIO(b'not-recorded'))
        with patch.object(collect, 'ROOT', self.root), patch('sys.argv', ['collect_manual_urls.py', '--input', str(file)]), patch.dict(os.environ, {'CAREER_COMPASS_CONTACT': 'fixture-role@example.invalid'}), patch('collect_jobs.urllib.request.build_opener', return_value=opener), redirect_stdout(io.StringIO()):
            self.assertEqual(collect.main(), 1)
        self.assertEqual(opener.open.call_count, 1)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, URL)
        self.assertFalse(request.has_header('Cookie'))
        report = json.loads(next((self.root / 'data/raw').glob('MANUAL-*.run.json')).read_text(encoding='utf-8'))
        self.assertEqual(report['request_count'], 1)
        self.assertEqual(report['not_requested'], 1)
        self.assertEqual(report['success'], 0)
        self.assertFalse('not-recorded' in json.dumps(report))
        self.assertFalse('fixture-role@example.invalid' in json.dumps(report))


if __name__ == '__main__':
    unittest.main(verbosity=2)
