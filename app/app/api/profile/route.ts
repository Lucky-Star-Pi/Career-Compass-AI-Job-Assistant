import {read,sign,validProfile} from '../../../lib/profile';
export const runtime='nodejs';
export const dynamic='force-dynamic';
export async function GET(request:Request){return Response.json(read(request),{headers:{'Cache-Control':'no-store'}});}
export async function POST(request:Request){try{const text=await request.text();if(text.length>4096)return Response.json({error:'输入过长'},{status:400});const profile=JSON.parse(text);if(!validProfile(profile))return Response.json({error:'仅接受求职条件枚举，不接收身份或联系信息'},{status:400});const secure=new URL(request.url).protocol==='https:'?'; Secure':'';return Response.json({ok:true},{headers:{'Set-Cookie':`career_profile=${sign(profile)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=28800${secure}`,'Cache-Control':'no-store'}});}catch{return Response.json({error:'格式错误'},{status:400});}}
export async function DELETE(){return Response.json({ok:true},{headers:{'Set-Cookie':'career_profile=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0','Cache-Control':'no-store'}});}
