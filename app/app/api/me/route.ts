import {currentUser} from '../../../lib/session';
export const runtime='nodejs';
export const dynamic='force-dynamic';
export async function GET(request:Request){try{const user=await currentUser(request);return Response.json(user?{user}:{error:'请先登录'},{status:user?200:401,headers:{'Cache-Control':'no-store'}});}catch{return Response.json({error:'账号服务暂不可用'},{status:503});}}
