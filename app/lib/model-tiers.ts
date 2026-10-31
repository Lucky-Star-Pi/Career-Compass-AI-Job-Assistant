export type Mode='deepseek'|'qwen'|'rules';
export const modeLabel=(mode?:Mode)=>mode==='deepseek'?'由小职（DeepSeek）生成':mode==='qwen'?'由小职（Qwen 备份）生成':'规则核对结果（小职升级中）';
type TierOptions={messages:{role:string;content:string}[];deepseekKey?:string;qwenKey?:string;accept:(value:unknown)=>boolean;fetcher?:typeof fetch;reserve?:()=>boolean};
export async function modelTiers(options:TierOptions):Promise<{mode:'deepseek'|'qwen';output:unknown}|null>{
 const fetcher=options.fetcher||fetch;
 const tiers=[{mode:'deepseek' as const,key:options.deepseekKey,url:'https://api.deepseek.com/chat/completions',model:'deepseek-flash',timeout:15000},{mode:'qwen' as const,key:options.qwenKey,url:'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',model:'qwen-plus',timeout:10000}];
 for(const tier of tiers){
  if(!tier.key)continue;if(options.reserve&&!options.reserve())return null;
  try{
   const response=await fetcher(tier.url,{method:'POST',headers:{Authorization:`Bearer ${tier.key}`,'Content-Type':'application/json'},body:JSON.stringify({model:tier.model,...(tier.mode==='deepseek'?{thinking:{type:'disabled'}}:{}),temperature:0,max_tokens:2400,response_format:{type:'json_object'},messages:options.messages}),signal:AbortSignal.timeout(tier.timeout)});
   if(!response.ok)continue;const body=await response.json();const choice=body.choices?.[0] as {finish_reason?:string;message?:{content?:string}}|undefined;
   if(!choice?.message?.content||choice.finish_reason==='length')continue;
   const output=JSON.parse(choice.message.content);if(options.accept(output))return {mode:tier.mode,output};
  }catch{/* Provider errors contain no user-visible diagnostics or secret logs. */}
 }
 return null;
}
