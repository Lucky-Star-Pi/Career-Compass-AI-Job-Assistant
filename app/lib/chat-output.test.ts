import test from 'node:test';
import assert from 'node:assert/strict';
import {requestJSON,validReply} from './chat-output.ts';
const references=[{job_id:'TEST-A',source_url:'https://example.invalid/a'},{job_id:'TEST-B',source_url:'https://example.invalid/b'}];
const output={reply:'符合学历条件；个人资格待核实，暂不能确认可报名。',references:[references[0]]};

test('正常JSON首轮2000 tokens，不重试',async()=>{
  let calls=0;
  assert.deepEqual(await requestJSON(async(tokens,prefix)=>{calls++;assert.equal(tokens,2000);assert.equal(prefix,'');return {content:JSON.stringify(output),finish_reason:'stop'};}),output);
  assert.equal(calls,1);
});
test('JSON截断重试一次，2400 tokens并追加严格JSON前缀',async()=>{
  const calls:{tokens:number;prefix:string}[]=[];
  const result=await requestJSON(async(tokens,prefix)=>{calls.push({tokens,prefix});return {content:calls.length===1?'{"references":[':JSON.stringify(output),finish_reason:'stop'};});
  assert.deepEqual(result,output);
  assert.deepEqual(calls,[{tokens:2000,prefix:''},{tokens:2400,prefix:'只输出 JSON，不要在字符串外写任何字符\n'}]);
});
test('finish_reason=length即使JSON可解析也重试',async()=>{
  let calls=0;
  assert.deepEqual(await requestJSON(async()=>({content:JSON.stringify(output),finish_reason:++calls===1?'length':'stop'})),output);
  assert.equal(calls,2);
});
test('连续两次JSON失败或length后结束，不进行第三次调用',async()=>{
  for(const completion of [{content:'{',finish_reason:'stop'},{content:JSON.stringify(output),finish_reason:'length'}]){
    let calls=0;
    await assert.rejects(requestJSON(async()=>{calls++;return completion;}),SyntaxError);
    assert.equal(calls,2);
  }
});
test('HTTP或网络错误不在JSON重试范围',async()=>{
  let calls=0;
  await assert.rejects(requestJSON(async()=>{calls++;throw new Error('HTTP failure');}));
  assert.equal(calls,1);
});
test('允许符合、不符合、待核实和可报名，仍拒绝承诺禁词',()=>{
  assert.equal(validReply(output,references),true);
  for(const phrase of ['保证','一定','无需核实','包过','百分百'])assert.equal(validReply({...output,reply:phrase},references),false);
});
test('拒绝reply内URL、空回复、过长回复和超过5条引用',()=>{
  for(const reply of ['https://example.invalid/a','HTTP://example.invalid/a','   ','字'.repeat(300)])assert.equal(validReply({...output,reply},references),false);
  assert.equal(validReply({...output,references:Array(6).fill(references[0])},references),false);
});
test('引用必须非空、属于候选集且ID和URL成对匹配',()=>{
  for(const refs of [[],[null],[{job_id:'OTHER',source_url:references[0].source_url}],[{job_id:references[0].job_id,source_url:references[1].source_url}]])assert.equal(validReply({...output,references:refs},references),false);
});
