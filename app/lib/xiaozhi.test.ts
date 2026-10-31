import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {recommendation,ruleAnswer} from './recommendation.ts';
import {modelTiers,modeLabel} from './model-tiers.ts';
import {validReply} from './chat-output.ts';
import {explicitResumeSlots} from './slots.ts';
import {pdfInputError,PDF_LIMITS} from './pdf-client.ts';
import {match,type Job,type Profile} from './match.ts';
import {modelFacts} from './model-evidence.ts';
const jobs:Job[]=JSON.parse(readFileSync(new URL('./jobs.json',import.meta.url),'utf8'));
const profile:Profile={confirmed:true,education:'本科',major:'国际商务类',graduationYear:2027,certificates:['CET-4','C1驾驶证']};
const date='2026-10-31';
const ref={job_id:jobs[0].id,source_url:jobs[0].source_url};
const good={reply:'请逐项核对原公告未载明条件。',references:[ref]};
const completion=(output:unknown,reason='stop')=>Response.json({choices:[{finish_reason:reason,message:{content:typeof output==='string'?output:JSON.stringify(output)}}]});
test('B口径保留核心unknown且列明源缺失，不把已载明未匹配的条件放行',()=>{
 const policy=recommendation(profile,jobs[0],date);assert.equal(policy.ruleStatus,match(profile,jobs[0],date).status);assert.equal(policy.ruleStatus,'unknown');assert.equal(policy.canRecommend,true);assert.ok(policy.missingNames.includes('学位'));assert.match(policy.text,/已载明条件全部符合/);
 assert.equal(recommendation({...profile,certificates:[]},jobs[0],date).canRecommend,false);
 assert.equal(recommendation({...profile,confirmed:false},jobs[0],date).canRecommend,false);
 assert.equal(recommendation(profile,{...jobs[0],human_verification:{state:'pending'}},date).canRecommend,false);
 assert.equal(recommendation(profile,jobs[0],'2028-01-01').canRecommend,false);
 assert.match(recommendation({...profile,education:'大专'},jobs[0],date).text,/存在明确不符：学历/);
});
test('规则回答最多3条带成对来源且说明缺项',()=>{const output=ruleAnswer(profile,jobs,date);assert.equal(output.references.length,3);assert.ok(output.references.every(ref=>jobs.some(job=>job.id===ref.job_id&&job.source_url===ref.source_url)));assert.match(output.reply,/^小职正在升级中，先用规则结果帮你核对：/);assert.match(output.reply,/状态 unknown/);assert.match(output.reply,/未载明项/);});
test('DeepSeek失败和引用校验失败依次进入Qwen；15s/10s并各只尝试一次',async()=>{
 const calls:{url:string;signal:AbortSignal|null|undefined;body:Record<string,unknown>}[]=[];
 const fetcher:typeof fetch=async(url,options)=>{calls.push({url:String(url),signal:options?.signal,body:JSON.parse(options?.body as string)});return calls.length===1?completion({...good,references:[{...ref,source_url:'https://invalid.example/x'}]}):completion(good);};
 const output=await modelTiers({messages:[],deepseekKey:'synthetic',qwenKey:'synthetic',fetcher,accept:value=>validReply(value,[ref])});
 assert.equal(output?.mode,'qwen');assert.equal(calls.length,2);assert.match(calls[0].url,/api.deepseek.com/);assert.match(calls[1].url,/compatible-mode/);assert.equal(calls[1].body.model,'qwen-plus');assert.ok(calls.every(v=>v.signal));assert.equal(modeLabel(output?.mode),'由小职（Qwen 备份）生成');
});
test('截断/非法JSON跳过；未配Qwen/预算耗尽/双失败返回规则层标记',async()=>{
 let calls=0;const fetcher:typeof fetch=async()=>{calls++;return completion('{bad','length');};
 assert.equal(await modelTiers({messages:[],deepseekKey:'synthetic',fetcher,accept:()=>true}),null);assert.equal(calls,1);
 assert.equal(await modelTiers({messages:[],deepseekKey:'synthetic',qwenKey:'synthetic',fetcher,accept:()=>true}),null);assert.equal(calls,3);
 assert.equal(await modelTiers({messages:[],deepseekKey:'synthetic',fetcher,reserve:()=>false,accept:()=>true}),null);assert.equal(calls,3);
 assert.equal(await modelTiers({messages:[],fetcher,accept:()=>true}),null);assert.equal(modeLabel('rules'),'规则核对结果（小职升级中）');
});
test('本机PDF输入边界：仅pdf、最大5MB、5页/6000字上限',()=>{assert.equal(pdfInputError({name:'synthetic.pdf',size:PDF_LIMITS.bytes}),null);assert.match(pdfInputError({name:'synthetic.pdf',size:PDF_LIMITS.bytes+1})!,/5MB/);assert.match(pdfInputError({name:'synthetic.doc',size:1})!,/PDF/);assert.equal(PDF_LIMITS.pages,5);assert.equal(PDF_LIMITS.characters,6000);});
test('本地保守槽位只接收明确枚举且拒绝歧义',()=>{assert.deepEqual(explicitResumeSlots('本科 国际商务类 2027届 湛江 CET-4 C1驾驶证'),{education:'本科',major:'国际商务类',city:'湛江市',graduationYear:2027,certificates:['CET-4','C1驾驶证']});const conflict=explicitResumeSlots('本科经历 硕士在读 2027届 2028届');assert.equal(conflict.education,undefined);assert.equal(conflict.graduationYear,undefined);assert.deepEqual(explicitResumeSlots('合成材料，没有明确求职条件'),{});});
test('回复承诺与模型自带status仍拒绝',()=>{assert.equal(validReply({...good,reply:'保证'+'能报'},[ref]),false);assert.equal(validReply({...good,status:'eligible'},[ref]),false);});
test('模型事实包含01湛江/本科/专业原文/具体截止，03硕士/长期招聘',()=>{
 const first=modelFacts(jobs[0]);assert.equal(first.location,'湛江-霞山区');assert.equal(first.education,'本科');assert.match(first.major,/国际商务类/);assert.equal(first.batch,'unknown');assert.equal(first.open,'截止2027-01-25');
 const third=modelFacts(jobs[2]);assert.equal(third.education,'硕士');assert.equal(third.major,'unknown');assert.equal(third.batch,'27届');assert.equal(third.open,'长期招聘，无固定截止日期');
 assert.equal('status' in first,false);assert.equal('policy' in first,false);
});
test('模型事实缺失保持unknown、开放信息未载明，不伪造日期',()=>{assert.deepEqual(modelFacts({id:'test',name:'test',source_url:'https://example.invalid'}),{location:'unknown',education:'unknown',major:'unknown',batch:'unknown',open:'未载明'});assert.equal(modelFacts({...jobs[0],application_end:'unknown',open_basis:'unknown'}).open,'未载明');});
