import test from 'node:test';
import assert from 'node:assert/strict';
import {filterProfileUpdates} from './slots.ts';
import {isResumeContent,forModel,containsResumeEcho} from './resume.ts';
test('五个枚举槽位校验通过，不接纳confirmed或status',()=>assert.deepEqual(filterProfileUpdates({education:'本科',major:'国际商务类',city:'湛江市',graduationYear:2027,certificates:['CET-4'],confirmed:true,status:'eligible'}),{profile_updates:{education:'本科',major:'国际商务类',city:'湛江市',graduationYear:2027,certificates:['CET-4']},dropped_fields:['confirmed','status']}));
test('无效槽位丢弃，不用未知值覆盖画像',()=>assert.deepEqual(filterProfileUpdates({education:'任意学历',major:'虚构专业',city:'错误地区',graduationYear:'2027',certificates:['虚构证书','CET-4']}),{profile_updates:{certificates:['CET-4']},dropped_fields:['education','major','city','graduationYear','certificates']}));
test('空/错误槽位形状安全拒绝',()=>{assert.deepEqual(filterProfileUpdates(undefined),{profile_updates:{},dropped_fields:[]});assert.deepEqual(filterProfileUpdates([]).dropped_fields,['profile_updates']);});
test('简历检测、个人信息行过滤和原文回显检查',()=>{assert.equal(isResumeContent('简历要点'),true);assert.equal(isResumeContent('合成经历'.repeat(60)),true);assert.equal(isResumeContent('那我还差什么'),false);assert.equal(forModel('姓名：合成测试\n学历：本科'),'[个人信息已省略]\n学历：本科');const source='合成项目经历中通过完整的需求讨论形成可复核的交付文档。';assert.equal(containsResumeEcho(source,source),true);assert.equal(containsResumeEcho('请核对确认条中的求职条件。',source),false);});
