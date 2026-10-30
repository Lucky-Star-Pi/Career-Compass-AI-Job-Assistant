"""Pure A/B facts and isolated zero-network reparse regression."""
import csv
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import collect_manual_urls as collector
import manual_intake as intake
from layout_parser import facts
from reparse_manual import reparse

TEXT = '''# 岗位名：测试岗位
# URL：https://www.zhidianmijin.com.cn/jobs/00000000-0000-0000-0000-000000000001
# 获取时间：2026-10-30T22:00:00+08:00
# 公告URL：unknown
测试用工有限公司
所属集团：
测试所属集团有限公司
国企
报名截止
2027年1月25日
招聘类型
校招
学历要求
本科
专业要求
经济与贸易类
岗位介绍
要求本科，经济与贸易类专业。
'''


class Tests(unittest.TestCase):
    def test_a_b_employer_not_parent_group_and_line_proof(self):
        for text in (TEXT, TEXT.replace('学历要求', '学历\n要求').replace('专业要求', '专业\n要求')):
            value = facts(text, 'data/raw/test.txt')
            self.assertEqual(value['employer'], '测试用工有限公司')
            self.assertEqual(value['organization_type'], '国企')
            ref = value['field_evidence']['organization_type']
            self.assertEqual(text.splitlines()[ref['line'] - 1], ref['evidence_ref'])
            self.assertEqual(value['education'], '本科')
            self.assertEqual(value['major'], '经济与贸易类')
            self.assertEqual(value['application_end']['normalized'], '2027-01-25')

    def test_long_term_and_unwritten_are_distinct(self):
        long_term = facts(TEXT.replace('2027年1月25日', '长期招聘，无固定截止日期'), 'data/raw/test.txt')
        self.assertEqual(long_term['application_end'], 'unknown')
        self.assertEqual(long_term['open_status'], 'open')
        self.assertEqual(long_term['open_basis'], '长期招聘')
        missing = facts(TEXT.replace('2027年1月25日', '公告未写明'), 'data/raw/test.txt')
        self.assertEqual(missing['open_status'], 'unknown')
        self.assertEqual(missing['open_basis'], 'unknown')

    def test_reparse_mode_no_network_evidence_unchanged_and_backups(self):
        base = intake.ROOT / 'data/.tmp'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base, ignore_cleanup_errors=True) as folder:
            root = Path(folder)
            raw = root / 'data/raw'
            raw.mkdir(parents=True)
            batch = 'MANUAL-20261030-220241'
            pages = raw / (batch + '.pages')
            pages.mkdir()
            evidence = pages / '01.evidence.txt'
            evidence.write_bytes(TEXT.encode())
            digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
            row = {key: 'unknown' for key in intake.COLUMNS}
            row.update(编号='TEST01', 岗位名称='测试岗位', 单位名称='PENDING', 单位性质='PENDING', 报名截止='PENDING', 开放状态='PENDING', 备注='PENDING', 证据文件=evidence.relative_to(root).as_posix(), 条件原文='要求本科，经济与贸易类专业。', 证据引用='要求本科')
            intake.write_csv(raw / (batch + '.auto.csv'), [row])
            collector.write_fill(raw / (batch + '.FILL_ME.csv'), [row])
            (raw / (batch + '.run.json')).write_text('{"requests": [{"http_status": 200}]}', encoding='utf-8')
            with patch.object(collector, 'ROOT', root), patch('sys.argv', ['collect_manual_urls.py', '--reparse']), patch.object(collector, 'read_urls', side_effect=AssertionError('URL list read in offline mode')), patch('collect_jobs.Fetcher.get', side_effect=AssertionError('network used')), patch('socket.socket', side_effect=AssertionError('network used')), redirect_stdout(io.StringIO()):
                self.assertEqual(collector.main(), 0)
            self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), digest)
            self.assertTrue((raw / (batch + '.auto.csv.v1')).exists())
            self.assertTrue((raw / (batch + '.FILL_ME.csv.v1')).exists())
            meta = json.loads((raw / (batch + '.run.json')).read_text(encoding='utf-8'))
            self.assertEqual(meta['mode'], 'reparse')
            self.assertEqual(meta['requests'], 0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(reparse(batch, root), 1)  # cannot overwrite .v1 on rerun

    def test_manual_long_term_open_requires_exact_evidence(self):
        from test_manual_intake import Tests as ManualCase
        case = ManualCase()
        case.setUp()
        try:
            row = case.row.copy()
            row.update(报名截止='unknown', 开放状态='open')
            self.assertTrue(any('显式长期招聘' in e for e in intake.check_row(row, case.root)[1]))
            path = case.root / row['证据文件']
            with path.open('a', encoding='utf-8') as stream:
                stream.write('报名截止\n长期招聘，无固定截止日期\n国企\n')
            record, errors, _ = intake.check_row(row, case.root)
            self.assertEqual(errors, [])
            self.assertEqual(record['open_basis'], '长期招聘')
            self.assertEqual(record['application_end'], 'unknown')
            self.assertEqual(record['status'], 'unknown')
        finally:
            case.doCleanups()


if __name__ == '__main__':
    unittest.main(verbosity=2)
