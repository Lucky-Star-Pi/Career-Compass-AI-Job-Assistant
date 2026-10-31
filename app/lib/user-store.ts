import {scrypt as scryptCallback,randomBytes,randomUUID,timingSafeEqual} from 'node:crypto';
import {promisify} from 'node:util';
import {mkdir,readFile,writeFile,rename,unlink} from 'node:fs/promises';
import {resolve,join,sep} from 'node:path';
import type {Profile} from './match.ts';
import type {Reference} from './chat-output.ts';

const scrypt=promisify(scryptCallback);
export type PublicUser={userId:string;username:string};
type User=PublicUser & {salt:string;hash:string;createdAt:string};
export type Message={id:string;role:'user'|'assistant';content:string;createdAt:string;references?:Reference[];model_status?:string;profile_updates?:Partial<Profile>;resume_received?:boolean};
export type UserData={profile:Profile;resume:string|null;messages:Message[];updatedAt:string};
const root=resolve(process.env.USER_DATA_DIR||'/opt/career-data');
const appRoot=resolve(process.cwd());
if(root===appRoot||root.startsWith(appRoot+sep))throw new Error('USER_DATA_DIR must be outside the application directory');
const globals=globalThis as typeof globalThis & {__ccStores?:Map<string,{queue:Promise<unknown>;ready:boolean}>};
const stores=globals.__ccStores??=new Map();
if(!stores.has(root))stores.set(root,{queue:Promise.resolve(),ready:false});
const state=stores.get(root)!;
function locked<T>(action:()=>Promise<T>):Promise<T>{const result=state.queue.then(action);state.queue=result.catch(()=>{});return result;}
async function atomic(path:string,value:unknown){
 const temp=path+'.'+randomUUID()+'.tmp';
 try{await writeFile(temp,JSON.stringify(value,null,2)+'\n',{encoding:'utf8',mode:0o600,flag:'wx'});await rename(temp,path);}
 finally{await unlink(temp).catch((e:NodeJS.ErrnoException)=>{if(e.code!=='ENOENT')throw e;});}
}
async function json<T>(path:string):Promise<T>{return JSON.parse(await readFile(path,'utf8'));}
const publicUser=(user:User):PublicUser=>({userId:user.userId,username:user.username});
export function validCredentials(username:unknown,password:unknown):username is string{return typeof username==='string'&&/^[A-Za-z0-9]{3,20}$/.test(username)&&typeof password==='string'&&password.length>=6&&password.length<=128;}
async function makeUser(username:string,password:string):Promise<User>{const salt=randomBytes(16).toString('hex');const hash=(await scrypt(password,salt,64) as Buffer).toString('hex');return {userId:randomUUID(),username,salt,hash,createdAt:new Date().toISOString()};}
async function init(){
 if(state.ready)return;
 await mkdir(join(root,'profiles'),{recursive:true,mode:0o700});
 let users:User[];
 try{users=await json<User[]>(join(root,'users.json'));if(!Array.isArray(users))throw new Error('Invalid user storage');}
 catch(e){if((e as NodeJS.ErrnoException).code!=='ENOENT')throw e;users=[];}
 if(!users.some(u=>u.username.toLowerCase()==='demo')){users.push(await makeUser('demo','demo2026'));await atomic(join(root,'users.json'),users);}
 state.ready=true;
}
export function initialize(){return locked(init);}
export async function register(username:string,password:string){return locked(async()=>{await init();const users=await json<User[]>(join(root,'users.json'));if(users.some(u=>u.username.toLowerCase()===username.toLowerCase()))return null;const user=await makeUser(username,password);users.push(user);await atomic(join(root,'users.json'),users);return publicUser(user);});}
export async function authenticate(username:string,password:string){await initialize();const users=await json<User[]>(join(root,'users.json'));const user=users.find(u=>u.username.toLowerCase()===username.toLowerCase());const salt=user?.salt||'unregistered-user';const actual=await scrypt(password,salt,64) as Buffer;const expected=Buffer.from(user?.hash||'00'.repeat(64),'hex');return user&&actual.length===expected.length&&timingSafeEqual(actual,expected)?publicUser(user):null;}
export async function findUser(userId:string){await initialize();const users=await json<User[]>(join(root,'users.json'));const user=users.find(u=>u.userId===userId);return user?publicUser(user):null;}
function profilePath(userId:string){if(!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(userId))throw new Error('Invalid user identity');return join(root,'profiles',userId+'.json');}
async function load(userId:string):Promise<UserData>{try{return await json<UserData>(profilePath(userId));}catch(e){if((e as NodeJS.ErrnoException).code!=='ENOENT')throw e;return {profile:{confirmed:false,certificates:[]},resume:null,messages:[],updatedAt:new Date().toISOString()};}}
export async function getData(userId:string){await initialize();return load(userId);}
export async function updateData(userId:string,change:(data:UserData)=>void){return locked(async()=>{await init();const data=await load(userId);change(data);data.messages=data.messages.slice(-20);data.updatedAt=new Date().toISOString();await atomic(profilePath(userId),data);return data;});}
export function appendTurn(userId:string,question:string,answer:{reply:string;references:Reference[];model_status:string;profile_updates?:Partial<Profile>;resume_received?:boolean},options?:{resume?:string;redactQuestion?:boolean}){return updateData(userId,data=>{const now=new Date().toISOString();if(options?.resume!==undefined)data.resume=options.resume;data.messages.push({id:randomUUID(),role:'user',content:options?.resume!==undefined||options?.redactQuestion?'已提交简历要点（原文仅保存在账号私有简历中）':question,createdAt:now},{id:randomUUID(),role:'assistant',content:answer.reply,createdAt:now,references:answer.references,model_status:answer.model_status,profile_updates:answer.profile_updates,resume_received:answer.resume_received});});}
