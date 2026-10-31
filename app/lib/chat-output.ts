export type Reference = {job_id:string; source_url:string};
export type Completion = {content:unknown; finish_reason?:string};
export type CompletionRequest = (maxTokens:number, userPrefix:string) => Promise<Completion>;

// A refusal is not a recommendation. Retain any positive claim elsewhere in
// the same reply, so "not A, but recommend B" still requires rule verification.
export function hasRecommendationClaim(reply:string){
  const positive=reply.replace(/(?:无法|不能|不宜|不应|不可|暂不|不)(?:(?:直接|明确|据此|为你|向你|给你|进行|给出|做出|提供|具体|任何|岗位|相关|有效|作出))*推荐/g,'');
  return /推荐|已载明条件全部符合/.test(positive);
}

// Only malformed/truncated JSON gets one retry; HTTP/network failures propagate.
export async function requestJSON(request:CompletionRequest):Promise<unknown> {
  for(let attempt=0;attempt<2;attempt++){
    const completion=await request(attempt===0?2000:2400,attempt===0?'':'只输出 JSON，不要在字符串外写任何字符\n');
    try{
      if(completion.finish_reason==='length')throw new SyntaxError('Truncated model JSON');
      if(typeof completion.content!=='string')throw new SyntaxError('Missing model JSON');
      return JSON.parse(completion.content);
    }catch(error){
      if(attempt===1)throw error;
    }
  }
  throw new SyntaxError('Missing model JSON');
}

export function validReply(value:unknown, candidates:Reference[]):value is {reply:string; references:Reference[];profile_updates?:unknown} {
  if(!value||typeof value!=='object'||'status' in value)return false;
  const output=value as {reply?:unknown; references?:unknown};
  if(typeof output.reply!=='string'||!output.reply.trim()||output.reply.length>=300||/(保证|确保|百分百)[^。！？]{0,8}(能报|报名|录用|录取)|一定(能|可以)(报|录用)|无需核对|包过|https?:\/\//i.test(output.reply))return false;
  if(!Array.isArray(output.references)||output.references.length>5)return false;
  return output.references.every(r=>r&&typeof r==='object'&&!('status' in r)&&typeof r.job_id==='string'&&typeof r.source_url==='string'&&candidates.some(c=>c.job_id===r.job_id&&c.source_url===r.source_url));
}
