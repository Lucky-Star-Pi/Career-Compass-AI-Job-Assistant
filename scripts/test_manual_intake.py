"""Synthetic rows live only under ignored temporary roots, never actual MANUAL.csv."""
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import import_data
import manual_intake as intake
from make_shortlist import derive


class Tests(unittest.TestCase):
    def setUp(self):
        tmp = intake.ROOT / 'data/.tmp'
        tmp.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=tmp, ignore_cleanup_errors=True)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'data/raw').mkdir(parents=True)
        self.row = {key: 'unknown' for key in intake.COLUMNS}
        self.row.update(编号='TEST01', 岗位名称='测试岗位', 单位名称='测试单位', 单位性质='民企', 招聘类型='校招',
                        详情页URL='https://www.zhidianmijin.com.cn/jobs/00000000-0000-0000-0000-000000000001',
                        公告URL='https://www.example.org/notice', 发布时间='2026年10月30日', 报名截止='2026-11-15',
                        学历='本科', 条件原文='岗位要求本科，专业条件未明确。', 证据引用='岗位要求本科', 开放状态='open',
                        采集时间='2026-10-30T21:00:00+08:00', 证据文件='data/raw/TEST01.txt')
        self.evidence()

    def evidence(self, row=None):
        row = row or self.row
        lines = [f'# 岗位名称：{row["岗位名称"]}', f'# 详情页URL：{row["详情页URL"]}', '# 公告URL：' + ('unknown' if intake.unknown(row['公告URL']) else row['公告URL']), f'# 采集时间：{row["采集时间"]}', row['条件原文']]
        (self.root / row['证据文件']).write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def test_success_and_import_preserves_two_sources(self):
        record, errors, _ = intake.check_row(self.row, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(record['status'], 'unknown')
        self.assertFalse(record['profile_confirmed'])
        self.assertFalse(record['is_fixture'])
        self.assertEqual(len(record['source_refs']), 2)
        with patch.object(import_data, 'ROOT', self.root):
            normalized = import_data.normalize(record, False)
        self.assertEqual(normalized['source_refs'], record['source_refs'])

    def test_missing_announcement_does_not_invent_source(self):
        self.row['公告URL'] = 'unknown'
        self.evidence()
        record, errors, _ = intake.check_row(self.row, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(len(record['source_refs']), 1)
        self.assertIn('announcement_url', record['missing_fields'])

    def test_all_eight_hard_fields(self):
        for field in intake.HARD:
            row = copy.deepcopy(self.row)
            row[field] = ''
            record, errors, _ = intake.check_row(row, self.root)
            self.assertIsNone(record)
            self.assertTrue(any(field in e for e in errors))

    def test_sample_and_empty_check_only_do_not_write(self):
        intake.create_templates(self.root)
        for file, expected in (('MANUAL.csv', '0 行'), ('MANUAL_TEMPLATE.csv', '示例行必须删除')):
            out = io.StringIO()
            with patch.object(intake, 'ROOT', self.root), patch('sys.argv', ['manual_intake.py', '--input', str(self.root / 'data/raw' / file), '--check-only']), redirect_stdout(out):
                code = intake.main()
            self.assertIn(expected, out.getvalue())
            self.assertEqual(code, 0 if file == 'MANUAL.csv' else 1)
        self.assertFalse((self.root / 'data/raw/MANUAL.records.json').exists())
        self.assertFalse((self.root / 'data/raw/MANUAL_REPORT.md').exists())

    def test_evidence_text_encoding_and_pii(self):
        for field in ('条件原文', '证据引用'):
            row = copy.deepcopy(self.row)
            row[field] = '该句不在证据中'
            self.assertTrue(intake.check_row(row, self.root)[1])
        row = copy.deepcopy(self.row)
        row['备注'] = '1' * 11
        self.assertTrue(any('单元格' in e for e in intake.check_row(row, self.root)[1]))
        path = self.root / self.row['证据文件']
        path.write_bytes(b'\xff\xfe')
        self.assertTrue(any('UTF-8' in e for e in intake.check_row(self.row, self.root)[1]))
        self.evidence()
        with path.open('a', encoding='utf-8') as stream:
            stream.write('fixture' + '@' + 'example.invalid')
        self.assertTrue(any('证据TXT含' in e for e in intake.check_row(self.row, self.root)[1]))

    def test_dates_states_enum_and_urls(self):
        for field, value, reason in (('报名截止', '2026/11/15', '日期不可解析'), ('报名截止', '2026-10-30', 'open要求'), ('单位性质', '不限', '枚举'), ('详情页URL', 'https://www.example.org/x', '详情页URL'), ('详情页URL', self.row['详情页URL'] + '#fragment', '详情页URL'), ('公告URL', 'https://www.zhidianmijin.com.cn/notice', '公告URL'), ('采集时间', '2026-10-30', 'ISO8601')):
            row = copy.deepcopy(self.row)
            row[field] = value
            self.assertTrue(any(reason in e for e in intake.check_row(row, self.root)[1]))
        for deadline, state, expected_ok in (('2026年10月29日', 'closed', True), ('2026-10-30', 'closed', False), ('2026-10-30', 'unknown', True)):
            row = copy.deepcopy(self.row)
            row.update(报名截止=deadline, 开放状态=state)
            self.assertEqual(not intake.check_row(row, self.root)[1], expected_ok)

    def test_duplicate_ids_and_evidence_are_rejected(self):
        records, results = intake.evaluate([(2, self.row), (3, self.row.copy())], self.root)
        self.assertEqual(records, [])
        self.assertTrue(all('编号重复' in r['reasons'] and '证据文件复用' in r['reasons'] for r in results))

    def test_path_escape_and_header_mismatch(self):
        row = copy.deepcopy(self.row)
        row['证据文件'] = 'data/private/session.txt'
        self.assertTrue(intake.check_row(row, self.root)[1])
        row = copy.deepcopy(self.row)
        row['岗位名称'] = '与证据不同的测试岗位'
        self.assertTrue(any('四行头部' in e for e in intake.check_row(row, self.root)[1]))

    def test_shortlist_local_dedupe_ranking_and_recent_boundary(self):
        path = self.root / 'data/raw/BATCH-TEST.pages'
        path.mkdir()
        rows = []
        for number, publication, employer, kind in ((1, '2026-09-15', '测试单位', '校招'), (2, '2026-10-30', 'unknown', '校招'), (3, '2026-09-14', '测试单位', '校招'), (4, '2026-10-30', '测试单位', '社招')):
            rows.append({'source_url': f'https://www.zhidianmijin.com.cn/jobs/TEST-{number}', 'name': '测试岗位', 'employer': employer, 'recruitment_type': kind, 'published_at': {'normalized': publication}, 'obtained_at': '2026-10-30T21:00:00+08:00'})
        (path / 'page-records.jsonl').write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows + [rows[0]]) + '\n', encoding='utf-8')
        result, bad = derive(self.root)
        self.assertEqual(len(result), 4)
        self.assertEqual([r['建议'] for r in result], ['优先', '备选', '不看', '不看'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
