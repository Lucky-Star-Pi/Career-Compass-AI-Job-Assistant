export type Profile = {confirmed:boolean; education?:string; major?:string; graduationYear?:number; city?:string; certificates?:string[]};
export type Check = {field:string; result:'pass'|'fail'|'unknown'; explanation:string; evidence:string; source_url:string};
export type Job = {id:string; name:string; source_url:string; [key:string]:unknown};
export function raw(value:unknown):string {
  if(typeof value==='string') return value;
  if(value && typeof value==='object' && 'raw' in value) return String(value.raw);
  return 'unknown';
}
export function match(profile:Profile, job:Job, asOf?:string) {
  const checks:Check[]=[];
  const add=(field:string,result:Check['result'],explanation:string)=>{
    const refs=job.field_evidence as Record<string,{evidence_ref?:string}>|undefined;
    const candidate=raw(job[field]);
    const evidence=refs?.[field]?.evidence_ref||(field==='open_status'?(refs?.application_end?.evidence_ref||(job.open_basis==='长期招聘'?'长期招聘':'')):(candidate!=='unknown'&&typeof job.condition_text==='string'&&job.condition_text.includes(candidate)?candidate:''));
    checks.push({field,result,explanation,evidence,source_url:job.source_url});
  };
  const finish=(status:'eligible'|'ineligible'|'unknown')=>({job_id:job.id,status,checks,missing_fields:checks.filter(x=>x.result==='unknown').map(x=>x.field),evidence_references:checks.filter(x=>x.evidence).map(x=>({field:x.field,quote:x.evidence,source_url:x.source_url})),source_url:job.source_url});
  if(!profile.confirmed){add('profile_confirmation','unknown','请先确认求职条件');return finish('unknown');}
  if(job.open_status==='closed'||job.open_status==='not_started') add('open_status','fail','来源显示已截止或尚未开放');
  else if(job.open_status!=='open') add('open_status','unknown','来源开放状态无法确认');
  else {
    const end=job.application_end as {normalized?:string}|undefined;
    if(end && typeof end==='object' && end.normalized && asOf && end.normalized < asOf) add('open_status','fail','具体截止日期已经过去');
    else if(end && typeof end==='object' && end.normalized && !asOf) add('open_status','unknown','缺少判定日期');
    else add('open_status','pass',job.open_basis==='长期招聘'?'页面明确长期招聘，无固定截止日期':'来源有开放声明，仍需以招聘方实时状态为准');
  }
  const edu=raw(job.education); const levels=['大专','本科','硕士','博士'];
  if(!profile.education||edu==='unknown')add('education','unknown','学历条件或画像缺失');
  else if(edu.includes(profile.education))add('education','pass','学历名称在来源要求中');
  else {
    const required=levels.find(x=>edu.includes(x));
    if(required&&levels.indexOf(profile.education)<levels.indexOf(required))add('education','fail','学历低于明确要求');
    else if(required&&edu.includes('以上')&&levels.indexOf(profile.education)>=levels.indexOf(required))add('education','pass','满足明确的最低学历');
    else add('education','unknown','来源未明确较高学历是否适用，不能自行扩大范围');
  }
  const major=raw(job.major);
  if(!profile.major||profile.major==='其他/待核实'||major==='unknown')add('major','unknown','专业条件缺失或需要目录口径核实');
  else if(major.split(/[、，,;；\s]+/).includes(profile.major))add('major','pass','专业名称与明确清单一致');
  else if(/相关|等|详见/.test(major))add('major','unknown','专业范围存在解释空间');
  else add('major','fail','所确认专业未出现在明确列出的专业清单中');
  const batch=raw(job.batch);const year=/((?:20)?\d{2})届/.exec(batch);
  if(!profile.graduationYear||!year)add('batch','unknown','届别信息缺失');
  else add('batch',Number(year[1].length===2?'20'+year[1]:year[1])===profile.graduationYear?'pass':'fail','比较已确认毕业届别和来源届别');
  const certificates=raw(job.certificates);
  if(certificates==='unknown')add('certificates','unknown','证书条件未写明，需核实');
  else if(certificates!=='不限'){
    const needed=[...(certificates.includes('CET-4')?['CET-4']:[]),...(/C1.*驾驶证/.test(certificates)?['C1驾驶证']:[])];
    if(!needed.length)add('certificates','unknown','证书条款尚未结构化');
    else for(const cert of needed)add('certificates',profile.certificates?.includes(cert)?'pass':'unknown','证书要求：'+cert+'；未提供不推断为不具备');
  }
  for(const field of ['degree','graduation_time','experience','political_status','age','other_restrictions']){
    if(raw(job[field])==='不限')add(field,'pass','来源明确写明不限');
    else add(field,'unknown','该限制缺失或尚需结合完整原文核实，未自动判通过');
  }
  const review=job.human_verification as {state?:string}|undefined;
  if(review?.state!=='verified')add('source_review','unknown','来源及完整附加限制尚未独立核验');
  if(profile.city)add('location','pass','工作地区仅作为偏好，不作为报名资格硬限制');
  if(checks.some(x=>x.result==='fail'))return finish('ineligible');
  if(checks.some(x=>x.result==='unknown'))return finish('unknown');
  return finish('eligible');
}
