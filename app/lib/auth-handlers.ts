import {register,authenticate,validCredentials} from './user-store.ts';
import {sameOrigin,signSession,sessionCookie} from './session.ts';
const attempts=new Map<string,{until:number;count:number}>();
export async function accountRequest(request:Request,mode:'register'|'login'){
 if(!sameOrigin(request))return Response.json({error:'请求来源不匹配'},{status:403});
 const key=request.headers.get('x-forwarded-for')?.split(',')[0]||'local';const now=Date.now();for(const [k,v] of attempts)if(v.until<now)attempts.delete(k);const entry=attempts.get(key)||{until:now+60_000,count:0};attempts.set(key,entry);if(++entry.count>30)return Response.json({error:'请求过于频繁，请稍后重试'},{status:429});
 try{const text=await request.text();if(text.length>2048)return Response.json({error:'输入过长'},{status:400});const {username,password}=JSON.parse(text);if(!validCredentials(username,password))return Response.json({error:'用户名需3–20位字母数字，密码需6–128位'},{status:400});const user=mode==='register'?await register(username,password):await authenticate(username,password);if(!user)return Response.json({error:mode==='register'?'用户名已存在':'用户名或密码不正确'},{status:mode==='register'?409:401});return Response.json({user},{headers:{'Set-Cookie':sessionCookie(request,signSession(user)),'Cache-Control':'no-store'}});}catch{return Response.json({error:'账号服务暂不可用，请稍后重试'},{status:503});}
}
