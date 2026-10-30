"""Derive a shortlist exclusively from existing local page journals; no network."""
import csv
import json
from datetime import date, timedelta
from pathlib import Path
from manual_intake import ROOT, PII, create_templates, parse_day, unknown

COLUMNS = '序号,岗位名称,单位,地点,发布时间,学历,招聘类型,详情页URL,页级证据文件,建议'.split(',')
BASE_DAY = date(2026, 10, 30)
SINCE = BASE_DAY - timedelta(days=45)


def value(row, key):
    field = row.get(key, 'unknown')
    if isinstance(field, dict):
        field = field.get('normalized') if field.get('normalized') not in (None, 'unknown', '') and key == 'published_at' else field.get('raw', 'unknown')
    return str(field) if field not in (None, '', [], {}) else 'unknown'


def day(row):
    try:
        return parse_day(value(row, 'published_at'))
    except ValueError:
        return None


def recommendation(row):
    if value(row, 'recruitment_type') != '校招':
        return '不看'
    if unknown(value(row, 'employer')):
        return '备选'
    return '优先' if day(row) is not None and SINCE <= day(row) <= BASE_DAY else '不看'


def derive(root=ROOT):
    jobs, invalid = {}, 0
    for file in sorted((root / 'data/raw').glob('BATCH-*.pages/page-records.jsonl')):
        for line in file.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                url = value(row, 'source_url')
                if unknown(url) or PII.search(url):
                    invalid += 1
                    continue
                if url not in jobs or value(row, 'obtained_at') > value(jobs[url], 'obtained_at'):
                    jobs[url] = row
            except (ValueError, TypeError, AttributeError):
                invalid += 1
    order = {'优先': 0, '备选': 1, '不看': 2}
    ranked = sorted(jobs.values(), key=lambda row: (order[recommendation(row)], -(day(row) or date.min).toordinal(), value(row, 'source_url')))
    rows = []
    mapping = {'岗位名称': 'name', '单位': 'employer', '地点': 'location', '发布时间': 'published_at', '学历': 'education', '招聘类型': 'recruitment_type', '详情页URL': 'source_url', '页级证据文件': 'raw_snapshot'}
    for index, row in enumerate(ranked, 1):
        output = {cn: value(row, en) for cn, en in mapping.items()}
        # Never leak accidental contact details from a historical journal into a new public CSV.
        output = {key: PII.sub('[REDACTED]', val) for key, val in output.items()}
        output.update(序号=str(index), 建议=recommendation(row))
        rows.append(output)
    return rows, invalid


def main():
    create_templates()
    rows, invalid = derive()
    with (ROOT / 'data/raw/SHORTLIST.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    counts = {label: sum(row['建议'] == label for row in rows) for label in ('优先', '备选', '不看')}
    print(f'总数={len(rows)} 优先={counts["优先"]} 备选={counts["备选"]} 不看={counts["不看"]} 无效输入行={invalid}')
    print(f'近45天口径：{SINCE.isoformat()}至{BASE_DAY.isoformat()}；只读本地候选，不代表可报名或已人工核验')
    if counts['优先'] < 3:
        print('未满足“优先档≥3”验收，不提升备选、不编造候选')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
