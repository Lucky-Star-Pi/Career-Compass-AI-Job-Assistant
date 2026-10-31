import {currentUser,sameOrigin} from '../../../lib/session';
import {getData,updateData} from '../../../lib/user-store';
export const runtime='nodejs';
export const dynamic='force-dynamic';
export async function GET(request:Request){try{const user=await currentUser(request);if(!user)return Response.json({error:'请先登录'},{status:401});const data=await getData(user.userId);return Response.json({preferences:{bubbleDismissed:data.preferences?.bubbleDismissed===true}},{headers:{'Cache-Control':'no-store'}});}catch{return Response.json({error:'偏好读取失败'},{status:503});}}
export async function POST(request:Request){
 if(!sameOrigin(request))return Response.json({error:'请求来源不匹配'},{status:403});
 try{const user=await currentUser(request);if(!user)return Response.json({error:'请先登录'},{status:401});const text=await request.text();if(text.length>256)return Response.json({error:'输入过长'},{status:400});let value;try{value=JSON.parse(text);}catch{return Response.json({error:'格式错误'},{status:400});}
 if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>k!=='bubbleDismissed')||typeof value.bubbleDismissed!=='boolean')return Response.json({error:'仅接受 bubbleDismissed 布尔偏好'},{status:400});
 const data=await updateData(user.userId,data=>{data.preferences={bubbleDismissed:value.bubbleDismissed};});return Response.json({preferences:data.preferences},{headers:{'Cache-Control':'no-store'}});
 }catch{return Response.json({error:'偏好保存失败，请重试'},{status:503});}
}
