export const dynamic='force-dynamic';
export function GET(){return Response.json({status:'ok',model:process.env.DEEPSEEK_API_KEY?'已配置，未实测':'未接通',data_count:10,storage:'只读JSON；画像仅签名Cookie',persistent_cookie_secret:!!process.env.PROFILE_COOKIE_SECRET});}
