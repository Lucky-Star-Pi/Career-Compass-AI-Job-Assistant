import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {match,type Profile,type Job} from '../app/lib/match.ts';
import jobs from '../app/lib/jobs.json' with {type:'json'};
import cases from './cases.json' with {type:'json'};

type Case={id:string;job_id:string;profile:Profile;as_of:string;expect:'eligible'|'ineligible'|'unknown';note:string};
const inputs=cases as Case[];
if(inputs.length!==8||new Set(inputs.map(c=>c.id)).size!==8)throw new Error('Expected exactly eight distinct cases');
const rows=inputs.map(c=>{
 const job=jobs.find(j=>j.id===c.job_id);if(!job)throw new Error('Missing real job for '+c.id);
 const result=match(c.profile,job as Job,c.as_of);
 const reason=result.checks.find(check=>check.result==='fail')||result.checks.find(check=>check.result==='unknown');
 return {input:c,job,result,agrees:c.expect===result.status,reason:reason?reason.field+'：'+reason.explanation:'所有已验证检查通过'};
});
const consistent=rows.filter(r=>r.agrees).length;
const decided=rows.filter(r=>r.input.expect!=='unknown');
const decidedCorrect=decided.filter(r=>r.agrees).length;
const unknown=rows.filter(r=>r.result.status==='unknown').length;
const percent=(n:number,d:number)=>d?(100*n/d).toFixed(1)+'%':'不适用（分母为0）';
const safe=(s:string)=>s.replace(/\|/g,'\\|').replace(/\r?\n/g,' ');
const hash=(path:string)=>createHash('sha256').update(readFileSync(new URL(path,import.meta.url))).digest('hex');
const content=[
 '# 离线规则评测结果',
 '',
 '命令：`node --experimental-strip-types eval/run_eval.ts`。仅导入规则函数与本地真实岗位JSON，不调用模型或联网。',
 '',
 '按参赛者指定表运行8例，覆盖'+new Set(inputs.map(c=>c.job_id)).size+'个不同的真实岗位（01、02、03、08），不是8个不同岗位。画像均为构造条件，不含真实个人信息。E1确认已有学历，专业省略表示未提供；只有E6为confirmed:false。',
 '',
 '| id | job | expect | actual | 是否一致 | 首个unknown字段或fail原因 |',
 '|---|---|---|---|---|---|',
 ...rows.map(r=>`| ${r.input.id} | ${safe(r.job.id+' · '+r.job.name)} | ${r.input.expect} | ${r.result.status} | ${r.agrees?'一致':'不一致'} | ${safe(r.reason)} |`),
 '',
 `- 判定一致率：${consistent}/8 = ${percent(consistent,8)}。`,
 `- expect为eligible或ineligible的已判定项一致率：${decidedCorrect}/${decided.length} = ${percent(decidedCorrect,decided.length)}（本表3例均为预期ineligible，无预期eligible）。`,
 `- actual为unknown的占比：${unknown}/8 = ${percent(unknown,8)}。`,
 '',
 rows.some(r=>!r.agrees)?'不一致说明：'+rows.filter(r=>!r.agrees).map(r=>r.input.id+'：'+r.reason+'；'+r.input.note).join('；'):'本次没有不一致项；expect按指定表保留，未为迎合结果而更改。',
 '',
 '**本评测只覆盖规则层，不含模型生成质量。** 8例未覆盖所有岗位、条件或边界，也没有证明任何真实用户确定具备报名资格；不将一致率当作模型正确率或全面准确率。',
 '',
 '复核输入：[cases.json](cases.json)、[runner](run_eval.ts)、[规则](../app/lib/match.ts)、[真实岗位](../app/lib/jobs.json)。原文溯源见[数据报告](../data/REPORT.md)。',
 '',
 '| 输入 | SHA256 |',
 '|---|---|',
 `| cases.json | ${hash('./cases.json')} |`,
 `| app/lib/match.ts | ${hash('../app/lib/match.ts')} |`,
 `| app/lib/jobs.json | ${hash('../app/lib/jobs.json')} |`,
 '',
].join('\n');
writeFileSync(new URL('./RESULT.md',import.meta.url),content,'utf8');
for(const row of rows)console.log(`${row.input.id}: expect=${row.input.expect}; actual=${row.result.status}; ${row.agrees?'一致':'不一致'}; ${row.reason}`);
console.log(`判定一致率=${consistent}/8 (${percent(consistent,8)}); 已判定项=${decidedCorrect}/${decided.length} (${percent(decidedCorrect,decided.length)}); unknown=${unknown}/8 (${percent(unknown,8)})`);
console.log('本评测只覆盖规则层，不含模型生成质量。');
process.exitCode=consistent===8?0:1;
