import {sameOrigin,sessionCookie} from '../../../../lib/session';
export function POST(request:Request){if(!sameOrigin(request))return Response.json({error:'请求来源不匹配'},{status:403});return Response.json({ok:true},{headers:{'Set-Cookie':sessionCookie(request,'',true),'Cache-Control':'no-store'}});}
