import test from 'node:test';
import assert from 'node:assert/strict';
import {requestJSON,validReply,hasRecommendationClaim} from './chat-output.ts';
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
test('中性与需核对语境放行，仅拦实际承诺',()=>{
  assert.equal(validReply(output,references),true);
  for(const reply of ['校招时间不一定相同，需核对公告。','保证信息来源可追溯。','是否可以报需核对原公告。','不具备明确条件时不能确认可报名。','无需核实'])assert.equal(validReply({...output,reply},references),true);
  for(const reply of ['保证'+'能报','确保顺利报名','百分百录取','一定'+'能报','一定可以录用','无需核对','包过'])assert.equal(validReply({...output,reply},references),false);
});
test('拒绝reply内URL、空回复、过长回复和超过5条引用',()=>{
  for(const reply of ['https://example.invalid/a','HTTP://example.invalid/a','   ','字'.repeat(300)])assert.equal(validReply({...output,reply},references),false);
  assert.equal(validReply({...output,references:Array(6).fill(references[0])},references),false);
});
test('通用回答可空引用，有引用时必须属于候选且ID与URL成对',()=>{
  assert.equal(validReply({...output,references:[]},references),true);
  for(const refs of [undefined,null,{},[null],[{job_id:'OTHER',source_url:references[0].source_url}],[{job_id:references[0].job_id,source_url:references[1].source_url}]])assert.equal(validReply({...output,references:refs},references),false);
});
test('模型不得输出status，槽位建议不能替代规则判定',()=>{assert.equal(validReply({...output,status:'eligible'},references),false);assert.equal(validReply({...output,references:[{...references[0],status:'eligible'}]},references),false);});
test('否定推荐不是推荐承诺，混合回复中的正向推荐仍需规则核对',()=>{
  for(const reply of ['尚无法推荐岗位，请先确认条件。','暂不能直接推荐，需核对。','不宜为你推荐该岗。'])assert.equal(hasRecommendationClaim(reply),false);
  for(const reply of ['推荐该岗位。','不推荐甲，但推荐乙。','已载明条件全部符合。'])assert.equal(hasRecommendationClaim(reply),true);
});
