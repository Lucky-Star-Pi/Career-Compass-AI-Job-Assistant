import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,rm} from 'node:fs/promises';
import {resolve,join,sep} from 'node:path';
import {randomBytes} from 'node:crypto';

test('账号持久化、并发注册、用户隔离、20条历史及会话防篡改',async()=>{
 const base=resolve('../data/private');await mkdir(base,{recursive:true});const root=await mkdtemp(join(base,'r4-store-'));assert.ok(root.startsWith(base+sep));process.env.USER_DATA_DIR=root;
 try{
  const store=await import('./user-store.ts');const session=await import('./session.ts');
  await store.initialize();assert.ok(await store.authenticate('demo','demo2026'));
  const password=randomBytes(20).toString('hex');const [a,b]=await Promise.all([store.register('testA',password),store.register('testB',password)]);assert.ok(a&&b);assert.notEqual(a.userId,b.userId);
  const duplicates=await Promise.all([store.register('duplicate',password),store.register('duplicate',password)]);assert.equal(duplicates.filter(Boolean).length,1);
  assert.equal(await store.authenticate('testA',randomBytes(20).toString('hex')),null);
  await store.updateData(a.userId,data=>{data.profile={confirmed:true,education:'本科'};});assert.equal((await store.getData(b.userId)).profile.confirmed,false);
  await Promise.all(Array.from({length:12},(_,i)=>store.appendTurn(a.userId,'合成问题'+i,{reply:'合成回答',references:[],model_status:'测试桩'})));
  assert.equal((await store.getData(a.userId)).messages.length,20);assert.equal((await store.getData(b.userId)).messages.length,0);
  const users=JSON.parse(await readFile(join(root,'users.json'),'utf8'));assert.ok(users.every((u:{hash:string;salt:string})=>/^[a-f0-9]{128}$/.test(u.hash)&&/^[a-f0-9]{32}$/.test(u.salt)));assert.ok(!JSON.stringify(users).includes(password));
  const token=session.signSession(a);assert.deepEqual(await session.userFromToken(token),a);assert.equal(session.verifySession((token[0]==='A'?'B':'A')+token.slice(1)),null);
  assert.equal(session.sameOrigin(new Request('http://localhost:3114/api/auth/login',{headers:{host:'127.0.0.1:3114',origin:'http://127.0.0.1:3114'}})),true);
  assert.equal(session.sameOrigin(new Request('http://localhost:3114/api/auth/login',{headers:{host:'127.0.0.1:3114',origin:'https://example.invalid'}})),false);
  assert.equal(store.validCredentials('../user',password),false);
  const resume='以下是合成简历要点，仅用于隔离测试。';await store.updateData(a.userId,data=>{data.resume=resume;});
  await store.updateData(a.userId,data=>{data.resume=null;});
  await store.appendTurn(a.userId,resume,{reply:'请确认求职条件',references:[],model_status:'测试桩'},{redactQuestion:true});
  const afterDelete=await store.getData(a.userId);assert.equal(afterDelete.resume,null);assert.ok(!JSON.stringify(afterDelete.messages).includes(resume));
 }finally{assert.ok(root.startsWith(base+sep));await rm(root,{recursive:true,force:true});}
});
