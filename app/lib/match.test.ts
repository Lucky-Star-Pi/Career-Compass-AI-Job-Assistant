import test from 'node:test';
import assert from 'node:assert/strict';
import {match,summarize} from './match.ts';
const job={id:'TEST',name:'合成测试',source_url:'https://example.invalid',degree:'不限',graduation_time:'不限',experience:'不限',political_status:'不限',age:'不限',other_restrictions:'不限',certificates:'不限',education:'本科',major:'计算机类',batch:'27届',open_status:'open',open_basis:'长期招聘',application_end:'unknown',human_verification:{state:'verified'}};
test('未确认画像始终unknown',()=>assert.equal(match({confirmed:false,education:'大专'},job).status,'unknown'));
test('明确学历不符优先ineligible',()=>assert.equal(match({confirmed:true,education:'大专'},job).status,'ineligible'));
test('关键专业缺失不能eligible',()=>assert.equal(match({confirmed:true,education:'本科',graduationYear:2027},job).status,'unknown'));
test('全部显式条件通过的合成岗位eligible',()=>assert.equal(match({confirmed:true,education:'本科',major:'计算机类',graduationYear:2027},job).status,'eligible'));
test('来源未核验不能eligible',()=>assert.equal(match({confirmed:true,education:'本科',major:'计算机类',graduationYear:2027},{...job,human_verification:{state:'pending'}}).status,'unknown'));
test('其他条件未支持保持unknown',()=>assert.equal(match({confirmed:true,education:'本科',major:'计算机类',graduationYear:2027},{...job,age:'年龄限制原文'}).status,'unknown'));

test('明确截止日按传入日期检查',()=>assert.equal(match({confirmed:true},{...job,application_end:{normalized:'2026-10-29'}},'2026-10-30').status,'ineligible'));
test('未知附加硬条件不放行',()=>assert.equal(match({confirmed:true,education:'本科',major:'计算机类',graduationYear:2027},{...job,age:'unknown'}).status,'unknown'));

test('缺失证据不会伪造引用',()=>assert.ok(match({confirmed:false},job).evidence_references.every(x=>x.quote!=='unknown')));

test('summarize 排除 meta 项',()=>{const s=summarize([{field:'education',result:'pass',explanation:'',evidence:'',source_url:''},{field:'major',result:'pass',explanation:'',evidence:'',source_url:''},{field:'batch',result:'unknown',explanation:'',evidence:'',source_url:''},{field:'source_review',result:'unknown',explanation:'',evidence:'',source_url:''}]);assert.deepEqual(s,{pass:2,unknown:1,fail:0});});
