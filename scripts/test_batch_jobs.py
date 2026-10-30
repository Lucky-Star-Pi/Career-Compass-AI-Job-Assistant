"""Fictional offline checks for B05-C pool rules, date order and sitemap ordering."""
import copy
import unittest
from batch_jobs import exclusions, rank, sitemap_entries, modified_key
from collect_jobs import parse_page
from test_collect_jobs import HTML, URL


class Tests(unittest.TestCase):
    def row(self, deadline='2026年11月7日'):
        html = HTML.replace('虚构校招', '校招').replace('2099年10月30日', deadline)
        return parse_page(html, URL, '2026-10-30T22:00:00+08:00', 'BATCH-01', 'data/raw/test.txt')

    def test_strict_pool_and_unknown(self):
        row, txt = self.row()
        self.assertEqual(exclusions(row, txt), [])
        for key, value, reason in (('employer', row['name'], '单位缺失或无效'), ('employer', '职点迷津', '单位缺失或无效'), ('recruitment_type', 'unknown', '招聘类型未知'), ('recruitment_type', '社招', '非校招'), ('application_end', 'unknown', '截止未知'), ('condition_text', '不在原文里的虚构长条件描述', '证据不符')):
            changed = copy.deepcopy(row)
            changed[key] = value
            self.assertIn(reason, exclusions(changed, txt))
        self.assertIn('PII', exclusions(row, txt + '\n' + '1' * 11))

    def test_cutoff_and_sort(self):
        a, txt = self.row('2026年10月30日')
        self.assertIn('已截止', exclusions(a, txt))
        late, _ = self.row('2026年11月8日')
        preferred, _ = self.row('2026年11月7日')
        earlier, _ = self.row('2026年10月31日')
        self.assertEqual(sorted([earlier, late, preferred], key=rank), [preferred, late, earlier])
        newer = copy.deepcopy(preferred)
        newer['published_at']['normalized'] = '2026-10-31'
        self.assertLess(rank(newer), rank(preferred))

    def test_sitemap_lastmod_and_white_list(self):
        data = ('<urlset><url><loc>' + URL + '</loc><lastmod>2026-10-30</lastmod></url><url><loc>https://other.invalid/x</loc></url></urlset>').encode()
        self.assertEqual(sitemap_entries(data), [(URL, '2026-10-30')])
        self.assertGreater(modified_key('2026-10-31T00:00:00+08:00'), modified_key('2026-10-30T23:00:00+08:00'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
