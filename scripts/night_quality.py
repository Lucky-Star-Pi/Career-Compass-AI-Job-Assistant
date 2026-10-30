"""Authorized night A/B preparation, existing ten evidence files only; no network."""
import csv
import hashlib
import json
from pathlib import Path
from layout_parser import quality_fields
from manual_intake import ROOT, read_input, write_csv
from collect_manual_urls import write_fill


def main():
    batch = 'MANUAL-20261030-220241'
    auto = ROOT / 'data/raw' / (batch + '.auto.csv')
    rows, errors = read_input(auto)
    if errors or len(rows) != 10:
        raise SystemExit('FAIL expected ten existing auto records')
    fixed = []
    for _, row in rows:
        path = ROOT / row['证据文件']
        payload = path.read_bytes()
        updated = quality_fields(row, payload.decode('utf-8-sig'))
        assert path.read_bytes() == payload
        assert all(value != 'PENDING' for value in updated.values())
        fixed.append(updated)
        print(updated['编号'] + ' 新引用：' + updated['证据引用'])
    for number in (3, 5):
        row = fixed[number - 1]
        text = (ROOT / row['证据文件']).read_text(encoding='utf-8')
        assert '学历要求\n硕士\n' in text and row['学历'] == '硕士'
        print(f'PASS {number:02d}: 学历要求下一行=硕士')
    write_csv(auto, fixed)
    write_fill(ROOT / 'data/raw' / (batch + '.FILL_ME.csv'), fixed)
    write_csv(ROOT / 'data/raw/MANUAL.csv', fixed)
    print('PASS ten exact qualification excerpts; zero PENDING; evidence unchanged')


if __name__ == '__main__':
    main()
