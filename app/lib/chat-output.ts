export type Reference = {job_id:string; source_url:string};
export type Completion = {content:unknown; finish_reason?:string};
export type CompletionRequest = (maxTokens:number, userPrefix:string) => Promise<Completion>;

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

export function validReply(value:unknown, candidates:Reference[]):value is {reply:string; references:Reference[]} {
  if(!value||typeof value!=='object')return false;
  const output=value as {reply?:unknown; references?:unknown};
  if(typeof output.reply!=='string'||!output.reply.trim()||output.reply.length>=300||/保证|一定|无需核实|包过|百分百|https?:\/\//i.test(output.reply))return false;
  if(!Array.isArray(output.references)||output.references.length<1||output.references.length>5)return false;
  return output.references.every(r=>r&&typeof r==='object'&&typeof r.job_id==='string'&&typeof r.source_url==='string'&&candidates.some(c=>c.job_id===r.job_id&&c.source_url===r.source_url));
}
