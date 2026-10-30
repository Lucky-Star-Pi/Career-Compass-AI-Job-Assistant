"""Shared CSV contract for manual and bounded automated collection (stdlib only)."""
import csv
import json
from pathlib import Path

COLUMNS = 'id name employer batch location organization_type source_url announcement_url application_url obtained_at last_verified_at published_at application_start application_end education degree major graduation_time experience political_status certificates age other_restrictions condition_text evidence_excerpt open_status raw_snapshot missing_fields evidence_metadata conditions recruitment_type salary is_fixture'.split()
JSON_COLUMNS = set('published_at application_start application_end education degree major graduation_time experience political_status certificates age other_restrictions missing_fields evidence_metadata conditions'.split())


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row.get(key, 'unknown'), ensure_ascii=False) if key in JSON_COLUMNS else str(row.get(key, 'unknown')).lower() if isinstance(row.get(key), bool) else row.get(key, 'unknown') for key in COLUMNS})


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError('CSV header differs from CO-001.records.csv')
        rows = []
        for row in reader:
            if None in row or any(value is None or value == '' for value in row.values()):
                raise ValueError('CSV contains missing/empty value')
            for key in JSON_COLUMNS:
                row[key] = json.loads(row[key])
            if row['is_fixture'] not in ('true', 'false'):
                raise ValueError('is_fixture must explicitly be true/false')
            row['is_fixture'] = row['is_fixture'] == 'true'
            rows.append(row)
        return rows
