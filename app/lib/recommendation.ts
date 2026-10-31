import {match,raw,type Job,type Profile} from './match.ts';
export const FIELD_NAMES:Record<string,string>={education:'学历',major:'专业',batch:'届别',certificates:'证书',degree:'学位',graduation_time:'毕业时间',experience:'工作经验',political_status:'政治面貌',age:'年龄',other_restrictions:'其他限制',open_status:'报名开放状态'};
export function recommendation(profile:Profile,job:Job,asOf:string){
 const result=match(profile,job,asOf);const fields=Object.keys(FIELD_NAMES);
 const known=(field:string)=>field==='open_status'?job.open_status==='open'&&(job.open_basis==='长期招聘'||raw(job.application_end)!=='unknown'):raw(job[field])!=='unknown';
 const missing=fields.filter(field=>!known(field));
 const failed=[...new Set(result.checks.filter(c=>fields.includes(c.field)&&c.result==='fail').map(c=>c.field))];
 const unresolved=[...new Set(result.checks.filter(c=>fields.includes(c.field)&&known(c.field)&&c.result==='unknown').map(c=>c.field))];
 const passed=result.checks.filter(c=>fields.includes(c.field)&&c.result==='pass').length;
 const review=job.human_verification as {state?:string}|undefined;
 const canRecommend=profile.confirmed&&job.open_status==='open'&&review?.state==='verified'&&!failed.length&&!unresolved.length&&passed>0;
 const names=(keys:string[])=>keys.map(k=>FIELD_NAMES[k]||k);
 const text=failed.length?'存在明确不符：'+names(failed).join('、'):canRecommend?`已载明条件全部符合（${passed} 项）；另有 ${missing.length} 项公告未载明，需自行核对原公告`:'关键条件未载明，无法判断';
 return {ruleStatus:result.status,canRecommend,text,passed,missingFields:missing,missingNames:names(missing),failedNames:names(failed),unresolvedNames:names(unresolved),checks:result.checks};
}
export function ruleAnswer(profile:Profile,jobs:Job[],asOf:string){
 const items=jobs.map(job=>({job,policy:recommendation(profile,job,asOf)}));
 items.sort((a,b)=>Number(b.policy.canRecommend)-Number(a.policy.canRecommend));
 const selected=items.slice(0,3);
 return {reply:'小职正在升级中，先用规则结果帮你核对：\n'+selected.map(({job,policy})=>`${job.name}：状态 ${policy.ruleStatus}。${policy.text}。未载明项：${policy.missingNames.join('、')||'无'}${policy.unresolvedNames.length?'；需补充或核实：'+policy.unresolvedNames.join('、'):''}。`).join('\n'),references:selected.map(({job})=>({job_id:job.id,source_url:job.source_url}))};
}
