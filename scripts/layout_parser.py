"""Pure visible-text layout A/B facts. No network, HTML fetch, or file writes."""
import copy
import re
from datetime import date

NATURES = ('央企', '国企', '事业单位', '民企')


def day_value(raw):
    match = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})|(\d{4})年(\d{1,2})月(\d{1,2})日', raw)
    if not match:
        return None
    try:
        return date(*map(int, match.groups()[:3] if match[1] else match.groups()[3:]))
    except ValueError:
        return None


def facts(text, evidence_path):
    original = text.splitlines()
    lines = [line.strip() for line in original]
    start = next((i for i, line in enumerate(lines) if line.rstrip('：:') == '报名截止'), None)
    result = {'field_evidence': {}, 'application_end': 'unknown', 'open_status': 'unknown', 'open_basis': 'unknown'}
    if start is None:
        return result
    def ref(index):
        return {'evidence_ref': original[index], 'raw': original[index], 'raw_snapshot': evidence_path, 'line': index + 1}
    # First actual employer line, not the value belonging to 所属集团.
    for i in range(max(0, start - 6), start):
        if not lines[i].startswith('#') and re.search('有限公司|集团|公司', lines[i]) and not (i > 0 and lines[i - 1].rstrip('：:') == '所属集团'):
            result['employer'] = lines[i]
            result['field_evidence']['employer'] = ref(i)
            break
    nature_lines = [(i, lines[i]) for i in range(max(0, start - 6), start) if lines[i] in NATURES]
    if len({value for _, value in nature_lines}) == 1:
        i, nature = nature_lines[0]
        result['organization_type'] = nature
        result['field_evidence']['organization_type'] = ref(i)
    if start + 1 < len(lines):
        raw = lines[start + 1]
        result['field_evidence']['application_end'] = ref(start + 1)
        day = day_value(raw)
        if day:
            result['application_end'] = {'raw': raw, 'normalized': day.isoformat(), 'precision': 'date'}
            result['open_status'] = 'open' if day >= date(2026, 10, 31) else 'closed' if day < date(2026, 10, 30) else 'unknown'
            result['open_basis'] = '具体截止日期'
            result['display_deadline'] = day.isoformat()
        elif re.fullmatch(r'长期招聘[，,]无固定截止日期', raw):
            result.update(open_status='open', open_basis='长期招聘', display_deadline='长期招聘，无固定截止日期')
        elif raw == '公告未写明':
            result['display_deadline'] = 'unknown'
    for field, label in (('education', '学历'), ('major', '专业')):
        single = next((i + 1 for i in range(start + 1, len(lines)) if lines[i].rstrip('：:') == label + '要求'), None)
        split = next((i + 2 for i in range(start + 1, len(lines) - 1) if lines[i] == label and lines[i + 1] == '要求'), None)
        value_index = single if single is not None else split
        if value_index is not None and value_index < len(lines):
            value = lines[value_index]
            if value not in ('', '学历要求', '专业要求', '岗位介绍'):
                result[field] = 'unknown' if value == '公告未写明' else value
                result['field_evidence'][field] = ref(value_index)
    return result


def apply_layout(row, text):
    output = copy.deepcopy(row)
    parsed = facts(text, row['证据文件'])
    for field, column in (('employer', '单位名称'), ('organization_type', '单位性质'), ('education', '学历'), ('major', '专业')):
        if field in parsed:
            output[column] = parsed[field]
    if 'application_end' in parsed['field_evidence']:
        end = parsed['application_end']
        if isinstance(end, dict):
            output['报名截止'] = end['normalized']
        elif parsed['open_basis'] == '长期招聘' or parsed.get('display_deadline') == 'unknown':
            output['报名截止'] = 'unknown'
        output['开放状态'] = parsed['open_status']
    if output.get('备注') == 'PENDING':
        output['备注'] = ''
    return output, parsed
